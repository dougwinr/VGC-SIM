"""Replay buffer and transition storage for RL training.

This module provides data structures for storing and sampling transitions,
supporting both online and offline RL workflows.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union
import json
import pickle
from pathlib import Path
import numpy as np

from agents.base import Action, ActionKind


@dataclass
class Transition:
    """A single transition in an RL trajectory.

    Stores all information needed for RL training from one step.

    Attributes:
        obs: Observation at time t
        action: Action taken
        reward: Reward received
        next_obs: Observation at time t+1
        done: Whether episode ended
        info: Additional metadata (agent type, LLM reasoning, etc.)
    """
    obs: Any
    action: Action
    reward: float
    next_obs: Any
    done: bool
    info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dict representation
        """
        obs_data = self.obs.tolist() if isinstance(self.obs, np.ndarray) else self.obs
        next_obs_data = self.next_obs.tolist() if isinstance(self.next_obs, np.ndarray) else self.next_obs

        return {
            "obs": obs_data,
            "action": {
                "kind": int(self.action.kind),
                "slot": self.action.slot,
                "arg": self.action.arg,
                "target_side": self.action.target_side,
                "target_slot": self.action.target_slot,
            },
            "reward": self.reward,
            "next_obs": next_obs_data,
            "done": self.done,
            "info": self.info,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Transition":
        """Create from dictionary.

        Args:
            d: Dict representation

        Returns:
            Transition object
        """
        action_data = d["action"]
        action = Action(
            kind=action_data["kind"],
            slot=action_data["slot"],
            arg=action_data.get("arg", 0),
            target_side=action_data.get("target_side", -1),
            target_slot=action_data.get("target_slot", -1),
        )

        obs = np.array(d["obs"]) if isinstance(d["obs"], list) else d["obs"]
        next_obs = np.array(d["next_obs"]) if isinstance(d["next_obs"], list) else d["next_obs"]

        return cls(
            obs=obs,
            action=action,
            reward=d["reward"],
            next_obs=next_obs,
            done=d["done"],
            info=d.get("info", {}),
        )


@dataclass
class Episode:
    """A complete episode (battle) as a sequence of transitions.

    Attributes:
        transitions: List of transitions in order
        metadata: Episode metadata (seed, agents, winner, etc.)
    """
    transitions: List[Transition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.transitions)

    def __iter__(self) -> Iterator[Transition]:
        return iter(self.transitions)

    def add(self, transition: Transition) -> None:
        """Add a transition to the episode."""
        self.transitions.append(transition)

    def get_returns(self, gamma: float = 0.99) -> List[float]:
        """Compute discounted returns for each timestep.

        Args:
            gamma: Discount factor

        Returns:
            List of returns (from each timestep to end)
        """
        returns = []
        running_return = 0.0

        for t in reversed(self.transitions):
            running_return = t.reward + gamma * running_return
            returns.append(running_return)

        returns.reverse()
        return returns

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "transitions": [t.to_dict() for t in self.transitions],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Episode":
        """Create from dictionary."""
        return cls(
            transitions=[Transition.from_dict(t) for t in d["transitions"]],
            metadata=d.get("metadata", {}),
        )


class ReplayBuffer:
    """Circular replay buffer for storing transitions.

    Supports:
    - Fixed capacity with FIFO replacement
    - Random sampling for training
    - Priority-based sampling (optional)
    - Persistence to disk

    Thread-safety note: This implementation is NOT thread-safe.
    For multi-threaded training, use appropriate synchronization.
    """

    def __init__(
        self,
        capacity: int,
        seed: Optional[int] = None,
    ):
        """Initialize replay buffer.

        Args:
            capacity: Maximum number of transitions to store
            seed: Random seed for sampling
        """
        self.capacity = capacity
        self.storage: List[Transition] = []
        self.position = 0
        self._rng = np.random.default_rng(seed)

        # Statistics
        self._total_added = 0

    def __len__(self) -> int:
        return len(self.storage)

    def add(self, transition: Transition) -> None:
        """Add a transition to the buffer.

        If buffer is full, overwrites oldest transition.

        Args:
            transition: Transition to add
        """
        if len(self.storage) < self.capacity:
            self.storage.append(transition)
        else:
            self.storage[self.position] = transition

        self.position = (self.position + 1) % self.capacity
        self._total_added += 1

    def add_batch(self, transitions: Sequence[Transition]) -> None:
        """Add multiple transitions.

        Args:
            transitions: Sequence of transitions to add
        """
        for t in transitions:
            self.add(t)

    def add_episode(self, episode: Episode) -> None:
        """Add all transitions from an episode.

        Args:
            episode: Episode to add
        """
        for t in episode.transitions:
            self.add(t)

    def sample(self, batch_size: int) -> List[Transition]:
        """Sample a random batch of transitions.

        Args:
            batch_size: Number of transitions to sample

        Returns:
            List of sampled transitions
        """
        if len(self.storage) == 0:
            return []

        batch_size = min(batch_size, len(self.storage))
        indices = self._rng.choice(len(self.storage), size=batch_size, replace=False)
        return [self.storage[i] for i in indices]

    def sample_with_indices(
        self,
        batch_size: int,
    ) -> Tuple[List[Transition], np.ndarray]:
        """Sample transitions and return their indices.

        Useful for priority updates in prioritized experience replay.

        Args:
            batch_size: Number of transitions to sample

        Returns:
            Tuple of (transitions, indices)
        """
        if len(self.storage) == 0:
            return [], np.array([])

        batch_size = min(batch_size, len(self.storage))
        indices = self._rng.choice(len(self.storage), size=batch_size, replace=False)
        transitions = [self.storage[i] for i in indices]
        return transitions, indices

    def get_batch_arrays(
        self,
        batch_size: int,
    ) -> Dict[str, np.ndarray]:
        """Sample batch and return as numpy arrays.

        Convenience method for training loops that expect numpy arrays.

        Args:
            batch_size: Number of transitions to sample

        Returns:
            Dict with 'obs', 'actions', 'rewards', 'next_obs', 'dones' arrays
        """
        transitions = self.sample(batch_size)

        if not transitions:
            return {}

        # Stack observations
        obs = np.stack([t.obs for t in transitions])
        next_obs = np.stack([t.next_obs for t in transitions])

        # Pack actions as integers
        actions = np.array([
            t.action.kind * 100 + t.action.slot * 10 + t.action.arg
            for t in transitions
        ])

        rewards = np.array([t.reward for t in transitions])
        dones = np.array([t.done for t in transitions])

        return {
            "obs": obs,
            "actions": actions,
            "rewards": rewards,
            "next_obs": next_obs,
            "dones": dones,
        }

    def clear(self) -> None:
        """Clear all transitions from the buffer."""
        self.storage.clear()
        self.position = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics.

        Returns:
            Dict with size, capacity, total_added
        """
        return {
            "size": len(self.storage),
            "capacity": self.capacity,
            "total_added": self._total_added,
            "utilization": len(self.storage) / self.capacity if self.capacity > 0 else 0,
        }

    def save(self, path: Union[str, Path], format: str = "pickle") -> None:
        """Save buffer to disk.

        Args:
            path: File path
            format: "pickle", "json", or "npz"
        """
        path = Path(path)

        if format == "pickle":
            with open(path, 'wb') as f:
                pickle.dump({
                    "storage": self.storage,
                    "position": self.position,
                    "capacity": self.capacity,
                    "total_added": self._total_added,
                }, f)

        elif format == "json":
            data = {
                "transitions": [t.to_dict() for t in self.storage],
                "position": self.position,
                "capacity": self.capacity,
                "total_added": self._total_added,
            }
            with open(path, 'w') as f:
                json.dump(data, f)

        elif format == "npz":
            if not self.storage:
                np.savez(path, empty=True)
                return

            # Convert to arrays
            obs = np.stack([t.obs for t in self.storage])
            next_obs = np.stack([t.next_obs for t in self.storage])
            actions = np.array([
                [t.action.kind, t.action.slot, t.action.arg,
                 t.action.target_side, t.action.target_slot]
                for t in self.storage
            ])
            rewards = np.array([t.reward for t in self.storage])
            dones = np.array([t.done for t in self.storage])

            np.savez(
                path,
                obs=obs,
                next_obs=next_obs,
                actions=actions,
                rewards=rewards,
                dones=dones,
                position=self.position,
                capacity=self.capacity,
                total_added=self._total_added,
            )

        else:
            raise ValueError(f"Unknown format: {format}")

    @classmethod
    def load(cls, path: Union[str, Path], format: str = "pickle") -> "ReplayBuffer":
        """Load buffer from disk.

        Args:
            path: File path
            format: "pickle", "json", or "npz"

        Returns:
            Loaded ReplayBuffer
        """
        path = Path(path)

        if format == "pickle":
            with open(path, 'rb') as f:
                data = pickle.load(f)

            buffer = cls(capacity=data["capacity"])
            buffer.storage = data["storage"]
            buffer.position = data["position"]
            buffer._total_added = data["total_added"]
            return buffer

        elif format == "json":
            with open(path, 'r') as f:
                data = json.load(f)

            buffer = cls(capacity=data["capacity"])
            buffer.storage = [Transition.from_dict(t) for t in data["transitions"]]
            buffer.position = data["position"]
            buffer._total_added = data["total_added"]
            return buffer

        elif format == "npz":
            data = np.load(path)

            if "empty" in data:
                return cls(capacity=1000)

            buffer = cls(capacity=int(data["capacity"]))

            obs = data["obs"]
            next_obs = data["next_obs"]
            actions = data["actions"]
            rewards = data["rewards"]
            dones = data["dones"]

            for i in range(len(obs)):
                action = Action(
                    kind=int(actions[i, 0]),
                    slot=int(actions[i, 1]),
                    arg=int(actions[i, 2]),
                    target_side=int(actions[i, 3]),
                    target_slot=int(actions[i, 4]),
                )
                buffer.storage.append(Transition(
                    obs=obs[i],
                    action=action,
                    reward=float(rewards[i]),
                    next_obs=next_obs[i],
                    done=bool(dones[i]),
                ))

            buffer.position = int(data["position"])
            buffer._total_added = int(data["total_added"])
            return buffer

        else:
            raise ValueError(f"Unknown format: {format}")


class EpisodeBuffer:
    """Buffer that stores complete episodes.

    Useful for:
    - Monte Carlo methods that need full episodes
    - Offline RL datasets
    - Analysis of complete games
    """

    def __init__(
        self,
        capacity: int,
        seed: Optional[int] = None,
    ):
        """Initialize episode buffer.

        Args:
            capacity: Maximum number of episodes to store
            seed: Random seed
        """
        self.capacity = capacity
        self.episodes: List[Episode] = []
        self._rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.episodes)

    def add(self, episode: Episode) -> None:
        """Add an episode to the buffer.

        Args:
            episode: Episode to add
        """
        if len(self.episodes) >= self.capacity:
            # Remove oldest
            self.episodes.pop(0)
        self.episodes.append(episode)

    def sample_episodes(self, n: int) -> List[Episode]:
        """Sample random episodes.

        Args:
            n: Number of episodes to sample

        Returns:
            List of sampled episodes
        """
        n = min(n, len(self.episodes))
        indices = self._rng.choice(len(self.episodes), size=n, replace=False)
        return [self.episodes[i] for i in indices]

    def sample_transitions(self, batch_size: int) -> List[Transition]:
        """Sample random transitions from all episodes.

        Args:
            batch_size: Number of transitions to sample

        Returns:
            List of sampled transitions
        """
        # Flatten all transitions
        all_transitions = []
        for ep in self.episodes:
            all_transitions.extend(ep.transitions)

        if not all_transitions:
            return []

        batch_size = min(batch_size, len(all_transitions))
        indices = self._rng.choice(len(all_transitions), size=batch_size, replace=False)
        return [all_transitions[i] for i in indices]

    def get_all_transitions(self) -> List[Transition]:
        """Get all transitions from all episodes.

        Returns:
            Flattened list of all transitions
        """
        all_transitions = []
        for ep in self.episodes:
            all_transitions.extend(ep.transitions)
        return all_transitions

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics.

        Returns:
            Dict with episode and transition counts
        """
        total_transitions = sum(len(ep) for ep in self.episodes)
        avg_length = total_transitions / len(self.episodes) if self.episodes else 0

        return {
            "num_episodes": len(self.episodes),
            "capacity": self.capacity,
            "total_transitions": total_transitions,
            "avg_episode_length": avg_length,
        }

    def filter_by_outcome(self, winner: int) -> List[Episode]:
        """Get episodes with specific winner.

        Args:
            winner: Winner side to filter by

        Returns:
            List of matching episodes
        """
        return [
            ep for ep in self.episodes
            if ep.metadata.get("winner") == winner
        ]

    def filter_by_agent(self, agent_type: str) -> List[Episode]:
        """Get episodes involving specific agent type.

        Args:
            agent_type: Agent type string to filter by

        Returns:
            List of matching episodes
        """
        return [
            ep for ep in self.episodes
            if agent_type in ep.metadata.get("agents", [])
        ]

    def save(self, path: Union[str, Path]) -> None:
        """Save to disk.

        Args:
            path: File path
        """
        path = Path(path)
        data = {
            "episodes": [ep.to_dict() for ep in self.episodes],
            "capacity": self.capacity,
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "EpisodeBuffer":
        """Load from disk.

        Args:
            path: File path

        Returns:
            Loaded EpisodeBuffer
        """
        path = Path(path)
        with open(path, 'rb') as f:
            data = pickle.load(f)

        buffer = cls(capacity=data["capacity"])
        buffer.episodes = [Episode.from_dict(ep) for ep in data["episodes"]]
        return buffer


class TransitionCollector:
    """Helper class for collecting transitions during environment interaction.

    Handles the bookkeeping of storing observations, actions, and computing
    transitions with proper next_obs and done values.
    """

    def __init__(
        self,
        buffer: Optional[ReplayBuffer] = None,
        episode_buffer: Optional[EpisodeBuffer] = None,
    ):
        """Initialize collector.

        Args:
            buffer: ReplayBuffer to add transitions to
            episode_buffer: EpisodeBuffer to add episodes to
        """
        self.buffer = buffer
        self.episode_buffer = episode_buffer

        self._current_episode = Episode()
        self._last_obs: Optional[Any] = None
        self._last_action: Optional[Action] = None
        self._last_info: Dict[str, Any] = {}

    def start_episode(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Start a new episode.

        Args:
            metadata: Episode metadata
        """
        self._current_episode = Episode(metadata=metadata or {})
        self._last_obs = None
        self._last_action = None
        self._last_info = {}

    def record_step(
        self,
        obs: Any,
        action: Action,
        reward: float,
        done: bool,
        info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a step.

        Args:
            obs: Current observation (before action)
            action: Action taken
            reward: Reward received
            done: Whether episode ended
            info: Additional info
        """
        if self._last_obs is not None:
            # Create transition from last step to this one
            transition = Transition(
                obs=self._last_obs,
                action=self._last_action,
                reward=reward,
                next_obs=obs,
                done=done,
                info=self._last_info,
            )

            self._current_episode.add(transition)

            if self.buffer is not None:
                self.buffer.add(transition)

        self._last_obs = obs
        self._last_action = action
        self._last_info = info or {}

        if done:
            self.end_episode()

    def end_episode(self, metadata: Optional[Dict[str, Any]] = None) -> Episode:
        """End the current episode.

        Args:
            metadata: Additional metadata to merge

        Returns:
            The completed Episode
        """
        if metadata:
            self._current_episode.metadata.update(metadata)

        if self.episode_buffer is not None:
            self.episode_buffer.add(self._current_episode)

        episode = self._current_episode
        self._current_episode = Episode()
        self._last_obs = None
        self._last_action = None
        self._last_info = {}

        return episode

    def get_current_episode(self) -> Episode:
        """Get the current in-progress episode.

        Returns:
            Current Episode
        """
        return self._current_episode
