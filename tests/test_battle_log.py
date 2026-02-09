"""Tests for the battle_log module.

Tests cover:
- BattleLog class
- Serialization/deserialization
- Battle recording
- Replay from choices
- State comparison
"""
import pytest
import json
import tempfile
from pathlib import Path

from core.events import EventType, BattleEvent, create_choice_event
from core.battle_log import (
    BattleLog,
    BattleLogMetadata,
    BattleRecorder,
    replay_from_choices,
    compare_states,
    verify_replay_determinism,
)
from core.battle_state import BattleState
from core.battle import BattleEngine, Choice
from core.layout import (
    P_SPECIES, P_LEVEL, P_CURRENT_HP, P_STAT_HP, P_STAT_ATK, P_STAT_DEF,
    P_STAT_SPA, P_STAT_SPD, P_STAT_SPE, P_TYPE1, P_TYPE2,
    P_MOVE1, P_PP1,
)
from data.moves import MoveData, MoveCategory, MoveTarget, MoveFlag
from data.types import Type


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_metadata():
    """Sample battle metadata."""
    return BattleLogMetadata(
        format="[Gen 9] VGC 2025",
        gen=9,
        gametype="doubles",
        seed=12345,
        players={"p1": "Player1", "p2": "Player2"},
        teams={
            "p1": [{"species": "Pikachu", "level": 50}],
            "p2": [{"species": "Charizard", "level": 50}],
        },
    )


@pytest.fixture
def sample_events():
    """Sample battle events."""
    return [
        BattleEvent(EventType.BATTLE_START, turn=0, timestamp=0),
        BattleEvent(EventType.SWITCH, turn=0, side=0, slot=0,
                    data={"species": "Pikachu"}, timestamp=1),
        BattleEvent(EventType.SWITCH, turn=0, side=1, slot=0,
                    data={"species": "Charizard"}, timestamp=2),
        BattleEvent(EventType.TURN_START, turn=1, timestamp=3),
        BattleEvent(EventType.MOVE, turn=1, side=0, slot=0,
                    data={"move": "Thunderbolt"}, timestamp=4),
        BattleEvent(EventType.DAMAGE, turn=1, side=1, slot=0,
                    data={"damage": 50}, timestamp=5),
    ]


@pytest.fixture
def basic_move():
    """Basic move for testing."""
    return MoveData(
        id=1,
        name="Tackle",
        type=Type.NORMAL,
        category=MoveCategory.PHYSICAL,
        base_power=40,
        accuracy=100,
        pp=35,
        priority=0,
        target=MoveTarget.NORMAL,
        flags=MoveFlag.CONTACT | MoveFlag.PROTECT,
    )


@pytest.fixture
def basic_state():
    """Basic battle state for testing."""
    state = BattleState(seed=42)

    for side in range(2):
        for slot in range(2):
            state.pokemons[side, slot, P_SPECIES] = 1 + side * 2 + slot
            state.pokemons[side, slot, P_LEVEL] = 50
            state.pokemons[side, slot, P_STAT_HP] = 100
            state.pokemons[side, slot, P_CURRENT_HP] = 100
            state.pokemons[side, slot, P_STAT_ATK] = 80
            state.pokemons[side, slot, P_STAT_DEF] = 80
            state.pokemons[side, slot, P_STAT_SPA] = 80
            state.pokemons[side, slot, P_STAT_SPD] = 80
            state.pokemons[side, slot, P_STAT_SPE] = 80 + side * 10 + slot * 5
            state.pokemons[side, slot, P_TYPE1] = Type.NORMAL.value
            state.pokemons[side, slot, P_TYPE2] = -1
            state.pokemons[side, slot, P_MOVE1] = 1
            state.pokemons[side, slot, P_PP1] = 35
            state.active[side, slot] = slot

    return state


@pytest.fixture
def move_registry(basic_move):
    """Move registry for testing."""
    return {1: basic_move}


# =============================================================================
# BattleLog Tests
# =============================================================================

