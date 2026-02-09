"""Tests for the agents module."""
import pytest
import numpy as np

from agents import (
    Agent,
    Action,
    ActionKind,
    HumanAgent,
    RLAgent,
    RandomAgent,
    LLMAgent,
    MockLLMAgent,
    HeuristicAgent,
    TypeMatchupAgent,
    MaxDamageAgent,
    DefensiveAgent,
    CompositeAgent,
)


class TestAction:
    """Tests for the Action dataclass."""

    def test_action_creation(self):
        """Test basic action creation."""
        action = Action(kind=ActionKind.MOVE, slot=0, arg=1)
        assert action.kind == ActionKind.MOVE
        assert action.slot == 0
        assert action.arg == 1
        assert action.target_side == -1
        assert action.target_slot == -1

    def test_action_frozen(self):
        """Test that Action is immutable."""
        action = Action(kind=ActionKind.MOVE, slot=0)
        with pytest.raises(AttributeError):
            action.slot = 1

    def test_move_factory(self):
        """Test Action.move() factory method."""
        action = Action.move(slot=0, move_slot=2, target_side=1, target_slot=0)
        assert action.kind == ActionKind.MOVE
        assert action.slot == 0
        assert action.arg == 2
        assert action.target_side == 1
        assert action.target_slot == 0

    def test_switch_factory(self):
        """Test Action.switch() factory method."""
        action = Action.switch(slot=0, switch_to=3)
        assert action.kind == ActionKind.SWITCH
        assert action.slot == 0
        assert action.arg == 3

    def test_pass_factory(self):
        """Test Action.pass_action() factory method."""
        action = Action.pass_action(slot=1)
        assert action.kind == ActionKind.PASS
        assert action.slot == 1


class TestRandomAgent:
    """Tests for RandomAgent."""

    def test_random_agent_creation(self):
        """Test RandomAgent creation."""
        agent = RandomAgent(name="TestRandom", seed=42)
        assert agent.name == "TestRandom"

    def test_random_agent_act(self):
        """Test RandomAgent action selection."""
        agent = RandomAgent(seed=42)
        legal_actions = [
            Action.move(0, 0),
            Action.move(0, 1),
            Action.switch(0, 2),
        ]

        action = agent.act(
            observation=np.zeros(10),
            legal_actions=legal_actions,
        )

        assert action in legal_actions

    def test_random_agent_deterministic_with_seed(self):
        """Test that seeded RandomAgent is deterministic."""
        agent1 = RandomAgent(seed=42)
        agent2 = RandomAgent(seed=42)

        legal_actions = [Action.move(0, i) for i in range(4)]

        actions1 = [agent1.act(None, legal_actions) for _ in range(10)]
        actions2 = [agent2.act(None, legal_actions) for _ in range(10)]

        assert actions1 == actions2

    def test_random_agent_raises_on_empty_actions(self):
        """Test that RandomAgent raises with no legal actions."""
        agent = RandomAgent()
        with pytest.raises(ValueError, match="No legal actions"):
            agent.act(None, [])


class TestRLAgent:
    """Tests for RLAgent."""

    def test_rl_agent_creation(self):
        """Test RLAgent creation."""
        def dummy_policy(obs, mask):
            return np.random.randn(len(mask))

        agent = RLAgent(policy=dummy_policy, name="TestRL")
        assert agent.name == "TestRL"

    def test_rl_agent_argmax_selection(self):
        """Test RLAgent with argmax selection."""
        # Policy that returns fixed scores
        def policy(obs, mask):
            return np.array([1.0, 3.0, 2.0, 0.5])

        agent = RLAgent(
            policy=policy,
            action_space_size=4,
            selection_mode="argmax",
        )

        legal_actions = [Action.move(0, i) for i in range(4)]
        action = agent.act(np.zeros(10), legal_actions)

        # Should select action with highest score (index 1)
        assert action == legal_actions[1]

    def test_rl_agent_epsilon_greedy(self):
        """Test RLAgent with epsilon-greedy selection."""
        def policy(obs, mask):
            return np.array([0.0, 10.0])  # Strongly prefer index 1

        agent = RLAgent(
            policy=policy,
            action_space_size=2,
            selection_mode="epsilon_greedy",
            epsilon=1.0,  # Always explore
            seed=42,
        )

        legal_actions = [Action.move(0, 0), Action.move(0, 1)]

        # With epsilon=1.0, should sometimes pick index 0
        actions = [agent.act(np.zeros(10), legal_actions) for _ in range(100)]
        action_0_count = sum(1 for a in actions if a == legal_actions[0])

        # Should have both actions represented
        assert action_0_count > 0
        assert action_0_count < 100

    def test_rl_agent_stats_tracking(self):
        """Test RLAgent statistics tracking."""
        def policy(obs, mask):
            return np.ones(4)

        agent = RLAgent(policy=policy, action_space_size=4, seed=42)
        legal_actions = [Action.move(0, i) for i in range(4)]

        for _ in range(10):
            agent.act(np.zeros(10), legal_actions)

        stats = agent.get_stats()
        assert stats["total_actions"] == 10
        assert sum(stats["action_counts"].values()) == 10


