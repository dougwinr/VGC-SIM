"""Action and observation encoding utilities.

This module provides standardized encoding/decoding for:
- Action spaces (converting between Action objects and integers)
- Observations (normalizing and structuring battle state)
- Action masks (legal action filtering)
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from .base import Action, ActionKind


@dataclass
class ActionSpaceConfig:
    """Configuration for action space encoding.

    Attributes:
        num_active_slots: Active Pokemon per side (1 for singles, 2 for doubles)
        num_moves: Maximum moves per Pokemon
        team_size: Total team size
        include_targets: Whether to include targeting in action space
        include_mega: Whether to include mega evolution
        include_zmove: Whether to include Z-moves
        include_dynamax: Whether to include Dynamax
        include_tera: Whether to include Terastallization
    """
    num_active_slots: int = 2
    num_moves: int = 4
    team_size: int = 6
    include_targets: bool = True
    include_mega: bool = False
    include_zmove: bool = False
    include_dynamax: bool = False
    include_tera: bool = False


class ActionEncoder:
    """Encodes and decodes actions to/from integers.

    Provides a fixed-size discrete action space for RL algorithms.
    The encoding scheme is:

    For each active slot:
      - Move actions: num_moves * num_targets
      - Switch actions: team_size - num_active_slots

    Plus:
      - Pass action(s)
    """

    def __init__(self, config: Optional[ActionSpaceConfig] = None):
        """Initialize encoder.

        Args:
            config: Action space configuration
        """
        self.config = config or ActionSpaceConfig()
        self._build_action_map()

    def _build_action_map(self) -> None:
        """Build the action index mapping."""
        self._actions: List[Action] = []
        self._action_to_idx: Dict[Tuple, int] = {}

        cfg = self.config

        # Number of targets per move
        if cfg.include_targets and cfg.num_active_slots > 1:
            num_targets = cfg.num_active_slots  # Target opponent slots
        else:
            num_targets = 1

        # For each active slot
        for active_slot in range(cfg.num_active_slots):
            # Move actions
            for move_slot in range(cfg.num_moves):
                if num_targets == 1:
                    action = Action.move(active_slot, move_slot)
                    self._add_action(action)
                else:
                    for target_slot in range(num_targets):
                        # Default to targeting opponent side
                        action = Action.move(active_slot, move_slot, -1, target_slot)
                        self._add_action(action)

            # Switch actions
            for bench_slot in range(cfg.num_active_slots, cfg.team_size):
                action = Action.switch(active_slot, bench_slot)
                self._add_action(action)

        # Pass action
        self._add_action(Action.pass_action(0))

    def _add_action(self, action: Action) -> None:
        """Add an action to the mapping."""
        idx = len(self._actions)
        self._actions.append(action)
        key = (action.kind, action.slot, action.arg, action.target_slot)
        self._action_to_idx[key] = idx

    @property
    def num_actions(self) -> int:
        """Total number of discrete actions."""
        return len(self._actions)

    def encode(self, action: Action) -> int:
        """Encode an Action to integer.

        Args:
            action: Action object

        Returns:
            Integer action index

        Raises:
            ValueError: If action cannot be encoded
        """
        # Try exact match first
        key = (action.kind, action.slot, action.arg, action.target_slot)
        if key in self._action_to_idx:
            return self._action_to_idx[key]

        # Try without target
        key_no_target = (action.kind, action.slot, action.arg, -1)
        if key_no_target in self._action_to_idx:
            return self._action_to_idx[key_no_target]

        # Try with target slot 0
        key_target_0 = (action.kind, action.slot, action.arg, 0)
        if key_target_0 in self._action_to_idx:
            return self._action_to_idx[key_target_0]

        raise ValueError(f"Cannot encode action: {action}")

    def decode(self, action_idx: int) -> Action:
        """Decode integer to Action.

        Args:
            action_idx: Integer action index

        Returns:
            Action object

        Raises:
            ValueError: If index is out of range
        """
        if 0 <= action_idx < len(self._actions):
            return self._actions[action_idx]
        raise ValueError(f"Action index {action_idx} out of range [0, {len(self._actions)})")

    def get_action_mask(
        self,
        legal_actions: List[Action],
    ) -> np.ndarray:
        """Create boolean mask for legal actions.

        Args:
            legal_actions: List of legal Action objects

        Returns:
            Boolean array where True = legal
        """
        mask = np.zeros(self.num_actions, dtype=bool)

        for action in legal_actions:
            try:
                idx = self.encode(action)
                mask[idx] = True
            except ValueError:
                # Action not in our encoding scheme
                pass

        return mask

    def filter_legal(
        self,
        legal_actions: List[Action],
    ) -> List[int]:
        """Get indices of legal actions.

        Args:
            legal_actions: List of legal Action objects

        Returns:
            List of legal action indices
        """
        indices = []
        for action in legal_actions:
            try:
                idx = self.encode(action)
                indices.append(idx)
            except ValueError:
                pass
        return indices

    def sample_legal(
        self,
        legal_actions: List[Action],
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[int, Action]:
        """Sample a random legal action.

        Args:
            legal_actions: List of legal actions
            rng: Random number generator

        Returns:
            Tuple of (action_index, action)
        """
        if rng is None:
            rng = np.random.default_rng()

        indices = self.filter_legal(legal_actions)
        if not indices:
            return 0, Action.pass_action(0)

        idx = indices[rng.integers(0, len(indices))]
        return idx, self._actions[idx]


class ObservationEncoder:
    """Encodes battle state into normalized observation arrays.

    Provides various encoding schemes:
    - "flat": Simple concatenated array
    - "normalized": Values scaled to [0, 1] or [-1, 1]
    - "structured": Dictionary with named components
    """

    def __init__(
        self,
        mode: str = "normalized",
        include_hidden: bool = False,
    ):
        """Initialize encoder.

        Args:
            mode: Encoding mode ("flat", "normalized", "structured")
            include_hidden: Whether to include hidden information
        """
        self.mode = mode
        self.include_hidden = include_hidden

        # Normalization constants
        self._hp_max = 1000  # Max reasonable HP
        self._stat_max = 500  # Max reasonable stat
        self._stage_min = -6
        self._stage_max = 6

    def encode(
        self,
        raw_obs: np.ndarray,
        side: int,
        info: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Encode observation.

        Args:
            raw_obs: Raw observation from BattleState.get_observation()
            side: Side index
            info: Optional additional info

        Returns:
            Encoded observation in configured format
        """
        if self.mode == "flat":
            return raw_obs.astype(np.float32)

        elif self.mode == "normalized":
            return self._normalize(raw_obs)

        elif self.mode == "structured":
            return self._structure(raw_obs, side, info)

        else:
            return raw_obs

    def _normalize(self, obs: np.ndarray) -> np.ndarray:
        """Normalize observation values.

        Args:
            obs: Raw observation

        Returns:
            Normalized float32 array in roughly [-1, 1] range
        """
        # Simple normalization: divide by reasonable max values
        # This is a basic approach; more sophisticated normalization
        # would use running statistics or predefined ranges per field

        normalized = obs.astype(np.float32)

        # The observation is a flat array from BattleState.get_observation()
        # Structure depends on layout, but we can apply general normalization

        # Clip to reasonable range and scale
        normalized = np.clip(normalized, -10000, 10000)
        normalized = normalized / 1000.0  # Simple scaling

        return normalized

    def _structure(
        self,
        obs: np.ndarray,
        side: int,
        info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create structured observation dict.

        Args:
            obs: Raw observation
            side: Side index
            info: Optional additional info

        Returns:
            Dictionary with named components
        """
        # This would need to know the exact layout to unpack properly
        # For now, return a simple structure
        return {
            "raw": obs,
            "side": side,
            "normalized": self._normalize(obs),
        }

    def get_space_info(self, obs_size: int) -> Dict[str, Any]:
        """Get observation space information.

        Args:
            obs_size: Size of raw observation

        Returns:
            Dict with shape, dtype, bounds
        """
        if self.mode == "structured":
            return {
                "type": "dict",
                "spaces": {
                    "raw": {"shape": (obs_size,), "dtype": np.float32},
                    "normalized": {"shape": (obs_size,), "dtype": np.float32},
                    "side": {"shape": (), "dtype": np.int32},
                },
            }
        else:
            return {
                "type": "box",
                "shape": (obs_size,),
                "dtype": np.float32,
                "low": -10.0 if self.mode == "normalized" else -np.inf,
                "high": 10.0 if self.mode == "normalized" else np.inf,
            }


class FeatureExtractor:
    """Extracts meaningful features from battle state.

    Useful for:
    - Dimensionality reduction
    - Interpretable features for heuristics
    - Input preprocessing for neural networks
    """

    def __init__(self):
        """Initialize extractor."""
        pass

    def extract(
        self,
        state: Any,
        side: int,
    ) -> Dict[str, np.ndarray]:
        """Extract features from battle state.

        Args:
            state: BattleState object
            side: Side to extract for

        Returns:
            Dict of named feature arrays
        """
        features = {}

        # HP ratios
        hp_ratios = []
        for i in range(state.team_size):
            pokemon = state.get_pokemon(side, i)
            if pokemon.max_hp > 0:
                hp_ratios.append(pokemon.current_hp / pokemon.max_hp)
            else:
                hp_ratios.append(0.0)
        features["own_hp_ratios"] = np.array(hp_ratios, dtype=np.float32)

        # Opponent HP ratios
        opp_hp_ratios = []
        opp_side = 1 - side
        for i in range(state.team_size):
            pokemon = state.get_pokemon(opp_side, i)
            if pokemon.max_hp > 0:
                opp_hp_ratios.append(pokemon.current_hp / pokemon.max_hp)
            else:
                opp_hp_ratios.append(0.0)
        features["opp_hp_ratios"] = np.array(opp_hp_ratios, dtype=np.float32)

        # Active Pokemon indices
        features["active_slots"] = state.active[side].astype(np.float32)
        features["opp_active_slots"] = state.active[opp_side].astype(np.float32)

        # Team alive count
        own_alive = sum(1 for i in range(state.team_size)
                       if not state.get_pokemon(side, i).is_fainted)
        opp_alive = sum(1 for i in range(state.team_size)
                       if not state.get_pokemon(opp_side, i).is_fainted)
        features["alive_count"] = np.array([own_alive, opp_alive], dtype=np.float32)

        # Field conditions (normalized)
        features["field"] = state.field.astype(np.float32) / 10.0
        features["side_conditions"] = state.side_conditions[side].astype(np.float32) / 10.0
        features["opp_side_conditions"] = state.side_conditions[opp_side].astype(np.float32) / 10.0

        # Turn number (normalized)
        features["turn"] = np.array([state.turn / 100.0], dtype=np.float32)

        return features

    def flatten_features(self, features: Dict[str, np.ndarray]) -> np.ndarray:
        """Flatten feature dict to single array.

        Args:
            features: Dict of named features

        Returns:
            Concatenated flat array
        """
        arrays = []
        for key in sorted(features.keys()):
            arr = features[key]
            arrays.append(arr.flatten())
        return np.concatenate(arrays)
