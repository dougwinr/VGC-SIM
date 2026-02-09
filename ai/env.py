"""Battle environment for RL and multi-agent training.

This module provides a generic, library-agnostic environment that wraps
the battle engine for reinforcement learning and agent evaluation.

Key features:
- Single entry point for both controlled RL and black-box agent battles
- Configurable observations, rewards, and action spaces
- Full logging support for offline RL and replay
- Deterministic operation via seeded PRNG
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np

from core.battle_state import BattleState
from core.battle import BattleEngine, Choice
from core.battle_log import BattleLog, BattleLogMetadata
from agents.base import Agent, Action, ActionKind


@dataclass
class EnvConfig:
    """Configuration for the battle environment.

    Attributes:
        format: Battle format string (e.g., "gen9vgc2025")
        game_type: "singles" or "doubles"
        team_size: Number of Pokemon per team
        active_slots: Active Pokemon per side (1 for singles, 2 for doubles)
        reward_mode: Reward scheme ("win_loss", "hp_delta", "shaped")
        win_reward: Reward for winning
        lose_reward: Reward (penalty) for losing
        draw_reward: Reward for draw
        hp_reward_scale: Scale factor for HP-based rewards
        faint_reward: Reward per opponent faint
        ko_penalty: Penalty per own faint
        turn_penalty: Per-turn penalty to encourage faster wins
        max_turns: Maximum turns before forced draw
        observation_mode: "raw", "normalized", or "structured"
        log_level: 0=minimal, 1=choices only, 2=full events
    """
    format: str = "gen9vgc2025"
    game_type: str = "doubles"
    team_size: int = 6
    active_slots: int = 2
    reward_mode: str = "win_loss"
    win_reward: float = 1.0
    lose_reward: float = -1.0
    draw_reward: float = 0.0
    hp_reward_scale: float = 0.001
    faint_reward: float = 0.1
    ko_penalty: float = -0.1
    turn_penalty: float = -0.001
    max_turns: int = 200
    observation_mode: str = "raw"
    log_level: int = 1


class BattleEnv:
    """Generic battle environment for RL and multi-agent training.

    This environment wraps the battle engine and provides a standard
    step/reset interface. It supports:

    - Single-agent training: External code controls one side, env manages others
    - Multi-agent training: External code provides actions for all sides
    - Black-box evaluation: Env queries agents internally for all actions

    The environment is library-agnostic and does not depend on Gym or any
    specific RL framework.
    """

    def __init__(
        self,
        player_map: Dict[int, Agent],
        config: Optional[EnvConfig] = None,
        move_registry: Optional[Dict[int, Any]] = None,
        team_generator: Optional[Callable[[int], Any]] = None,
    ):
        """Initialize the battle environment.

        Args:
            player_map: Mapping side_id -> Agent (e.g., {0: RLAgent, 1: HeuristicAgent})
            config: Environment configuration
            move_registry: Optional dict mapping move IDs to MoveData
            team_generator: Optional function to generate teams (side -> team data)
        """
        self.player_map = player_map
        self.config = config or EnvConfig()
        self._move_registry = move_registry or {}
        self._team_generator = team_generator

        # State
        self._state: Optional[BattleState] = None
        self._engine: Optional[BattleEngine] = None
        self._battle_log: Optional[BattleLog] = None
        self._prev_hp: Dict[int, np.ndarray] = {}
        self._done = True
        self._turn = 0
        self._seed: Optional[int] = None

        # Observation space info (computed on first reset)
        self._obs_shape: Optional[Tuple[int, ...]] = None

    @property
    def observation_shape(self) -> Tuple[int, ...]:
        """Get the shape of observations.

        Returns:
            Tuple of observation dimensions
        """
        if self._obs_shape is None:
            # Create temporary state to compute shape
            temp_state = BattleState(
                num_sides=2,
                team_size=self.config.team_size,
                active_slots=self.config.active_slots,
            )
            obs = temp_state.get_observation(0)
            self._obs_shape = obs.shape
        return self._obs_shape

    def reset(
        self,
        seed: Optional[int] = None,
        teams: Optional[Dict[int, Any]] = None,
    ) -> Dict[int, Any]:
        """Initialize a new battle.

        Args:
            seed: Random seed for determinism (None for random)
            teams: Optional pre-specified teams per side

        Returns:
            Dict mapping side_id -> observation
        """
        self._seed = seed

        # Create new battle state
        self._state = BattleState(
            num_sides=2,
            team_size=self.config.team_size,
            active_slots=self.config.active_slots,
            seed=seed,
            game_type=self.config.game_type,
        )

        # Set up teams
        if teams:
            for side, team in teams.items():
                self._set_team(side, team)
        elif self._team_generator:
            for side in range(2):
                team = self._team_generator(side)
                self._set_team(side, team)

        # Initialize engine
        self._engine = BattleEngine(self._state, self._move_registry)

        # Start battle
        self._state.start_battle()
        self._turn = 0
        self._done = False

        # Initialize HP tracking for rewards
        self._prev_hp = {
            side: self._get_team_hp(side) for side in range(2)
        }

        # Initialize battle log
        self._battle_log = BattleLog(
            metadata=BattleLogMetadata(
                format=self.config.format,
                gametype=self.config.game_type,
                seed=seed or 0,
            )
        )

        # Reset agents
        for agent in self.player_map.values():
            agent.reset()

        # Return initial observations
        return self._get_observations()

    def _set_team(self, side: int, team: Any) -> None:
        """Set a team for a side.

        Args:
            side: Side index
            team: Team data (format depends on loader)
        """
        # This is a placeholder - actual implementation depends on
        # how teams are represented in the data module
        pass

    def _get_team_hp(self, side: int) -> np.ndarray:
        """Get HP values for a team.

        Args:
            side: Side index

        Returns:
            Array of current HP values
        """
        hp = np.zeros(self.config.team_size)
        for i in range(self.config.team_size):
            pokemon = self._state.get_pokemon(side, i)
            hp[i] = pokemon.current_hp
        return hp

    def _get_observations(self) -> Dict[int, Any]:
        """Get observations for all sides.

        Returns:
            Dict mapping side_id -> observation
        """
        observations = {}
        for side in self.player_map.keys():
            observations[side] = self._get_observation(side)
        return observations

    def _get_observation(self, side: int) -> Any:
        """Get observation for a single side.

        Args:
            side: Side index

        Returns:
            Observation in configured format
        """
        if self.config.observation_mode == "raw":
            return self._state.get_observation(side)

        elif self.config.observation_mode == "normalized":
            obs = self._state.get_observation(side)
            # Normalize to [0, 1] range (simple approach)
            # In practice, you'd want more sophisticated normalization
            obs = obs.astype(np.float32)
            obs = np.clip(obs / 1000.0, -1.0, 1.0)
            return obs

        elif self.config.observation_mode == "structured":
            return self._get_structured_observation(side)

        else:
            return self._state.get_observation(side)

    def _get_structured_observation(self, side: int) -> Dict[str, Any]:
        """Get a structured observation dict.

        Args:
            side: Side index

        Returns:
            Dict with parsed battle information
        """
        obs = {
            "turn": self._turn,
            "raw": self._state.get_observation(side),
            "your_pokemon": [],
            "opponent_pokemon": [],
            "active": self._state.active[side].tolist(),
            "opponent_active": self._state.active[1 - side].tolist(),
            "side_conditions": self._state.side_conditions[side].tolist(),
            "opponent_side_conditions": self._state.side_conditions[1 - side].tolist(),
            "field": self._state.field.tolist(),
        }

        # Your Pokemon
        for i in range(self.config.team_size):
            pokemon = self._state.get_pokemon(side, i)
            obs["your_pokemon"].append({
                "slot": i,
                "species_id": pokemon.species_id,
                "hp": pokemon.current_hp,
                "max_hp": pokemon.max_hp,
                "status": pokemon.status,
                "active": i in self._state.active[side],
            })

        # Opponent Pokemon (partial info in real games)
        for i in range(self.config.team_size):
            pokemon = self._state.get_pokemon(1 - side, i)
            obs["opponent_pokemon"].append({
                "slot": i,
                "species_id": pokemon.species_id,
                "hp_ratio": pokemon.current_hp / max(pokemon.max_hp, 1),
                "status": pokemon.status,
                "active": i in self._state.active[1 - side],
            })

        return obs

    def _get_legal_actions(self, side: int) -> List[Action]:
        """Get legal actions for a side.

        Args:
            side: Side index

        Returns:
            List of legal Action objects
        """
        legal_actions = []

        for active_slot in range(self.config.active_slots):
            team_slot = self._state.active[side, active_slot]
            if team_slot < 0:
                # Empty slot - pass
                legal_actions.append(Action.pass_action(active_slot))
                continue

            pokemon = self._state.get_pokemon(side, team_slot)
            if pokemon.is_fainted:
                legal_actions.append(Action.pass_action(active_slot))
                continue

            # Move actions
            for move_slot in range(4):
                move_id = pokemon.get_move(move_slot)
                if move_id == 0:
                    continue
                pp = self._state.pokemons[side, team_slot, 28 + move_slot]  # PP slot
                if pp <= 0:
                    continue

                # For simplicity, add actions for each valid target
                # In doubles, there could be multiple targets
                if self.config.active_slots == 1:
                    # Singles: default target
                    legal_actions.append(Action.move(active_slot, move_slot))
                else:
                    # Doubles: add targeting options
                    # Target opponent slots
                    for target_slot in range(self.config.active_slots):
                        opp_team_slot = self._state.active[1 - side, target_slot]
                        if opp_team_slot >= 0:
                            opp_pokemon = self._state.get_pokemon(1 - side, opp_team_slot)
                            if not opp_pokemon.is_fainted:
                                legal_actions.append(Action.move(
                                    active_slot, move_slot, 1 - side, target_slot
                                ))

                    # If no opponent targets available, still allow the move
                    if not any(a.kind == ActionKind.MOVE and a.slot == active_slot
                              for a in legal_actions):
                        legal_actions.append(Action.move(active_slot, move_slot))

            # Switch actions
            for bench_slot in range(self.config.team_size):
                if bench_slot in self._state.active[side]:
                    continue  # Already active
                bench_pokemon = self._state.get_pokemon(side, bench_slot)
                if bench_pokemon.is_fainted:
                    continue
                if bench_pokemon.max_hp == 0:
                    continue  # Invalid Pokemon
                legal_actions.append(Action.switch(active_slot, bench_slot))

        # Ensure at least one action (pass) exists
        if not legal_actions:
            legal_actions.append(Action.pass_action(0))

        return legal_actions

    def _action_to_choice(self, action: Action, side: int) -> Choice:
        """Convert an agent Action to engine Choice.

        Args:
            action: Agent action
            side: Side index

        Returns:
            Engine Choice object
        """
        if action.kind == ActionKind.MOVE:
            # Convert target from active slot to encoded format
            target = 0
            if action.target_side >= 0 and action.target_slot >= 0:
                if action.target_side == side:
                    # Targeting ally
                    target = -(action.target_slot + 1)
                else:
                    # Targeting opponent
                    target = action.target_slot + 1

            return Choice(
                choice_type='move',
                slot=action.slot,
                move_slot=action.arg,
                target=target,
            )

        elif action.kind == ActionKind.SWITCH:
            return Choice(
                choice_type='switch',
                slot=action.slot,
                switch_to=action.arg,
            )

        else:  # PASS
            return Choice(
                choice_type='pass',
                slot=action.slot,
            )

    def _compute_rewards(self) -> Dict[int, float]:
        """Compute rewards for all sides.

        Returns:
            Dict mapping side_id -> reward
        """
        rewards = {}

        for side in self.player_map.keys():
            reward = 0.0

            # Terminal rewards
            if self._done:
                if self._engine.winner == side:
                    reward += self.config.win_reward
                elif self._engine.winner >= 0:
                    reward += self.config.lose_reward
                else:
                    reward += self.config.draw_reward

            # Shaping rewards
            if self.config.reward_mode in ("hp_delta", "shaped"):
                # HP delta reward
                current_hp = self._get_team_hp(side)
                opp_hp = self._get_team_hp(1 - side)
                prev_hp = self._prev_hp[side]
                prev_opp_hp = self._prev_hp[1 - side]

                # Reward for damage dealt
                damage_dealt = np.sum(prev_opp_hp - opp_hp)
                reward += damage_dealt * self.config.hp_reward_scale

                # Penalty for damage taken
                damage_taken = np.sum(prev_hp - current_hp)
                reward -= damage_taken * self.config.hp_reward_scale

            if self.config.reward_mode == "shaped":
                # Faint bonuses/penalties
                current_fainted = sum(
                    1 for i in range(self.config.team_size)
                    if self._state.get_pokemon(1 - side, i).is_fainted
                )
                prev_fainted = sum(
                    1 for i in range(self.config.team_size)
                    if self._prev_hp[1 - side][i] == 0
                )
                new_faints = current_fainted - prev_fainted
                reward += new_faints * self.config.faint_reward

                # KO penalties
                own_fainted = sum(
                    1 for i in range(self.config.team_size)
                    if self._state.get_pokemon(side, i).is_fainted
                )
                prev_own_fainted = sum(
                    1 for i in range(self.config.team_size)
                    if self._prev_hp[side][i] == 0
                )
                own_new_faints = own_fainted - prev_own_fainted
                reward += own_new_faints * self.config.ko_penalty

                # Turn penalty
                reward += self.config.turn_penalty

            rewards[side] = reward

        return rewards

    def _get_info(self, side: int) -> Dict[str, Any]:
        """Get additional info for a side.

        Args:
            side: Side index

        Returns:
            Info dict
        """
        return {
            "side": side,
            "turn": self._turn,
            "winner": self._engine.winner if self._done else -1,
            "legal_actions": self._get_legal_actions(side),
            "move_names": {},  # Could populate with move data
            "team_names": [],  # Could populate with Pokemon names
        }

    def step(
        self,
        actions: Optional[Dict[int, Action]] = None,
    ) -> Tuple[Dict[int, Any], Dict[int, float], bool, Dict[str, Any]]:
        """Execute one turn of battle.

        If actions is None, queries each Agent in player_map for actions.
        If actions is provided, uses those actions for the specified sides
        and queries agents for remaining sides.

        Args:
            actions: Optional dict mapping side_id -> Action

        Returns:
            Tuple of (observations, rewards, done, info)
            - observations: Dict mapping side_id -> observation
            - rewards: Dict mapping side_id -> float reward
            - done: True if battle ended
            - info: Additional information dict
        """
        if self._done:
            raise RuntimeError("Cannot step a finished battle. Call reset() first.")

        actions = actions or {}

        # Collect actions for all sides
        all_actions: Dict[int, List[Action]] = {0: [], 1: []}

        for side in range(2):
            if side in actions:
                # Use provided action
                action = actions[side]
                all_actions[side].append(action)
            elif side in self.player_map:
                # Query agent
                agent = self.player_map[side]
                obs = self._get_observation(side)
                legal = self._get_legal_actions(side)
                info = self._get_info(side)
                action = agent.act(obs, legal, info)
                all_actions[side].append(action)

                # Log the choice
                if self.config.log_level >= 1 and self._battle_log:
                    self._battle_log.add_choice(
                        turn=self._turn,
                        side=side,
                        slot=action.slot,
                        choice=self._action_to_choice(action, side),
                    )

        # Convert actions to choices
        choices: Dict[int, List[Choice]] = {}
        for side, side_actions in all_actions.items():
            choices[side] = [self._action_to_choice(a, side) for a in side_actions]

        # Execute turn
        self._turn += 1
        battle_continues = self._engine.step(choices)
        self._done = not battle_continues

        # Check max turns
        if self._turn >= self.config.max_turns and not self._done:
            self._done = True
            self._engine.ended = True
            self._engine.winner = -1  # Draw

        # Compute rewards
        rewards = self._compute_rewards()

        # Update HP tracking
        self._prev_hp = {
            side: self._get_team_hp(side) for side in range(2)
        }

        # Get observations
        observations = self._get_observations()

        # Build info
        info = {
            "turn": self._turn,
            "done": self._done,
            "winner": self._engine.winner,
            "battle_log": self._battle_log,
        }

        # Notify agents if battle ended
        if self._done:
            for side, agent in self.player_map.items():
                agent.on_battle_end(self._engine.winner, {"side": side})

        return observations, rewards, self._done, info

    def run_battle(
        self,
        seed: Optional[int] = None,
        teams: Optional[Dict[int, Any]] = None,
        max_turns: Optional[int] = None,
    ) -> Tuple[int, BattleLog]:
        """Run a complete battle using internal agents.

        Convenience method that runs reset() and step() until done.

        Args:
            seed: Random seed
            teams: Optional teams
            max_turns: Override max turns

        Returns:
            Tuple of (winner_side, battle_log)
        """
        if max_turns:
            original_max = self.config.max_turns
            self.config.max_turns = max_turns

        self.reset(seed=seed, teams=teams)

        while not self._done:
            _, _, done, _ = self.step()

        if max_turns:
            self.config.max_turns = original_max

        return self._engine.winner, self._battle_log

    def get_battle_log(self) -> Optional[BattleLog]:
        """Get the current battle log.

        Returns:
            BattleLog or None if no battle in progress
        """
        return self._battle_log

    def get_state(self) -> Optional[BattleState]:
        """Get the current battle state.

        Returns:
            BattleState or None if no battle in progress
        """
        return self._state

    def clone(self) -> "BattleEnv":
        """Create a clone of this environment.

        Returns:
            New BattleEnv with same config but independent state
        """
        new_env = BattleEnv(
            player_map=self.player_map.copy(),
            config=self.config,
            move_registry=self._move_registry,
            team_generator=self._team_generator,
        )
        return new_env


class SingleAgentEnv:
    """Wrapper that presents BattleEnv as a single-agent environment.

    For RL training where one side is controlled by the learning agent
    and the other side(s) are controlled by fixed opponents.
    """

    def __init__(
        self,
        env: BattleEnv,
        agent_side: int = 0,
    ):
        """Initialize single-agent wrapper.

        Args:
            env: The underlying BattleEnv
            agent_side: Which side the learning agent controls
        """
        self.env = env
        self.agent_side = agent_side

    @property
    def observation_shape(self) -> Tuple[int, ...]:
        """Get observation shape."""
        return self.env.observation_shape

    def reset(
        self,
        seed: Optional[int] = None,
        teams: Optional[Dict[int, Any]] = None,
    ) -> Any:
        """Reset and return observation for agent's side.

        Args:
            seed: Random seed
            teams: Optional teams

        Returns:
            Observation for agent_side
        """
        observations = self.env.reset(seed=seed, teams=teams)
        return observations.get(self.agent_side)

    def step(self, action: Action) -> Tuple[Any, float, bool, Dict[str, Any]]:
        """Take a step with the agent's action.

        Args:
            action: Action for agent's side

        Returns:
            Tuple of (observation, reward, done, info)
        """
        observations, rewards, done, info = self.env.step({self.agent_side: action})

        return (
            observations.get(self.agent_side),
            rewards.get(self.agent_side, 0.0),
            done,
            info,
        )

    def get_legal_actions(self) -> List[Action]:
        """Get legal actions for the agent's side.

        Returns:
            List of legal Action objects
        """
        return self.env._get_legal_actions(self.agent_side)

    def get_observation(self) -> Any:
        """Get current observation for agent's side.

        Returns:
            Current observation
        """
        return self.env._get_observation(self.agent_side)
