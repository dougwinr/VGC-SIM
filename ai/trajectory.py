"""Trajectory reconstruction from BattleLog for offline RL.

This module provides tools for:
- Converting BattleLogs to RL transitions
- Reconstructing full trajectories from replay data
- Building offline RL datasets from recorded battles
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
import numpy as np

from core.battle_state import BattleState
from core.battle import BattleEngine, Choice
from core.battle_log import BattleLog
from core.events import EventType
from agents.base import Action, ActionKind
from .replay_buffer import Transition, Episode


@dataclass
class TrajectoryConfig:
    """Configuration for trajectory extraction.

    Attributes:
        include_opponent_obs: Include opponent's perspective
        reward_mode: How to compute rewards ("terminal", "hp_delta", "per_event")
        win_reward: Reward for winning
        lose_reward: Reward for losing
        faint_reward: Reward per opponent faint
        damage_scale: Scale factor for damage-based rewards
        annotate_agent_type: Include agent type in transition info
        include_reasoning: Include LLM reasoning if available
    """
    include_opponent_obs: bool = False
    reward_mode: str = "terminal"
    win_reward: float = 1.0
    lose_reward: float = -1.0
    faint_reward: float = 0.0
    damage_scale: float = 0.0
    annotate_agent_type: bool = True
    include_reasoning: bool = True


def choice_to_action(choice: Choice, side: int) -> Action:
    """Convert a Choice object to an Action.

    Args:
        choice: Engine Choice object
        side: Side that made the choice

    Returns:
        Agent Action object
    """
    if choice.choice_type == 'move':
        # Parse target
        target_side, target_slot = -1, -1
        if choice.target > 0:
            target_side = 1 - side
            target_slot = choice.target - 1
        elif choice.target < 0:
            target_side = side
            target_slot = abs(choice.target) - 1

        return Action.move(
            slot=choice.slot,
            move_slot=choice.move_slot,
            target_side=target_side,
            target_slot=target_slot,
        )

    elif choice.choice_type == 'switch':
        return Action.switch(
            slot=choice.slot,
            switch_to=choice.switch_to,
        )

    else:  # 'pass'
        return Action.pass_action(slot=choice.slot)


class TrajectoryExtractor:
    """Extracts RL trajectories from BattleLogs.

    Supports:
    - Reconstructing state at each turn via replay
    - Computing rewards from events
    - Building transition tuples for offline RL
    """

    def __init__(
        self,
        config: Optional[TrajectoryConfig] = None,
        move_registry: Optional[Dict[int, Any]] = None,
        observation_func: Optional[Callable[[BattleState, int], Any]] = None,
    ):
        """Initialize extractor.

        Args:
            config: Extraction configuration
            move_registry: Move data for replay
            observation_func: Custom observation extraction function
        """
        self.config = config or TrajectoryConfig()
        self._move_registry = move_registry or {}
        self._get_obs = observation_func or (lambda s, side: s.get_observation(side))

    def extract_from_log(
        self,
        battle_log: BattleLog,
        initial_state: Optional[BattleState] = None,
    ) -> Dict[int, Episode]:
        """Extract episodes from a BattleLog.

        Args:
            battle_log: The battle log to process
            initial_state: Optional initial state (will create from metadata if None)

        Returns:
            Dict mapping side -> Episode
        """
        # Create initial state from metadata
        if initial_state is None:
            initial_state = self._create_initial_state(battle_log)

        # Create engine for replay
        engine = BattleEngine(initial_state, self._move_registry)
        state = engine.state
        state.start_battle()

        # Initialize episodes
        episodes = {
            0: Episode(metadata=self._get_episode_metadata(battle_log, 0)),
            1: Episode(metadata=self._get_episode_metadata(battle_log, 1)),
        }

        # Track HP for damage-based rewards
        prev_hp = {
            0: self._get_team_hp(state, 0),
            1: self._get_team_hp(state, 1),
        }

        # Get observations before first turn
        prev_obs = {
            0: self._get_obs(state, 0),
            1: self._get_obs(state, 1),
        }

        # Process each turn
        for turn, events in battle_log.iter_turns():
            if turn == 0:
                continue  # Skip turn 0 (battle start)

            # Get choices for this turn
            choices = battle_log.get_choices_for_turn(turn)

            if not any(choices.values()):
                continue

            # Convert choices to actions
            actions = {}
            for side, side_choices in choices.items():
                if side_choices:
                    actions[side] = choice_to_action(side_choices[0], side)

            # Execute turn
            engine.step(choices)

            # Get new observations
            new_obs = {
                0: self._get_obs(state, 0),
                1: self._get_obs(state, 1),
            }

            # Compute rewards
            rewards = self._compute_rewards(
                state, prev_hp, events, battle_log.metadata.winner_side
            )

            # Update HP tracking
            new_hp = {
                0: self._get_team_hp(state, 0),
                1: self._get_team_hp(state, 1),
            }

            # Check if done
            done = state.ended

            # Create transitions for each side
            for side in [0, 1]:
                if side not in actions:
                    continue

                if not self.config.include_opponent_obs and side == 1:
                    continue

                info = self._build_transition_info(
                    side, turn, events, battle_log
                )

                transition = Transition(
                    obs=prev_obs[side],
                    action=actions[side],
                    reward=rewards[side],
                    next_obs=new_obs[side],
                    done=done,
                    info=info,
                )

                episodes[side].add(transition)

            # Update state for next iteration
            prev_obs = new_obs
            prev_hp = new_hp

            if done:
                break

        return episodes

    def _create_initial_state(self, battle_log: BattleLog) -> BattleState:
        """Create initial state from battle log metadata."""
        meta = battle_log.metadata

        state = BattleState(
            num_sides=2,
            team_size=6,
            active_slots=2 if meta.gametype == "doubles" else 1,
            seed=meta.seed,
            gen=meta.gen,
            game_type=meta.gametype,
        )

        # Load teams from metadata if available
        if meta.teams:
            for side_str, team_data in meta.teams.items():
                side = int(side_str) if side_str.isdigit() else 0
                self._load_team(state, side, team_data)

        return state

    def _load_team(
        self,
        state: BattleState,
        side: int,
        team_data: List[Dict],
    ) -> None:
        """Load team data into state."""
        # This would need to parse team_data format
        # For now, this is a placeholder
        pass

    def _get_team_hp(self, state: BattleState, side: int) -> np.ndarray:
        """Get HP array for a team."""
        hp = np.zeros(state.team_size)
        for i in range(state.team_size):
            pokemon = state.get_pokemon(side, i)
            hp[i] = pokemon.current_hp
        return hp

    def _get_episode_metadata(
        self,
        battle_log: BattleLog,
        side: int,
    ) -> Dict[str, Any]:
        """Build episode metadata."""
        meta = battle_log.metadata
        return {
            "format": meta.format,
            "gen": meta.gen,
            "gametype": meta.gametype,
            "seed": meta.seed,
            "side": side,
            "winner": meta.winner_side,
            "won": meta.winner_side == side,
            "total_turns": meta.total_turns,
        }

    def _compute_rewards(
        self,
        state: BattleState,
        prev_hp: Dict[int, np.ndarray],
        events: List,
        winner: int,
    ) -> Dict[int, float]:
        """Compute rewards based on configuration."""
        rewards = {0: 0.0, 1: 0.0}

        if self.config.reward_mode == "terminal":
            if state.ended:
                for side in [0, 1]:
                    if winner == side:
                        rewards[side] = self.config.win_reward
                    elif winner >= 0:
                        rewards[side] = self.config.lose_reward

        elif self.config.reward_mode == "hp_delta":
            for side in [0, 1]:
                # Reward for damage dealt to opponent
                opp = 1 - side
                curr_hp = self._get_team_hp(state, opp)
                damage_dealt = np.sum(prev_hp[opp] - curr_hp)
                rewards[side] += damage_dealt * self.config.damage_scale

                # Penalty for damage taken
                curr_own_hp = self._get_team_hp(state, side)
                damage_taken = np.sum(prev_hp[side] - curr_own_hp)
                rewards[side] -= damage_taken * self.config.damage_scale

            # Terminal reward
            if state.ended:
                for side in [0, 1]:
                    if winner == side:
                        rewards[side] += self.config.win_reward
                    elif winner >= 0:
                        rewards[side] += self.config.lose_reward

        elif self.config.reward_mode == "per_event":
            # Reward based on events (faints, etc.)
            for event in events:
                if event.event_type == EventType.FAINT:
                    fainted_side = event.side
                    other_side = 1 - fainted_side
                    rewards[other_side] += self.config.faint_reward

            if state.ended:
                for side in [0, 1]:
                    if winner == side:
                        rewards[side] += self.config.win_reward
                    elif winner >= 0:
                        rewards[side] += self.config.lose_reward

        return rewards

    def _build_transition_info(
        self,
        side: int,
        turn: int,
        events: List,
        battle_log: BattleLog,
    ) -> Dict[str, Any]:
        """Build info dict for a transition."""
        info = {
            "turn": turn,
            "side": side,
        }

        if self.config.annotate_agent_type:
            # Would need agent type from battle log metadata
            info["agent_type"] = battle_log.metadata.players.get(str(side), "unknown")

        return info


class DatasetBuilder:
    """Builds offline RL datasets from multiple BattleLogs.

    Supports:
    - Combining trajectories from multiple battles
    - Filtering by agent type, outcome, etc.
    - Exporting in various formats
    """

    def __init__(
        self,
        extractor: Optional[TrajectoryExtractor] = None,
    ):
        """Initialize builder.

        Args:
            extractor: Trajectory extractor to use
        """
        self.extractor = extractor or TrajectoryExtractor()
        self._episodes: List[Episode] = []
        self._metadata: Dict[str, Any] = {
            "num_battles": 0,
            "num_transitions": 0,
        }

    def add_battle_log(
        self,
        battle_log: BattleLog,
        filter_func: Optional[Callable[[Episode], bool]] = None,
    ) -> int:
        """Add episodes from a battle log.

        Args:
            battle_log: Battle log to process
            filter_func: Optional filter for episodes

        Returns:
            Number of episodes added
        """
        episodes = self.extractor.extract_from_log(battle_log)

        added = 0
        for side, episode in episodes.items():
            if filter_func is None or filter_func(episode):
                self._episodes.append(episode)
                self._metadata["num_transitions"] += len(episode)
                added += 1

        self._metadata["num_battles"] += 1
        return added

    def add_battle_logs(
        self,
        battle_logs: Iterator[BattleLog],
        filter_func: Optional[Callable[[Episode], bool]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> int:
        """Add episodes from multiple battle logs.

        Args:
            battle_logs: Iterator of battle logs
            filter_func: Optional filter for episodes
            progress_callback: Called with count after each battle

        Returns:
            Total number of episodes added
        """
        total_added = 0

        for i, log in enumerate(battle_logs):
            added = self.add_battle_log(log, filter_func)
            total_added += added

            if progress_callback:
                progress_callback(i + 1)

        return total_added

    def get_episodes(self) -> List[Episode]:
        """Get all collected episodes."""
        return list(self._episodes)

    def get_transitions(self) -> List[Transition]:
        """Get all transitions from all episodes."""
        transitions = []
        for ep in self._episodes:
            transitions.extend(ep.transitions)
        return transitions

    def filter_by_winner(self, winner: bool = True) -> "DatasetBuilder":
        """Create new builder with filtered episodes.

        Args:
            winner: If True, keep only winning episodes

        Returns:
            New DatasetBuilder with filtered data
        """
        builder = DatasetBuilder(self.extractor)

        for ep in self._episodes:
            won = ep.metadata.get("won", False)
            if won == winner:
                builder._episodes.append(ep)
                builder._metadata["num_transitions"] += len(ep)

        builder._metadata["num_battles"] = len(builder._episodes)
        return builder

    def filter_by_agent_type(self, agent_type: str) -> "DatasetBuilder":
        """Create new builder with episodes from specific agent type.

        Args:
            agent_type: Agent type to filter for

        Returns:
            New DatasetBuilder with filtered data
        """
        builder = DatasetBuilder(self.extractor)

        for ep in self._episodes:
            ep_agent = ep.metadata.get("agent_type", "")
            if agent_type in ep_agent:
                builder._episodes.append(ep)
                builder._metadata["num_transitions"] += len(ep)

        builder._metadata["num_battles"] = len(builder._episodes)
        return builder

    def get_stats(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self._episodes:
            return self._metadata

        wins = sum(1 for ep in self._episodes if ep.metadata.get("won", False))
        turns = [ep.metadata.get("total_turns", len(ep)) for ep in self._episodes]

        return {
            **self._metadata,
            "num_episodes": len(self._episodes),
            "win_episodes": wins,
            "avg_episode_length": np.mean([len(ep) for ep in self._episodes]),
            "avg_turns": np.mean(turns) if turns else 0,
        }

    def to_arrays(self) -> Dict[str, np.ndarray]:
        """Convert dataset to numpy arrays.

        Returns:
            Dict with obs, actions, rewards, next_obs, dones, masks
        """
        transitions = self.get_transitions()

        if not transitions:
            return {}

        obs = np.stack([t.obs for t in transitions])
        next_obs = np.stack([t.next_obs for t in transitions])

        actions = np.array([
            [t.action.kind, t.action.slot, t.action.arg,
             t.action.target_side, t.action.target_slot]
            for t in transitions
        ])

        rewards = np.array([t.reward for t in transitions])
        dones = np.array([t.done for t in transitions])

        return {
            "observations": obs,
            "actions": actions,
            "rewards": rewards,
            "next_observations": next_obs,
            "terminals": dones,
        }

    def save(self, path: str, format: str = "npz") -> None:
        """Save dataset to disk.

        Args:
            path: File path
            format: "npz" or "pickle"
        """
        import pickle

        if format == "npz":
            arrays = self.to_arrays()
            np.savez(path, **arrays, **{f"meta_{k}": v for k, v in self._metadata.items()})

        elif format == "pickle":
            with open(path, 'wb') as f:
                pickle.dump({
                    "episodes": [ep.to_dict() for ep in self._episodes],
                    "metadata": self._metadata,
                }, f)

        else:
            raise ValueError(f"Unknown format: {format}")

    @classmethod
    def load(cls, path: str, format: str = "npz") -> "DatasetBuilder":
        """Load dataset from disk.

        Args:
            path: File path
            format: "npz" or "pickle"

        Returns:
            Loaded DatasetBuilder
        """
        import pickle

        builder = cls()

        if format == "pickle":
            with open(path, 'rb') as f:
                data = pickle.load(f)
            builder._episodes = [Episode.from_dict(ep) for ep in data["episodes"]]
            builder._metadata = data["metadata"]

        else:
            raise ValueError(f"Unknown format: {format}")

        return builder
