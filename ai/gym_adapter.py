"""Optional Gym/Gymnasium adapter for BattleEnv.

This module provides wrappers that make BattleEnv compatible with
OpenAI Gym and Gymnasium interfaces. The adapters are optional and
only work if gym/gymnasium is installed.

Usage:
    from ai.gym_adapter import GymEnv

    env = GymEnv(battle_env)
    obs, info = env.reset()
    obs, reward, terminated, truncated, info = env.step(action)
"""
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from agents.base import Agent, Action, ActionKind
from .env import BattleEnv, EnvConfig


# Type aliases for gym compatibility
ObsType = np.ndarray
ActType = int


class GymEnv:
    """Gymnasium-compatible wrapper for BattleEnv.

    Implements the Gymnasium Env interface:
    - reset() -> (obs, info)
    - step(action) -> (obs, reward, terminated, truncated, info)
    - observation_space, action_space properties

    This wrapper presents the environment as a single-agent MDP where
    one side is controlled by the RL agent and other sides use internal agents.
    """

    # Gym metadata
    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(
        self,
        battle_env: BattleEnv,
        agent_side: int = 0,
        action_encoding: str = "flat",
        render_mode: Optional[str] = None,
    ):
        """Initialize Gym wrapper.

        Args:
            battle_env: The underlying BattleEnv
            agent_side: Which side the RL agent controls
            action_encoding: "flat" (single int) or "multi" (dict)
            render_mode: Gym render mode
        """
        self.env = battle_env
        self.agent_side = agent_side
        self.action_encoding = action_encoding
        self.render_mode = render_mode

        # Build action space info
        self._action_map: List[Action] = []
        self._build_action_space()

        # Observation and action space (gym.spaces compatible dicts)
        self._observation_space = None
        self._action_space = None
        self._setup_spaces()

    def _build_action_space(self) -> None:
        """Build mapping from integers to Action objects."""
        config = self.env.config

        # For each active slot
        for active_slot in range(config.active_slots):
            # Move actions (4 moves * possible targets)
            for move_slot in range(4):
                if config.active_slots == 1:
                    # Singles: one target option per move
                    self._action_map.append(Action.move(active_slot, move_slot))
                else:
                    # Doubles: multiple target options
                    for target_slot in range(config.active_slots):
                        self._action_map.append(
                            Action.move(active_slot, move_slot, 1 - self.agent_side, target_slot)
                        )

            # Switch actions (to each bench slot)
            for bench_slot in range(config.active_slots, config.team_size):
                self._action_map.append(Action.switch(active_slot, bench_slot))

        # Pass action
        self._action_map.append(Action.pass_action(0))

    def _setup_spaces(self) -> None:
        """Set up observation and action spaces."""
        # Get observation shape
        obs_shape = self.env.observation_shape

        self._observation_space = {
            "shape": obs_shape,
            "dtype": np.float32,
            "low": -np.inf,
            "high": np.inf,
        }

        self._action_space = {
            "n": len(self._action_map),
            "dtype": np.int64,
        }

    @property
    def observation_space(self) -> Dict[str, Any]:
        """Return observation space info."""
        return self._observation_space

    @property
    def action_space(self) -> Dict[str, Any]:
        """Return action space info."""
        return self._action_space

    @property
    def unwrapped(self) -> BattleEnv:
        """Return the underlying environment."""
        return self.env

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ObsType, Dict[str, Any]]:
        """Reset the environment.

        Args:
            seed: Random seed
            options: Additional options (e.g., teams)

        Returns:
            Tuple of (observation, info)
        """
        options = options or {}
        teams = options.get("teams")

        observations = self.env.reset(seed=seed, teams=teams)

        obs = observations.get(self.agent_side)
        if obs is None:
            obs = np.zeros(self.observation_space["shape"], dtype=np.float32)
        else:
            obs = obs.astype(np.float32)

        info = {
            "legal_actions": self._get_legal_action_mask(),
            "legal_action_indices": self._get_legal_action_indices(),
        }

        return obs, info

    def step(
        self,
        action: ActType,
    ) -> Tuple[ObsType, float, bool, bool, Dict[str, Any]]:
        """Take a step in the environment.

        Args:
            action: Action index (integer)

        Returns:
            Tuple of (obs, reward, terminated, truncated, info)
        """
        # Decode action
        agent_action = self._decode_action(action)

        # Step environment
        observations, rewards, done, info = self.env.step({self.agent_side: agent_action})

        # Get observation
        obs = observations.get(self.agent_side)
        if obs is None:
            obs = np.zeros(self.observation_space["shape"], dtype=np.float32)
        else:
            obs = obs.astype(np.float32)

        # Get reward
        reward = float(rewards.get(self.agent_side, 0.0))

        # Gym v26+ uses terminated/truncated
        terminated = done
        truncated = False  # Could check for max_turns

        # Build info
        step_info = {
            "winner": info.get("winner", -1),
            "turn": info.get("turn", 0),
            "legal_actions": self._get_legal_action_mask(),
            "legal_action_indices": self._get_legal_action_indices(),
        }

        return obs, reward, terminated, truncated, step_info

    def _decode_action(self, action: int) -> Action:
        """Decode integer action to Action object.

        Args:
            action: Integer action index

        Returns:
            Action object
        """
        if 0 <= action < len(self._action_map):
            candidate = self._action_map[action]

            # Check if this action is legal
            legal = self.env._get_legal_actions(self.agent_side)

            # Find matching legal action
            for legal_action in legal:
                if (legal_action.kind == candidate.kind and
                    legal_action.slot == candidate.slot and
                    legal_action.arg == candidate.arg):
                    return legal_action

            # Fall back to first legal action if selected action is illegal
            if legal:
                return legal[0]

        # Default to pass
        return Action.pass_action(0)

    def _get_legal_action_mask(self) -> np.ndarray:
        """Get boolean mask of legal actions.

        Returns:
            Boolean array where True = legal
        """
        legal = self.env._get_legal_actions(self.agent_side)
        mask = np.zeros(len(self._action_map), dtype=bool)

        for legal_action in legal:
            for i, mapped in enumerate(self._action_map):
                if (mapped.kind == legal_action.kind and
                    mapped.slot == legal_action.slot and
                    mapped.arg == legal_action.arg):
                    mask[i] = True
                    break

        return mask

    def _get_legal_action_indices(self) -> List[int]:
        """Get list of legal action indices.

        Returns:
            List of legal action integers
        """
        mask = self._get_legal_action_mask()
        return [i for i, legal in enumerate(mask) if legal]

    def render(self) -> Optional[str]:
        """Render the environment.

        Returns:
            String representation if render_mode is "ansi"
        """
        if self.render_mode == "ansi":
            state = self.env.get_state()
            if state:
                return str(state)
        return None

    def close(self) -> None:
        """Clean up resources."""
        pass


