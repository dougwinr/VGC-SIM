"""Tests for the ai module."""
import pytest
import numpy as np
import tempfile
from pathlib import Path

from agents import Action, ActionKind, RandomAgent, HeuristicAgent
from ai import (
    BattleEnv,
    EnvConfig,
    SingleAgentEnv,
    Transition,
    Episode,
    ReplayBuffer,
    EpisodeBuffer,
    TransitionCollector,
)


class TestTransition:
    """Tests for the Transition dataclass."""

    def test_transition_creation(self):
        """Test basic transition creation."""
        action = Action.move(0, 1)
        t = Transition(
            obs=np.array([1, 2, 3]),
            action=action,
            reward=1.0,
            next_obs=np.array([4, 5, 6]),
            done=False,
        )

        assert t.reward == 1.0
        assert not t.done
        assert t.action == action

    def test_transition_serialization(self):
        """Test transition to/from dict."""
        action = Action.move(0, 2, target_side=1, target_slot=0)
        t = Transition(
            obs=np.array([1.0, 2.0]),
            action=action,
            reward=0.5,
            next_obs=np.array([3.0, 4.0]),
            done=True,
            info={"side": 0, "turn": 5},
        )

        d = t.to_dict()
        t2 = Transition.from_dict(d)

        assert np.allclose(t2.obs, t.obs)
        assert t2.action.kind == t.action.kind
        assert t2.action.arg == t.action.arg
        assert t2.reward == t.reward
        assert t2.done == t.done
        assert t2.info == t.info


class TestEpisode:
    """Tests for the Episode class."""

    def test_episode_creation(self):
        """Test episode creation and addition."""
        ep = Episode(metadata={"seed": 42})

        action = Action.move(0, 0)
        t1 = Transition(np.zeros(3), action, 0.1, np.zeros(3), False)
        t2 = Transition(np.zeros(3), action, 0.2, np.zeros(3), True)

        ep.add(t1)
        ep.add(t2)

        assert len(ep) == 2
        assert ep.metadata["seed"] == 42

    def test_episode_returns_calculation(self):
        """Test discounted returns calculation."""
        ep = Episode()

        action = Action.move(0, 0)
        # Rewards: [1, 2, 3]
        ep.add(Transition(np.zeros(1), action, 1.0, np.zeros(1), False))
        ep.add(Transition(np.zeros(1), action, 2.0, np.zeros(1), False))
        ep.add(Transition(np.zeros(1), action, 3.0, np.zeros(1), True))

        # With gamma=1.0, returns should be [6, 5, 3]
        returns = ep.get_returns(gamma=1.0)
        assert returns == [6.0, 5.0, 3.0]

        # With gamma=0.5
        # R_2 = 3
        # R_1 = 2 + 0.5 * 3 = 3.5
        # R_0 = 1 + 0.5 * 3.5 = 2.75
        returns = ep.get_returns(gamma=0.5)
        assert np.isclose(returns[2], 3.0)
        assert np.isclose(returns[1], 3.5)
        assert np.isclose(returns[0], 2.75)

    def test_episode_iteration(self):
        """Test episode iteration."""
        ep = Episode()
        action = Action.move(0, 0)

        for i in range(5):
            ep.add(Transition(np.array([i]), action, float(i), np.array([i+1]), False))

        count = 0
        for t in ep:
            count += 1
        assert count == 5

    def test_episode_serialization(self):
        """Test episode to/from dict."""
        ep = Episode(metadata={"winner": 0})
        action = Action.switch(0, 2)
        ep.add(Transition(np.array([1.0]), action, 1.0, np.array([2.0]), True))

        d = ep.to_dict()
        ep2 = Episode.from_dict(d)

        assert len(ep2) == 1
        assert ep2.metadata["winner"] == 0


