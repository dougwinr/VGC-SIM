"""AI environment and data management module.

This module provides a generic, library-agnostic layer for:
- Running battles between arbitrary agent types
- Exposing a standard environment step/reset interface
- Logging data for training, evaluation, and offline RL

The module does NOT depend on any specific RL library (Gym, etc.);
adapters can be built externally if needed.

Example usage:
    from ai import BattleEnv, EnvConfig, ReplayBuffer
    from agents import HeuristicAgent, RLAgent

    # Create environment
    config = EnvConfig(reward_mode="shaped")
    env = BattleEnv(
        player_map={0: RLAgent(policy), 1: HeuristicAgent()},
        config=config,
    )

    # Training loop
    buffer = ReplayBuffer(capacity=10000)

    obs = env.reset(seed=42)
    while True:
        action = policy.select_action(obs[0])
        next_obs, rewards, done, info = env.step({0: action})

        buffer.add(Transition(obs[0], action, rewards[0], next_obs[0], done))

        if done:
            break
        obs = next_obs
"""

from .env import (
    BattleEnv,
    EnvConfig,
    SingleAgentEnv,
)

from .replay_buffer import (
    Transition,
    Episode,
    ReplayBuffer,
    EpisodeBuffer,
    TransitionCollector,
)

from .evaluation import (
    MatchResult,
    EvaluationResult,
    Evaluator,
    PerformanceTracker,
    binomial_test,
    is_significantly_better,
)

from .trajectory import (
    TrajectoryConfig,
    TrajectoryExtractor,
    DatasetBuilder,
    choice_to_action,
)

from .gym_adapter import (
    GymEnv,
    VectorGymEnv,
    make_gym_env,
)

__all__ = [
    # Environment
    "BattleEnv",
    "EnvConfig",
    "SingleAgentEnv",
    # Data
    "Transition",
    "Episode",
    "ReplayBuffer",
    "EpisodeBuffer",
    "TransitionCollector",
    # Evaluation
    "MatchResult",
    "EvaluationResult",
    "Evaluator",
    "PerformanceTracker",
    "binomial_test",
    "is_significantly_better",
    # Trajectory / Offline RL
    "TrajectoryConfig",
    "TrajectoryExtractor",
    "DatasetBuilder",
    "choice_to_action",
    # Gym Adapter
    "GymEnv",
    "VectorGymEnv",
    "make_gym_env",
]