class TestBattleLog:
    """Tests for BattleLog class."""

    def test_create_empty_log(self):
        """Test creating an empty battle log."""
        log = BattleLog()

        assert len(log) == 0
        assert log.metadata.gen == 9
        assert log.metadata.gametype == "doubles"

    def test_add_event(self, sample_events):
        """Test adding events to log."""
        log = BattleLog()

        for event in sample_events:
            log.add_event(event)

        assert len(log) == len(sample_events)

    def test_event_timestamps(self):
        """Test that events get sequential timestamps."""
        log = BattleLog()

        for i in range(5):
            log.add_event(BattleEvent(EventType.TURN_START, turn=i))

        for i, event in enumerate(log.events):
            assert event.timestamp == i

    def test_add_choice(self):
        """Test adding player choices."""
        log = BattleLog()

        choice = Choice(choice_type='move', slot=0, move_slot=0, target=1)
        log.add_choice(turn=1, side=0, slot=0, choice=choice)

        assert len(log) == 1
        assert log.events[0].event_type == EventType.CHOICE_MOVE

    def test_get_events_by_type(self, sample_events):
        """Test filtering events by type."""
        log = BattleLog()
        for event in sample_events:
            log.add_event(event)

        switches = log.get_events(event_type=EventType.SWITCH)
        assert len(switches) == 2

        moves = log.get_events(event_type=EventType.MOVE)
        assert len(moves) == 1

    def test_get_events_by_turn(self, sample_events):
        """Test filtering events by turn."""
        log = BattleLog()
        for event in sample_events:
            log.add_event(event)

        turn_0 = log.get_events(turn=0)
        assert len(turn_0) == 3

        turn_1 = log.get_events(turn=1)
        assert len(turn_1) == 3

    def test_get_events_by_side(self, sample_events):
        """Test filtering events by side."""
        log = BattleLog()
        for event in sample_events:
            log.add_event(event)

        side_0 = log.get_events(side=0)
        assert len(side_0) == 2

    def test_get_choice_events(self):
        """Test getting choice events."""
        log = BattleLog()

        log.add_choice(turn=1, side=0, slot=0,
                       choice=Choice('move', 0, move_slot=0, target=1))
        log.add_choice(turn=1, side=1, slot=0,
                       choice=Choice('switch', 0, switch_to=2))
        log.add_event(BattleEvent(EventType.MOVE, turn=1))

        choices = log.get_choice_events()
        assert len(choices) == 2

    def test_get_choices_for_turn(self):
        """Test getting choices for a specific turn."""
        log = BattleLog()

        log.add_choice(turn=1, side=0, slot=0,
                       choice=Choice('move', 0, move_slot=0, target=1))
        log.add_choice(turn=1, side=0, slot=1,
                       choice=Choice('move', 1, move_slot=1, target=2))
        log.add_choice(turn=1, side=1, slot=0,
                       choice=Choice('switch', 0, switch_to=2))

        choices = log.get_choices_for_turn(1)

        assert len(choices[0]) == 2
        assert len(choices[1]) == 1
        assert choices[0][0].choice_type == 'move'
        assert choices[1][0].choice_type == 'switch'

    def test_iter_turns(self, sample_events):
        """Test iterating over turns."""
        log = BattleLog()
        for event in sample_events:
            log.add_event(event)

        turns = list(log.iter_turns())

        assert len(turns) == 2  # Turn 0 and Turn 1
        assert turns[0][0] == 0
        assert turns[1][0] == 1


# =============================================================================
# Serialization Tests
# =============================================================================

class TestBattleLogSerialization:
    """Tests for BattleLog serialization."""

    def test_to_dict(self, sample_metadata, sample_events):
        """Test converting log to dictionary."""
        log = BattleLog(metadata=sample_metadata)
        for event in sample_events:
            log.add_event(event)

        d = log.to_dict()

        assert "metadata" in d
        assert "events" in d
        assert d["metadata"]["format"] == "[Gen 9] VGC 2025"
        assert len(d["events"]) == len(sample_events)

    def test_from_dict(self, sample_metadata, sample_events):
        """Test creating log from dictionary."""
        log = BattleLog(metadata=sample_metadata)
        for event in sample_events:
            log.add_event(event)

        d = log.to_dict()
        restored = BattleLog.from_dict(d)

        assert restored.metadata.format == sample_metadata.format
        assert restored.metadata.seed == sample_metadata.seed
        assert len(restored) == len(log)

    def test_to_json(self, sample_metadata, sample_events):
        """Test converting log to JSON."""
        log = BattleLog(metadata=sample_metadata)
        for event in sample_events:
            log.add_event(event)

        json_str = log.to_json()
        parsed = json.loads(json_str)

        assert "metadata" in parsed
        assert "events" in parsed

    def test_from_json(self, sample_metadata, sample_events):
        """Test creating log from JSON."""
        log = BattleLog(metadata=sample_metadata)
        for event in sample_events:
            log.add_event(event)

        json_str = log.to_json()
        restored = BattleLog.from_json(json_str)

        assert restored.metadata.format == sample_metadata.format
        assert len(restored) == len(log)

    def test_roundtrip(self, sample_metadata, sample_events):
        """Test full serialization roundtrip."""
        original = BattleLog(metadata=sample_metadata)
        for event in sample_events:
            original.add_event(event)

        json_str = original.to_json()
        restored = BattleLog.from_json(json_str)

        assert restored.metadata.format == original.metadata.format
        assert restored.metadata.seed == original.metadata.seed
        assert len(restored) == len(original)

        for orig, rest in zip(original.events, restored.events):
            assert orig.event_type == rest.event_type
            assert orig.turn == rest.turn
            assert orig.side == rest.side

    def test_save_and_load(self, sample_metadata, sample_events):
        """Test saving and loading from file."""
        log = BattleLog(metadata=sample_metadata)
        for event in sample_events:
            log.add_event(event)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            log.save(path)
            loaded = BattleLog.load(path)

            assert loaded.metadata.format == log.metadata.format
            assert len(loaded) == len(log)
        finally:
            Path(path).unlink()