class TestReplayBuffer:
    """Tests for ReplayBuffer."""

    def test_buffer_creation(self):
        """Test replay buffer creation."""
        buffer = ReplayBuffer(capacity=100)
        assert len(buffer) == 0
        assert buffer.capacity == 100

    def test_buffer_add_and_sample(self):
        """Test adding and sampling from buffer."""
        buffer = ReplayBuffer(capacity=100, seed=42)

        action = Action.move(0, 0)
        for i in range(50):
            t = Transition(
                obs=np.array([i]),
                action=action,
                reward=float(i),
                next_obs=np.array([i+1]),
                done=False,
            )
            buffer.add(t)

        assert len(buffer) == 50

        # Sample batch
        batch = buffer.sample(10)
        assert len(batch) == 10

        # All samples should be from buffer
        rewards = [t.reward for t in batch]
        assert all(0 <= r < 50 for r in rewards)

    def test_buffer_circular_overwrite(self):
        """Test circular buffer behavior."""
        buffer = ReplayBuffer(capacity=5)

        action = Action.move(0, 0)
        for i in range(10):
            buffer.add(Transition(
                obs=np.array([i]),
                action=action,
                reward=float(i),
                next_obs=np.array([i+1]),
                done=False,
            ))

        assert len(buffer) == 5

        # Should only have rewards 5-9 (last 5)
        rewards = sorted([t.reward for t in buffer.storage])
        assert rewards == [5.0, 6.0, 7.0, 8.0, 9.0]

    def test_buffer_get_batch_arrays(self):
        """Test getting batch as numpy arrays."""
        buffer = ReplayBuffer(capacity=100, seed=42)

        action = Action.move(0, 1)
        for i in range(20):
            buffer.add(Transition(
                obs=np.array([1.0, 2.0]),
                action=action,
                reward=float(i),
                next_obs=np.array([3.0, 4.0]),
                done=False,
            ))

        batch = buffer.get_batch_arrays(batch_size=10)

        assert "obs" in batch
        assert batch["obs"].shape == (10, 2)
        assert batch["rewards"].shape == (10,)
        assert batch["dones"].shape == (10,)

    def test_buffer_stats(self):
        """Test buffer statistics."""
        buffer = ReplayBuffer(capacity=100)

        action = Action.move(0, 0)
        for i in range(30):
            buffer.add(Transition(
                obs=np.zeros(1), action=action,
                reward=0.0, next_obs=np.zeros(1), done=False
            ))

        stats = buffer.get_stats()
        assert stats["size"] == 30
        assert stats["capacity"] == 100
        assert stats["total_added"] == 30
        assert stats["utilization"] == 0.3

    def test_buffer_save_load_pickle(self):
        """Test buffer persistence with pickle."""
        buffer = ReplayBuffer(capacity=50, seed=42)

        action = Action.move(0, 0)
        for i in range(20):
            buffer.add(Transition(
                obs=np.array([float(i)]),
                action=action,
                reward=float(i),
                next_obs=np.array([float(i+1)]),
                done=False,
            ))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "buffer.pkl"
            buffer.save(path, format="pickle")

            loaded = ReplayBuffer.load(path, format="pickle")

        assert len(loaded) == 20
        assert loaded.capacity == 50

    def test_buffer_save_load_json(self):
        """Test buffer persistence with JSON."""
        buffer = ReplayBuffer(capacity=50)

        action = Action.switch(0, 2)
        for i in range(5):
            buffer.add(Transition(
                obs=np.array([1.0, 2.0]),
                action=action,
                reward=float(i),
                next_obs=np.array([3.0, 4.0]),
                done=i == 4,
            ))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "buffer.json"
            buffer.save(path, format="json")
            loaded = ReplayBuffer.load(path, format="json")

        assert len(loaded) == 5

    def test_buffer_save_load_npz(self):
        """Test buffer persistence with npz."""
        buffer = ReplayBuffer(capacity=50)

        action = Action.move(0, 1, target_side=1, target_slot=0)
        for i in range(10):
            buffer.add(Transition(
                obs=np.array([float(i), float(i+1)]),
                action=action,
                reward=float(i) * 0.1,
                next_obs=np.array([float(i+1), float(i+2)]),
                done=False,
            ))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "buffer.npz"
            buffer.save(path, format="npz")
            loaded = ReplayBuffer.load(path, format="npz")

        assert len(loaded) == 10


class TestEpisodeBuffer:
    """Tests for EpisodeBuffer."""

    def test_episode_buffer_creation(self):
        """Test episode buffer creation."""
        buffer = EpisodeBuffer(capacity=10)
        assert len(buffer) == 0

    def test_episode_buffer_add_and_sample(self):
        """Test adding and sampling episodes."""
        buffer = EpisodeBuffer(capacity=10, seed=42)

        action = Action.move(0, 0)
        for i in range(5):
            ep = Episode(metadata={"id": i})
            for j in range(3):
                ep.add(Transition(
                    obs=np.zeros(2),
                    action=action,
                    reward=float(j),
                    next_obs=np.zeros(2),
                    done=j == 2,
                ))
            buffer.add(ep)

        assert len(buffer) == 5

        sampled = buffer.sample_episodes(3)
        assert len(sampled) == 3

    def test_episode_buffer_sample_transitions(self):
        """Test sampling transitions across episodes."""
        buffer = EpisodeBuffer(capacity=10, seed=42)

        action = Action.move(0, 0)
        for i in range(3):
            ep = Episode()
            for j in range(4):
                ep.add(Transition(
                    obs=np.array([float(i * 10 + j)]),
                    action=action,
                    reward=float(i * 10 + j),
                    next_obs=np.array([float(i * 10 + j + 1)]),
                    done=j == 3,
                ))
            buffer.add(ep)

        # 3 episodes * 4 transitions = 12 total
        transitions = buffer.sample_transitions(5)
        assert len(transitions) == 5

    def test_episode_buffer_stats(self):
        """Test episode buffer statistics."""
        buffer = EpisodeBuffer(capacity=10)

        action = Action.move(0, 0)
        for i in range(3):
            ep = Episode()
            for j in range(5):
                ep.add(Transition(np.zeros(1), action, 0.0, np.zeros(1), False))
            buffer.add(ep)

        stats = buffer.get_stats()
        assert stats["num_episodes"] == 3
        assert stats["total_transitions"] == 15
        assert stats["avg_episode_length"] == 5.0

    def test_episode_buffer_filter_by_outcome(self):
        """Test filtering episodes by winner."""
        buffer = EpisodeBuffer(capacity=10)

        action = Action.move(0, 0)
        for i in range(4):
            ep = Episode(metadata={"winner": i % 2})
            ep.add(Transition(np.zeros(1), action, 0.0, np.zeros(1), True))
            buffer.add(ep)

        wins = buffer.filter_by_outcome(winner=0)
        losses = buffer.filter_by_outcome(winner=1)

        assert len(wins) == 2
        assert len(losses) == 2


