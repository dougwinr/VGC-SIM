"""Pokemon battle agents module.

This module provides a unified agent interface for Pokemon battles with
four concrete agent types:

- HumanAgent: Interactive agent for human players (CLI/GUI/web)
- RLAgent: Reinforcement learning policy wrapper
- LLMAgent: Large language model based decision making
- HeuristicAgent: Hand-coded rules and scoring functions

All agents implement the same interface and can be freely composed
in battle environments.

Example usage:
    from agents import Agent, Action, HeuristicAgent, RLAgent

    # Create agents
    agent1 = HeuristicAgent(name="Bot1")
    agent2 = RLAgent(policy=my_policy, name="RL")

    # Use in environment
    env = BattleEnv(player_map={0: agent1, 1: agent2})
"""

from .base import (
    Agent,
    Action,
    ActionKind,
)

from .human_agent import (
    HumanAgent,
    AsyncHumanAgent,
)

from .rl_agent import (
    RLAgent,
    RandomAgent,
    ConstantPolicyAgent,
)

from .llm_agent import (
    LLMAgent,
    MockLLMAgent,
)

from .heuristic_agent import (
    HeuristicAgent,
    TypeMatchupAgent,
    MaxDamageAgent,
    DefensiveAgent,
    CompositeAgent,
)

from .encoding import (
    ActionSpaceConfig,
    ActionEncoder,
    ObservationEncoder,
    FeatureExtractor,
)

__all__ = [
    # Base
    "Agent",
    "Action",
    "ActionKind",
    # Human
    "HumanAgent",
    "AsyncHumanAgent",
    # RL
    "RLAgent",
    "RandomAgent",
    "ConstantPolicyAgent",
    # LLM
    "LLMAgent",
    "MockLLMAgent",
    # Heuristic
    "HeuristicAgent",
    "TypeMatchupAgent",
    "MaxDamageAgent",
    "DefensiveAgent",
    "CompositeAgent",
    # Encoding
    "ActionSpaceConfig",
    "ActionEncoder",
    "ObservationEncoder",
    "FeatureExtractor",
]