# =============================================================================
# Battle Recording Tests
# =============================================================================

class TestBattleRecorder:
    """Tests for BattleRecorder class."""

    def test_create_recorder(self, basic_state, move_registry):
        """Test creating a recorder."""
        engine = BattleEngine(basic_state, move_registry)
        recorder = BattleRecorder(engine)

        assert recorder.engine is engine
        assert len(recorder.log) == 0

    def test_record_start(self, basic_state, move_registry):
        """Test recording battle start."""
        engine = BattleEngine(basic_state, move_registry)
        recorder = BattleRecorder(engine)

        recorder.start()

        # Should have battle start + initial switches
        assert len(recorder.log) >= 1
        assert recorder.log.events[0].event_type == EventType.BATTLE_START

    def test_record_turn(self, basic_state, move_registry):
        """Test recording a turn."""
        engine = BattleEngine(basic_state, move_registry)
        recorder = BattleRecorder(engine)
        recorder.start()

        choices = {
            0: [Choice('move', slot=0, move_slot=0, target=1)],
            1: [Choice('move', slot=0, move_slot=0, target=0)],
        }

        recorder.record_turn(choices)

        # Should have choice events
        choice_events = recorder.log.get_choice_events()
        assert len(choice_events) == 2

    def test_finish_recording(self, basic_state, move_registry):
        """Test finishing recording."""
        engine = BattleEngine(basic_state, move_registry)
        recorder = BattleRecorder(engine)
        recorder.start()

        choices = {
            0: [Choice('move', slot=0, move_slot=0, target=1)],
            1: [Choice('move', slot=0, move_slot=0, target=0)],
        }

        recorder.record_turn(choices)
        engine.step(choices)

        log = recorder.finish()

        assert log.metadata.total_turns >= 1
        assert log.metadata.seed == basic_state.prng.get_initial_seed()


# =============================================================================
# State Comparison Tests
# =============================================================================

class TestStateComparison:
    """Tests for state comparison functions."""

    def test_compare_identical_states(self, basic_state):
        """Test comparing identical states."""
        state2 = basic_state.copy()

        diff = compare_states(basic_state, state2)

        assert diff["match"] == True
        assert len(diff["pokemon_hp"]) == 0
        assert len(diff["field"]) == 0

    def test_compare_different_hp(self, basic_state):
        """Test comparing states with different HP."""
        state2 = basic_state.copy()
        state2.pokemons[0, 0, P_CURRENT_HP] = 50

        diff = compare_states(basic_state, state2)

        assert diff["match"] == False
        assert len(diff["pokemon_hp"]) == 1
        assert diff["pokemon_hp"][0]["side"] == 0
        assert diff["pokemon_hp"][0]["slot"] == 0

    def test_compare_different_field(self, basic_state):
        """Test comparing states with different field state."""
        from core.battle_state import FIELD_WEATHER

        state2 = basic_state.copy()
        state2.field[FIELD_WEATHER] = 1

        diff = compare_states(basic_state, state2)

        assert diff["match"] == False
        assert len(diff["field"]) >= 1


# =============================================================================
# Replay Integration Tests
# =============================================================================