class TestHeuristicAgent:
    """Tests for HeuristicAgent."""

    def test_heuristic_agent_creation(self):
        """Test HeuristicAgent creation."""
        agent = HeuristicAgent(name="TestHeuristic")
        assert agent.name == "TestHeuristic"

    def test_heuristic_agent_custom_scoring(self):
        """Test HeuristicAgent with custom scoring function."""
        # Score function that prefers switches
        def score_func(action, obs, info):
            return 2.0 if action.kind == ActionKind.SWITCH else 1.0

        agent = HeuristicAgent(score_func=score_func)

        legal_actions = [
            Action.move(0, 0),
            Action.move(0, 1),
            Action.switch(0, 2),
        ]

        action = agent.act(None, legal_actions, {})
        assert action.kind == ActionKind.SWITCH

    def test_heuristic_agent_tie_breaking(self):
        """Test HeuristicAgent tie-breaking modes."""
        # All actions have same score
        def score_func(action, obs, info):
            return 1.0

        agent_first = HeuristicAgent(score_func=score_func, tie_break="first")
        agent_last = HeuristicAgent(score_func=score_func, tie_break="last")

        legal_actions = [Action.move(0, i) for i in range(4)]

        action_first = agent_first.act(None, legal_actions, {})
        action_last = agent_last.act(None, legal_actions, {})

        assert action_first == legal_actions[0]
        assert action_last == legal_actions[-1]


class TestTypeMatchupAgent:
    """Tests for TypeMatchupAgent."""

    def test_type_matchup_agent_creation(self):
        """Test TypeMatchupAgent creation."""
        agent = TypeMatchupAgent()
        assert agent.name == "TypeMatchup"

    def test_type_effectiveness_calculation(self):
        """Test type effectiveness calculation."""
        agent = TypeMatchupAgent()

        # Fire vs Grass = 2x
        eff = agent._get_type_effectiveness("fire", "grass")
        assert eff == 2.0

        # Electric vs Ground = 0x
        eff = agent._get_type_effectiveness("electric", "ground")
        assert eff == 0.0

        # Normal vs Normal = 1x
        eff = agent._get_type_effectiveness("normal", "normal")
        assert eff == 1.0

        # Water vs Fire/Ground = 4x (2x * 2x)
        eff = agent._get_type_effectiveness("water", "fire", "ground")
        assert eff == 4.0

        # Fire vs Water/Rock = 0.25x
        eff = agent._get_type_effectiveness("fire", "water", "rock")
        assert eff == 0.25


class TestMockLLMAgent:
    """Tests for MockLLMAgent."""

    def test_mock_llm_agent_creation(self):
        """Test MockLLMAgent creation."""
        agent = MockLLMAgent(
            responses=["ACTION: 0\nREASONING: Test"],
            name="TestLLM",
        )
        assert agent.name == "TestLLM"

    def test_mock_llm_agent_cycles_responses(self):
        """Test that MockLLMAgent cycles through responses."""
        responses = [
            "ACTION: 0\nREASONING: First",
            "ACTION: 1\nREASONING: Second",
        ]
        agent = MockLLMAgent(responses=responses)

        legal_actions = [Action.move(0, 0), Action.move(0, 1)]

        action1 = agent.act(None, legal_actions, {})
        action2 = agent.act(None, legal_actions, {})
        action3 = agent.act(None, legal_actions, {})  # Should cycle back

        assert action1 == legal_actions[0]
        assert action2 == legal_actions[1]
        assert action3 == legal_actions[0]

    def test_mock_llm_agent_stores_reasoning(self):
        """Test that MockLLMAgent stores reasoning."""
        agent = MockLLMAgent(
            responses=["ACTION: 0\nREASONING: My reasoning here"],
        )

        legal_actions = [Action.move(0, 0)]
        agent.act(None, legal_actions, {})

        reasoning = agent.get_last_reasoning()
        assert "reasoning here" in reasoning.lower()


class TestCompositeAgent:
    """Tests for CompositeAgent."""

    def test_composite_agent_creation(self):
        """Test CompositeAgent creation."""
        sub1 = HeuristicAgent()
        sub2 = TypeMatchupAgent()

        agent = CompositeAgent(
            agents=[(sub1, 1.0), (sub2, 1.0)],
            name="Composite",
        )

        assert agent.name == "Composite"

    def test_composite_agent_weighted_scoring(self):
        """Test CompositeAgent combines scores correctly."""
        # Agent that scores 1.0 for all actions
        agent1 = HeuristicAgent(score_func=lambda a, o, i: 1.0)
        # Agent that scores 2.0 for all actions
        agent2 = HeuristicAgent(score_func=lambda a, o, i: 2.0)

        composite = CompositeAgent(
            agents=[(agent1, 1.0), (agent2, 1.0)],
        )

        action = Action.move(0, 0)
        score = composite.score_action(action, None, {})

        # Average: (1.0 * 1.0 + 2.0 * 1.0) / 2.0 = 1.5
        assert score == 1.5


class TestHumanAgent:
    """Tests for HumanAgent."""

    def test_human_agent_creation(self):
        """Test HumanAgent creation."""
        agent = HumanAgent(name="Human")
        assert agent.name == "Human"

    def test_human_agent_with_custom_io(self):
        """Test HumanAgent with custom I/O functions."""
        displayed = []
        input_response = "0"

        def display(text):
            displayed.append(text)

        def get_input(prompt):
            return input_response

        agent = HumanAgent(
            display_func=display,
            input_func=get_input,
        )

        legal_actions = [Action.move(0, 0), Action.move(0, 1)]
        action = agent.act({}, legal_actions, {})

        # Should have displayed something
        assert len(displayed) > 0
        # Should return first action based on input "0"
        assert action == legal_actions[0]
