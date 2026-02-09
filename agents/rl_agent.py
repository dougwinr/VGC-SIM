"""RL policy agent for Pokemon battles.

This module provides an agent that wraps reinforcement learning policies.
It handles observation encoding, action masking, and policy inference.
"""
from typing import Any, Callable, Dict, List, Optional, Protocol, Union
import numpy as np

from .base import Agent, Action, ActionKind


class PolicyProtocol(Protocol):
    """Protocol for RL policy models.

    Any policy that implements this protocol can be used with RLAgent.
    This allows flexibility in the underlying RL framework (PyTorch, TF, JAX, etc.).
    """

    def __call__(self, observation: np.ndarray, action_mask: np.ndarray) -> np.ndarray:
        """Compute action scores/probabilities.

        Args:
            observation: Encoded observation array
            action_mask: Boolean mask where True = legal action

        Returns:
            Array of action scores/logits (before masking/softmax)
        """
        ...


class RLAgent(Agent):
    """Agent that wraps an RL policy model.

    Handles:
    - Encoding observations into numeric arrays
    - Computing action masks from legal actions
    - Running the policy to get action scores
    - Selecting actions (argmax, sampling, epsilon-greedy)

    The agent is framework-agnostic; it accepts any policy that follows
    the PolicyProtocol (takes observation + mask, returns scores).
    """

    def __init__(
        self,
        policy: Callable[[np.ndarray, np.ndarray], np.ndarray],
        name: str = "RLAgent",
        action_space_size: int = 14,  # 4 moves * 2 targets + 6 switches (simplified)
        observation_encoder: Optional[Callable[[Any], np.ndarray]] = None,
        action_decoder: Optional[Callable[[int, List[Action]], Action]] = None,
        selection_mode: str = "argmax",
        epsilon: float = 0.0,
        temperature: float = 1.0,
        seed: Optional[int] = None,
    ):
        """Initialize the RL agent.

        Args:
            policy: Policy function (observation, mask) -> action_scores
            name: Agent name
            action_space_size: Size of the action space for encoding
            observation_encoder: Custom function to encode observations to arrays
            action_decoder: Custom function to decode action indices to Actions
            selection_mode: "argmax", "sample", or "epsilon_greedy"
            epsilon: Exploration rate for epsilon-greedy
            temperature: Temperature for sampling (higher = more random)
            seed: Random seed for reproducibility
        """
        super().__init__(name)
        self.policy = policy
        self.action_space_size = action_space_size
        self._encode_obs = observation_encoder or self._default_encode_observation
        self._decode_action = action_decoder or self._default_decode_action
        self.selection_mode = selection_mode
        self.epsilon = epsilon
        self.temperature = temperature
        self._rng = np.random.default_rng(seed)

        # Statistics tracking
        self._action_counts: Dict[int, int] = {}
        self._total_actions = 0

    def _default_encode_observation(self, observation: Any) -> np.ndarray:
        """Default observation encoder.

        Args:
            observation: Raw observation (numpy array or dict)

        Returns:
            Flattened numpy array
        """
        if isinstance(observation, np.ndarray):
            return observation.astype(np.float32).flatten()
        elif isinstance(observation, dict) and "raw" in observation:
            return np.asarray(observation["raw"], dtype=np.float32).flatten()
        else:
            # Attempt to convert to array
            return np.asarray(observation, dtype=np.float32).flatten()

    def _default_decode_action(self, action_idx: int, legal_actions: List[Action]) -> Action:
        """Default action decoder.

        Maps action index to legal action. This default implementation
        assumes the action_idx maps to the index in legal_actions.

        Args:
            action_idx: Selected action index
            legal_actions: List of legal actions

        Returns:
            The corresponding Action
        """
        # Simple mapping: action_idx is index into legal_actions
        if 0 <= action_idx < len(legal_actions):
            return legal_actions[action_idx]
        # Fallback: return first legal action
        return legal_actions[0]

    def _build_action_mask(self, legal_actions: List[Action]) -> np.ndarray:
        """Build action mask from legal actions.

        Args:
            legal_actions: List of legal Action objects

        Returns:
            Boolean mask array of shape (action_space_size,)
        """
        mask = np.zeros(self.action_space_size, dtype=bool)

        # Mark legal action indices
        # Default: just mark indices up to len(legal_actions)
        for i in range(min(len(legal_actions), self.action_space_size)):
            mask[i] = True

        return mask

    def _select_action(self, scores: np.ndarray, mask: np.ndarray) -> int:
        """Select an action from scores.

        Args:
            scores: Action scores/logits
            mask: Boolean mask of legal actions

        Returns:
            Selected action index
        """
        # Apply mask: set illegal actions to -inf
        masked_scores = np.where(mask, scores, -np.inf)

        if self.selection_mode == "argmax":
            return int(np.argmax(masked_scores))

        elif self.selection_mode == "sample":
            # Softmax with temperature
            scores_shifted = masked_scores - np.max(masked_scores[mask])
            exp_scores = np.exp(scores_shifted / max(self.temperature, 1e-8))
            exp_scores = np.where(mask, exp_scores, 0.0)
            probs = exp_scores / (np.sum(exp_scores) + 1e-8)
            return int(self._rng.choice(len(probs), p=probs))

        elif self.selection_mode == "epsilon_greedy":
            if self._rng.random() < self.epsilon:
                # Random legal action
                legal_indices = np.where(mask)[0]
                return int(self._rng.choice(legal_indices))
            else:
                return int(np.argmax(masked_scores))

        else:
            raise ValueError(f"Unknown selection mode: {self.selection_mode}")

    def act(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> Action:
        """Select an action using the RL policy.

        Args:
            observation: Current battle state
            legal_actions: List of legal actions
            info: Optional additional information

        Returns:
            Selected Action
        """
        if not legal_actions:
            raise ValueError("No legal actions available")

        # Encode observation
        obs_array = self._encode_obs(observation)

        # Build action mask
        mask = self._build_action_mask(legal_actions)

        # Get policy scores
        scores = self.policy(obs_array, mask)

        # Select action index
        action_idx = self._select_action(scores, mask)

        # Track statistics
        self._action_counts[action_idx] = self._action_counts.get(action_idx, 0) + 1
        self._total_actions += 1

        # Decode to Action
        return self._decode_action(action_idx, legal_actions)

    def reset(self) -> None:
        """Reset episode-specific state."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get action statistics.

        Returns:
            Dict with action counts and totals
        """
        return {
            "action_counts": dict(self._action_counts),
            "total_actions": self._total_actions,
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._action_counts.clear()
        self._total_actions = 0


class RandomAgent(Agent):
    """Simple agent that selects random legal actions.

    Useful as a baseline or for random exploration.
    """

    def __init__(self, name: str = "Random", seed: Optional[int] = None):
        """Initialize random agent.

        Args:
            name: Agent name
            seed: Random seed
        """
        super().__init__(name)
        self._rng = np.random.default_rng(seed)

    def act(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> Action:
        """Select a random legal action.

        Args:
            observation: Unused
            legal_actions: List of legal actions
            info: Unused

        Returns:
            Randomly selected Action
        """
        if not legal_actions:
            raise ValueError("No legal actions available")
        idx = self._rng.integers(0, len(legal_actions))
        return legal_actions[idx]


class ConstantPolicyAgent(RLAgent):
    """Agent with a constant/static policy for testing.

    Wraps a fixed score array as a "policy" for deterministic testing.
    """

    def __init__(
        self,
        scores: np.ndarray,
        name: str = "ConstantPolicy",
        **kwargs,
    ):
        """Initialize with fixed scores.

        Args:
            scores: Fixed score array returned for all observations
            name: Agent name
            **kwargs: Additional RLAgent arguments
        """
        self._fixed_scores = scores

        def constant_policy(obs: np.ndarray, mask: np.ndarray) -> np.ndarray:
            return self._fixed_scores

        super().__init__(policy=constant_policy, name=name, **kwargs)