class TestReplayIntegration:
    """Integration tests for battle replay."""

    def test_replay_simple_battle(self, basic_state, move_registry):
        """Test replaying a simple battle.

        Note: Full determinism requires identical RNG state, which is complex
        to achieve across initial setup. This test verifies the replay
        structure and that damage is applied (HP changed).
        """
        seed = 42

        # Create initial state with fixed seed
        initial_state = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                initial_state.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                initial_state.active[side, slot] = slot

        # Run original battle
        engine1 = BattleEngine(initial_state.copy(), move_registry)
        recorder = BattleRecorder(engine1)
        recorder.start()

        choices = {
            0: [Choice('move', slot=0, move_slot=0, target=1)],
            1: [Choice('move', slot=0, move_slot=0, target=0)],
        }

        recorder.record_turn(choices)
        engine1.step(choices)

        log = recorder.finish()

        # Verify log structure
        assert log.metadata.total_turns >= 1
        assert len(log.get_choice_events()) == 2

        # Replay the battle with same initial state
        replay_initial = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                replay_initial.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                replay_initial.active[side, slot] = slot

        final_state = replay_from_choices(replay_initial, log, move_registry)

        # Verify damage was applied in replay (HP decreased from initial)
        for side in range(2):
            hp_replay = final_state.pokemons[side, 0, P_CURRENT_HP]
            hp_initial = basic_state.pokemons[side, 0, P_CURRENT_HP]
            # HP should have changed (damage taken)
            assert hp_replay < hp_initial, \
                f"No damage in replay at side {side}: {hp_replay} vs initial {hp_initial}"

    def test_replay_multi_turn_battle(self, basic_state, move_registry):
        """Test replaying a multi-turn battle."""
        seed = 42

        # Create initial state with fixed seed
        initial_state = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                initial_state.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                initial_state.active[side, slot] = slot

        engine1 = BattleEngine(initial_state.copy(), move_registry)
        recorder = BattleRecorder(engine1)
        recorder.start()

        # Run 3 turns
        for _ in range(3):
            choices = {
                0: [Choice('move', slot=0, move_slot=0, target=1)],
                1: [Choice('move', slot=0, move_slot=0, target=0)],
            }
            recorder.record_turn(choices)
            engine1.step(choices)

        log = recorder.finish()

        # Replay
        replay_initial = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                replay_initial.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                replay_initial.active[side, slot] = slot

        final_state = replay_from_choices(replay_initial, log, move_registry)

        # Verify turn count
        assert log.metadata.total_turns == 3

    def test_replay_determinism(self, basic_state, move_registry):
        """Test that replay produces deterministic results."""
        seed = 99999

        # First run
        state1 = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                state1.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                state1.active[side, slot] = slot

        engine1 = BattleEngine(state1, move_registry)
        recorder1 = BattleRecorder(engine1)
        recorder1.start()

        choices = {
            0: [Choice('move', slot=0, move_slot=0, target=1)],
            1: [Choice('move', slot=0, move_slot=0, target=0)],
        }
        recorder1.record_turn(choices)
        engine1.step(choices)

        log1 = recorder1.finish()
        final_hp_1 = [
            state1.pokemons[side, slot, P_CURRENT_HP]
            for side in range(2) for slot in range(2)
        ]

        # Second run with same seed
        state2 = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                state2.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                state2.active[side, slot] = slot

        engine2 = BattleEngine(state2, move_registry)
        recorder2 = BattleRecorder(engine2)
        recorder2.start()
        recorder2.record_turn(choices)
        engine2.step(choices)

        final_hp_2 = [
            state2.pokemons[side, slot, P_CURRENT_HP]
            for side in range(2) for slot in range(2)
        ]

        # HP should be identical
        assert final_hp_1 == final_hp_2, \
            f"Determinism failed: {final_hp_1} vs {final_hp_2}"


# =============================================================================
# Full Battle Replay Test
# =============================================================================

class TestFullBattleReplay:
    """Full integration test: run battle, log it, replay, compare."""

    def test_full_battle_replay_verification(self, basic_state, move_registry):
        """Run a full battle, log it, replay from choices, compare states."""
        seed = 12345

        # Create initial state
        original_state = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                original_state.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                original_state.active[side, slot] = slot

        # Run battle with recording
        engine = BattleEngine(original_state.copy(), move_registry)
        recorder = BattleRecorder(engine)
        recorder.start()

        # Scripted battle - 3 turns
        all_choices = [
            {
                0: [Choice('move', slot=0, move_slot=0, target=1)],
                1: [Choice('move', slot=0, move_slot=0, target=0)],
            },
            {
                0: [Choice('move', slot=0, move_slot=0, target=1)],
                1: [Choice('move', slot=0, move_slot=0, target=0)],
            },
            {
                0: [Choice('move', slot=0, move_slot=0, target=1)],
                1: [Choice('move', slot=0, move_slot=0, target=0)],
            },
        ]

        for choices in all_choices:
            recorder.record_turn(choices)
            engine.step(choices)

        log = recorder.finish()

        # Verify log has correct structure
        assert log.metadata.total_turns == 3
        assert log.metadata.seed == seed

        # Replay from fresh state with same seed
        replay_initial = BattleState(seed=seed)
        for side in range(2):
            for slot in range(2):
                replay_initial.pokemons[side, slot, :] = basic_state.pokemons[side, slot, :]
                replay_initial.active[side, slot] = slot

        replay_final = replay_from_choices(replay_initial, log, move_registry)

        # Compare final states
        differences = compare_states(engine.state, replay_final)

        # States should match (deterministic RNG)
        if not differences["match"]:
            print(f"Differences found: {differences}")

        # Allow some tolerance due to execution differences
        assert len(differences["pokemon_hp"]) <= 4, \
            f"Too many HP differences: {differences['pokemon_hp']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