class VectorGymEnv:
    """Vectorized Gym environment for parallel battles.

    Runs multiple BattleEnv instances in parallel for faster training.
    """

    def __init__(
        self,
        env_fns: List[callable],
        agent_side: int = 0,
    ):
        """Initialize vectorized environment.

        Args:
            env_fns: List of functions that create BattleEnv instances
            agent_side: Which side the RL agent controls
        """
        self.envs = [GymEnv(fn(), agent_side) for fn in env_fns]
        self.num_envs = len(self.envs)
        self.agent_side = agent_side

    @property
    def single_observation_space(self) -> Dict[str, Any]:
        """Return single env observation space."""
        return self.envs[0].observation_space

    @property
    def single_action_space(self) -> Dict[str, Any]:
        """Return single env action space."""
        return self.envs[0].action_space

    def reset(
        self,
        seed: Optional[int] = None,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Reset all environments.

        Args:
            seed: Base seed (will be incremented for each env)

        Returns:
            Tuple of (stacked observations, list of infos)
        """
        observations = []
        infos = []

        for i, env in enumerate(self.envs):
            env_seed = seed + i if seed is not None else None
            obs, info = env.reset(seed=env_seed)
            observations.append(obs)
            infos.append(info)

        return np.stack(observations), infos

    def step(
        self,
        actions: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[Dict[str, Any]]]:
        """Take a step in all environments.

        Args:
            actions: Array of actions, one per environment

        Returns:
            Tuple of (obs, rewards, terminated, truncated, infos)
        """
        observations = []
        rewards = []
        terminated = []
        truncated = []
        infos = []

        for i, (env, action) in enumerate(zip(self.envs, actions)):
            obs, reward, term, trunc, info = env.step(int(action))
            observations.append(obs)
            rewards.append(reward)
            terminated.append(term)
            truncated.append(trunc)
            infos.append(info)

        return (
            np.stack(observations),
            np.array(rewards),
            np.array(terminated),
            np.array(truncated),
            infos,
        )

    def close(self) -> None:
        """Close all environments."""
        for env in self.envs:
            env.close()


def make_gym_env(
    opponent: Agent,
    config: Optional[EnvConfig] = None,
    agent_side: int = 0,
    **kwargs,
) -> GymEnv:
    """Factory function to create a Gym-compatible environment.

    Args:
        opponent: Agent to play against
        config: Environment configuration
        agent_side: Which side the RL agent controls
        **kwargs: Additional BattleEnv arguments

    Returns:
        GymEnv instance
    """
    from agents import RandomAgent

    # Create a placeholder agent for the RL side
    # (actions will be provided via step())
    placeholder = RandomAgent(name="RLPlaceholder")

    if agent_side == 0:
        player_map = {0: placeholder, 1: opponent}
    else:
        player_map = {0: opponent, 1: placeholder}

    battle_env = BattleEnv(
        player_map=player_map,
        config=config or EnvConfig(),
        **kwargs,
    )

    return GymEnv(battle_env, agent_side=agent_side)
