"""Tests for extended AI module components."""
import pytest
import numpy as np
import tempfile
from pathlib import Path

from agents import (
    Action,
    ActionKind,
    RandomAgent,
    HeuristicAgent,
    ActionSpaceConfig,
    ActionEncoder,
    ObservationEncoder,
    FeatureExtractor,
)
from ai import (
    BattleEnv,
    EnvConfig,
    Transition,
    Episode,
)
from ai.evaluation import (
    MatchResult,
    EvaluationResult,
    Evaluator,
    PerformanceTracker,
    binomial_test,
    is_significantly_better,
)
from ai.trajectory import (
    TrajectoryConfig,
    TrajectoryExtractor,
    DatasetBuilder,
    choice_to_action,
)
from ai.gym_adapter import (
    GymEnv,
    VectorGymEnv,
    make_gym_env,
)
from core.battle import Choice


class TestActionEncoder:
    """Tests for ActionEncoder."""

    def test_encoder_creation(self):
        """Test encoder creation with default config."""
        encoder = ActionEncoder()
        assert encoder.num_actions > 0

    def test_encoder_custom_config(self):
        """Test encoder with custom config."""
        config = ActionSpaceConfig(
            num_active_slots=1,
            num_moves=4,
            team_size=6,
            include_targets=False,
        )
        encoder = ActionEncoder(config)

        # Singles: 4 moves + 5 switches + 1 pass = 10
        assert encoder.num_actions == 10

    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip."""
        encoder = ActionEncoder()

        # Test move action
        action = Action.move(0, 2)
        idx = encoder.encode(action)
        decoded = encoder.decode(idx)

        assert decoded.kind == action.kind
        assert decoded.slot == action.slot
        assert decoded.arg == action.arg

    def test_action_mask(self):
        """Test action mask generation."""
        encoder = ActionEncoder(ActionSpaceConfig(num_active_slots=1, include_targets=False))

        legal = [
            Action.move(0, 0),
            Action.move(0, 1),
            Action.switch(0, 2),
        ]

        mask = encoder.get_action_mask(legal)

        assert isinstance(mask, np.ndarray)
        assert mask.dtype == bool
        assert mask.sum() == 3

    def test_filter_legal(self):
        """Test filtering legal actions."""
        encoder = ActionEncoder(ActionSpaceConfig(num_active_slots=1, include_targets=False))

        legal = [Action.move(0, i) for i in range(4)]
        indices = encoder.filter_legal(legal)

        assert len(indices) == 4

    def test_sample_legal(self):
        """Test sampling legal actions."""
        encoder = ActionEncoder(ActionSpaceConfig(num_active_slots=1, include_targets=False))
        rng = np.random.default_rng(42)

        legal = [Action.move(0, 0), Action.move(0, 1)]
        idx, action = encoder.sample_legal(legal, rng)

        assert idx in encoder.filter_legal(legal)


class TestObservationEncoder:
    """Tests for ObservationEncoder."""

    def test_flat_encoding(self):
        """Test flat encoding mode."""
        encoder = ObservationEncoder(mode="flat")
        raw = np.array([1, 2, 3, 100, 200], dtype=np.int32)

        encoded = encoder.encode(raw, side=0)

        assert encoded.dtype == np.float32
        assert encoded.shape == raw.shape

    def test_normalized_encoding(self):
        """Test normalized encoding mode."""
        encoder = ObservationEncoder(mode="normalized")
        raw = np.array([0, 1000, 2000, -500], dtype=np.int32)

        encoded = encoder.encode(raw, side=0)

        assert encoded.dtype == np.float32
        # Values should be scaled down
        assert np.all(np.abs(encoded) <= 10)

    def test_structured_encoding(self):
        """Test structured encoding mode."""
        encoder = ObservationEncoder(mode="structured")
        raw = np.array([1, 2, 3])

        encoded = encoder.encode(raw, side=0)

        assert isinstance(encoded, dict)
        assert "raw" in encoded
        assert "normalized" in encoded
        assert "side" in encoded

    def test_space_info(self):
        """Test observation space info."""
        encoder = ObservationEncoder(mode="normalized")
        info = encoder.get_space_info(100)

        assert info["type"] == "box"
        assert info["shape"] == (100,)
        assert info["dtype"] == np.float32


class TestEvaluation:
    """Tests for evaluation module."""

    def test_match_result_creation(self):
        """Test MatchResult creation."""
        result = MatchResult(
            winner=0,
            turns=25,
            total_reward={0: 1.0, 1: -1.0},
            seed=42,
        )

        assert result.winner == 0
        assert result.turns == 25

    def test_evaluation_result_summary(self):
        """Test EvaluationResult summary generation."""
        result = EvaluationResult(
            agent_names=("Agent1", "Agent2"),
            num_matches=100,
            wins=(60, 35),
            draws=5,
            win_rates=(0.6, 0.35),
            avg_turns=30.0,
            avg_rewards=(0.5, -0.3),
            std_rewards=(0.1, 0.15),
        )

        summary = result.summary()

        assert "Agent1" in summary
        assert "Agent2" in summary
        assert "60" in summary  # wins

    def test_evaluator_creation(self):
        """Test Evaluator creation."""
        evaluator = Evaluator(config=EnvConfig(max_turns=10))
        assert evaluator.config.max_turns == 10

    def test_performance_tracker(self):
        """Test PerformanceTracker."""
        tracker = PerformanceTracker()

        tracker.record("agent1", "win_rate", 0.5)
        tracker.record("agent1", "win_rate", 0.55)
        tracker.record("agent1", "win_rate", 0.6)

        latest = tracker.get_latest("agent1", "win_rate")
        assert latest == 0.6

        history = tracker.get_history("agent1", "win_rate")
        assert len(history) == 3

    def test_binomial_test(self):
        """Test binomial test function."""
        # Clear winner
        p_value = binomial_test(80, 20)
        assert p_value < 0.05

        # Close match
        p_value = binomial_test(52, 48)
        assert p_value > 0.05


class TestTrajectory:
    """Tests for trajectory module."""

    def test_choice_to_action_move(self):
        """Test converting move choice to action."""
        choice = Choice(
            choice_type='move',
            slot=0,
            move_slot=2,
            target=1,
        )

        action = choice_to_action(choice, side=0)

        assert action.kind == ActionKind.MOVE
        assert action.slot == 0
        assert action.arg == 2
        assert action.target_side == 1  # Opponent
        assert action.target_slot == 0

    def test_choice_to_action_switch(self):
        """Test converting switch choice to action."""
        choice = Choice(
            choice_type='switch',
            slot=0,
            switch_to=3,
        )

        action = choice_to_action(choice, side=0)

        assert action.kind == ActionKind.SWITCH
        assert action.arg == 3

    def test_choice_to_action_pass(self):
        """Test converting pass choice to action."""
        choice = Choice(
            choice_type='pass',
            slot=1,
        )

        action = choice_to_action(choice, side=0)

        assert action.kind == ActionKind.PASS
        assert action.slot == 1

    def test_trajectory_config(self):
        """Test TrajectoryConfig defaults."""
        config = TrajectoryConfig()

        assert config.reward_mode == "terminal"
        assert config.win_reward == 1.0

    def test_dataset_builder_stats(self):
        """Test DatasetBuilder statistics."""
        builder = DatasetBuilder()

        # Add some episodes manually
        ep = Episode(metadata={"won": True})
        action = Action.move(0, 0)
        ep.add(Transition(np.zeros(10), action, 1.0, np.zeros(10), True))
        builder._episodes.append(ep)
        builder._metadata["num_transitions"] = 1

        stats = builder.get_stats()

        assert stats["num_transitions"] == 1


class TestGymAdapter:
    """Tests for Gym adapter."""

    def test_gym_env_creation(self):
        """Test GymEnv creation."""
        agent1 = RandomAgent(seed=1)
        agent2 = RandomAgent(seed=2)

        battle_env = BattleEnv(
            player_map={0: agent1, 1: agent2},
            config=EnvConfig(max_turns=5),
        )

        gym_env = GymEnv(battle_env, agent_side=0)

        assert gym_env.agent_side == 0
        assert gym_env.observation_space is not None
        assert gym_env.action_space is not None

    def test_gym_env_reset(self):
        """Test GymEnv reset."""
        agent1 = RandomAgent(seed=1)
        agent2 = RandomAgent(seed=2)

        battle_env = BattleEnv(
            player_map={0: agent1, 1: agent2},
        )

        gym_env = GymEnv(battle_env, agent_side=0)
        obs, info = gym_env.reset(seed=42)

        assert isinstance(obs, np.ndarray)
        assert "legal_actions" in info
        assert "legal_action_indices" in info

    def test_gym_env_step(self):
        """Test GymEnv step."""
        agent1 = RandomAgent(seed=1)
        agent2 = RandomAgent(seed=2)

        battle_env = BattleEnv(
            player_map={0: agent1, 1: agent2},
            config=EnvConfig(max_turns=5),
        )

        gym_env = GymEnv(battle_env, agent_side=0)
        obs, info = gym_env.reset(seed=42)

        # Get a legal action
        legal_indices = info["legal_action_indices"]
        if legal_indices:
            action = legal_indices[0]
            next_obs, reward, terminated, truncated, step_info = gym_env.step(action)

            assert isinstance(next_obs, np.ndarray)
            assert isinstance(reward, float)
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)

    def test_make_gym_env_factory(self):
        """Test make_gym_env factory function."""
        opponent = HeuristicAgent()
        config = EnvConfig(max_turns=10)

        env = make_gym_env(opponent, config=config, agent_side=0)

        assert isinstance(env, GymEnv)
        assert env.agent_side == 0

    def test_gym_env_legal_action_mask(self):
        """Test legal action masking."""
        agent1 = RandomAgent()
        agent2 = RandomAgent()

        battle_env = BattleEnv(
            player_map={0: agent1, 1: agent2},
        )

        gym_env = GymEnv(battle_env, agent_side=0)
        _, info = gym_env.reset(seed=42)

        mask = info["legal_actions"]

        assert isinstance(mask, np.ndarray)
        assert mask.dtype == bool
        assert mask.sum() > 0  # At least one legal action

    def test_vector_env_creation(self):
        """Test VectorGymEnv creation."""
        def make_env():
            return BattleEnv(
                player_map={0: RandomAgent(), 1: RandomAgent()},
                config=EnvConfig(max_turns=5),
            )

        vec_env = VectorGymEnv([make_env for _ in range(3)], agent_side=0)

        assert vec_env.num_envs == 3

    def test_vector_env_reset(self):
        """Test VectorGymEnv reset."""
        def make_env():
            return BattleEnv(
                player_map={0: RandomAgent(), 1: RandomAgent()},
            )

        vec_env = VectorGymEnv([make_env for _ in range(2)], agent_side=0)
        obs, infos = vec_env.reset(seed=42)

        assert obs.shape[0] == 2
        assert len(infos) == 2

    def test_vector_env_step(self):
        """Test VectorGymEnv step."""
        def make_env():
            return BattleEnv(
                player_map={0: RandomAgent(), 1: RandomAgent()},
                config=EnvConfig(max_turns=5),
            )

        vec_env = VectorGymEnv([make_env for _ in range(2)], agent_side=0)
        obs, infos = vec_env.reset(seed=42)

        # Take random actions
        actions = np.array([0, 0])
        next_obs, rewards, terminated, truncated, step_infos = vec_env.step(actions)

        assert next_obs.shape[0] == 2
        assert rewards.shape == (2,)
        assert terminated.shape == (2,)