class TestTransitionCollector:
    """Tests for TransitionCollector."""

    def test_collector_basic_usage(self):
        """Test basic transition collection."""
        buffer = ReplayBuffer(capacity=100)
        collector = TransitionCollector(buffer=buffer)

        collector.start_episode(metadata={"seed": 42})

        action = Action.move(0, 0)
        collector.record_step(np.array([1]), action, 0.1, False)
        collector.record_step(np.array([2]), action, 0.2, False)
        collector.record_step(np.array([3]), action, 0.3, True)

        # Should have 2 transitions (obs1->obs2, obs2->obs3)
        # The last observation doesn't have a "next" yet until done
        assert len(buffer) == 2

    def test_collector_with_episode_buffer(self):
        """Test collection into episode buffer."""
        ep_buffer = EpisodeBuffer(capacity=10)
        collector = TransitionCollector(episode_buffer=ep_buffer)

        action = Action.move(0, 0)

        collector.start_episode()
        collector.record_step(np.array([1]), action, 0.1, False)
        collector.record_step(np.array([2]), action, 0.2, True)

        assert len(ep_buffer) == 1
        assert len(ep_buffer.episodes[0]) == 1


class TestEnvConfig:
    """Tests for EnvConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EnvConfig()

        assert config.game_type == "doubles"
        assert config.active_slots == 2
        assert config.team_size == 6
        assert config.reward_mode == "win_loss"
        assert config.max_turns == 200

    def test_custom_config(self):
        """Test custom configuration."""
        config = EnvConfig(
            game_type="singles",
            active_slots=1,
            reward_mode="shaped",
            win_reward=10.0,
            max_turns=100,
        )

        assert config.game_type == "singles"
        assert config.active_slots == 1
        assert config.reward_mode == "shaped"
        assert config.win_reward == 10.0
        assert config.max_turns == 100


class TestBattleEnv:
    """Tests for BattleEnv."""

    def test_env_creation(self):
        """Test environment creation."""
        agent1 = RandomAgent(seed=1)
        agent2 = RandomAgent(seed=2)

        env = BattleEnv(
            player_map={0: agent1, 1: agent2},
            config=EnvConfig(max_turns=10),
        )

        assert env.config.max_turns == 10

    def test_env_reset(self):
        """Test environment reset."""
        agent1 = RandomAgent(seed=1)
        agent2 = RandomAgent(seed=2)

        env = BattleEnv(
            player_map={0: agent1, 1: agent2},
        )

        observations = env.reset(seed=42)

        assert isinstance(observations, dict)
        assert 0 in observations
        assert 1 in observations

    def test_env_observation_shape(self):
        """Test observation shape property."""
        agent1 = RandomAgent()
        agent2 = RandomAgent()

        env = BattleEnv(
            player_map={0: agent1, 1: agent2},
            config=EnvConfig(team_size=6, active_slots=2),
        )

        shape = env.observation_shape
        assert isinstance(shape, tuple)
        assert len(shape) == 1  # Flattened observation

    def test_env_legal_actions(self):
        """Test getting legal actions."""
        agent1 = RandomAgent()
        agent2 = RandomAgent()

        env = BattleEnv(
            player_map={0: agent1, 1: agent2},
        )

        env.reset(seed=42)
        legal = env._get_legal_actions(0)

        # Should have at least one legal action
        assert len(legal) > 0
        assert all(isinstance(a, Action) for a in legal)


class TestSingleAgentEnv:
    """Tests for SingleAgentEnv wrapper."""

    def test_single_agent_wrapper(self):
        """Test single-agent wrapper."""
        agent1 = RandomAgent()  # Learning agent (will be controlled externally)
        agent2 = HeuristicAgent()  # Opponent

        base_env = BattleEnv(
            player_map={0: agent1, 1: agent2},
        )

        env = SingleAgentEnv(base_env, agent_side=0)

        obs = env.reset(seed=42)
        assert isinstance(obs, np.ndarray)

        legal = env.get_legal_actions()
        assert len(legal) > 0

    def test_single_agent_step(self):
        """Test single-agent step."""
        agent1 = RandomAgent()
        agent2 = RandomAgent()

        base_env = BattleEnv(
            player_map={0: agent1, 1: agent2},
            config=EnvConfig(max_turns=5),
        )

        env = SingleAgentEnv(base_env, agent_side=0)

        obs = env.reset(seed=42)
        legal = env.get_legal_actions()

        if legal:
            action = legal[0]
            next_obs, reward, done, info = env.step(action)

            assert isinstance(next_obs, np.ndarray)
            assert isinstance(reward, float)
            assert isinstance(done, bool)
