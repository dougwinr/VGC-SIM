"""Tests for the events module.

Tests cover:
- EventType enum
- BattleEvent dataclass
- Event factory functions
- Serialization/deserialization
"""
import pytest

from core.events import (
    EventType,
    BattleEvent,
    create_switch_event,
    create_move_event,
    create_damage_event,
    create_heal_event,
    create_faint_event,
    create_status_event,
    create_boost_event,
    create_weather_event,
    create_terrain_event,
    create_win_event,
    create_choice_event,
)


# =============================================================================
# EventType Tests
# =============================================================================

class TestEventType:
    """Tests for EventType enum."""

    def test_event_type_values(self):
        """Verify key event types have correct values."""
        assert EventType.BATTLE_START == 0
        assert EventType.TURN_START == 20
        assert EventType.SWITCH == 30
        assert EventType.MOVE == 32
        assert EventType.DAMAGE == 50
        assert EventType.FAINT == 53
        assert EventType.STATUS == 70
        assert EventType.BOOST == 90
        assert EventType.WEATHER_START == 110
        assert EventType.WIN == 210

    def test_event_type_categories(self):
        """Verify event types are in correct categories."""
        # Setup events (0-19)
        assert 0 <= EventType.BATTLE_START < 20
        assert 0 <= EventType.TEAM_PREVIEW < 20

        # Turn events (20-29)
        assert 20 <= EventType.TURN_START < 30
        assert 20 <= EventType.TURN_END < 30

        # Action events (30-49)
        assert 30 <= EventType.SWITCH < 50
        assert 30 <= EventType.MOVE < 50

        # Damage events (50-69)
        assert 50 <= EventType.DAMAGE < 70
        assert 50 <= EventType.FAINT < 70

    def test_all_event_types_unique(self):
        """Verify all event types have unique values."""
        values = [e.value for e in EventType]
        assert len(values) == len(set(values))

    def test_event_type_name(self):
        """Verify event type names are accessible."""
        assert EventType.DAMAGE.name == "DAMAGE"
        assert EventType.SWITCH.name == "SWITCH"
        assert EventType.WIN.name == "WIN"


# =============================================================================
# BattleEvent Tests
# =============================================================================

class TestBattleEvent:
    """Tests for BattleEvent dataclass."""

    def test_create_basic_event(self):
        """Test creating a basic event."""
        event = BattleEvent(
            event_type=EventType.DAMAGE,
            turn=1,
            side=0,
            slot=0,
        )

        assert event.event_type == EventType.DAMAGE
        assert event.turn == 1
        assert event.side == 0
        assert event.slot == 0
        assert event.data == {}
        assert event.timestamp == 0

    def test_create_event_with_data(self):
        """Test creating an event with data."""
        event = BattleEvent(
            event_type=EventType.DAMAGE,
            turn=1,
            side=0,
            slot=0,
            data={"damage": 50, "source": "Thunderbolt"},
        )

        assert event.data["damage"] == 50
        assert event.data["source"] == "Thunderbolt"

    def test_create_event_with_none_data(self):
        """Test creating an event with data=None defaults to empty dict."""
        event = BattleEvent(
            event_type=EventType.DAMAGE,
            turn=1,
            side=0,
            slot=0,
            data=None,
        )

        # __post_init__ should convert None to empty dict
        assert event.data == {}

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = BattleEvent(
            event_type=EventType.MOVE,
            turn=2,
            side=1,
            slot=0,
            data={"move": "Earthquake"},
            timestamp=5,
        )

        d = event.to_dict()

        assert d["type"] == "MOVE"
        assert d["type_id"] == EventType.MOVE.value
        assert d["turn"] == 2
        assert d["side"] == 1
        assert d["slot"] == 0
        assert d["data"]["move"] == "Earthquake"
        assert d["timestamp"] == 5

    def test_event_from_dict(self):
        """Test creating event from dictionary."""
        d = {
            "type": "FAINT",
            "type_id": EventType.FAINT.value,
            "turn": 5,
            "side": 0,
            "slot": 1,
            "data": {"species": "Pikachu"},
            "timestamp": 10,
        }

        event = BattleEvent.from_dict(d)

        assert event.event_type == EventType.FAINT
        assert event.turn == 5
        assert event.side == 0
        assert event.slot == 1
        assert event.data["species"] == "Pikachu"
        assert event.timestamp == 10

    def test_event_roundtrip(self):
        """Test serialization roundtrip."""
        original = BattleEvent(
            event_type=EventType.STATUS,
            turn=3,
            side=1,
            slot=0,
            data={"status": "brn", "source": "Flamethrower"},
            timestamp=15,
        )

        d = original.to_dict()
        restored = BattleEvent.from_dict(d)

        assert restored.event_type == original.event_type
        assert restored.turn == original.turn
        assert restored.side == original.side
        assert restored.slot == original.slot
        assert restored.data == original.data
        assert restored.timestamp == original.timestamp

    def test_event_str(self):
        """Test event string representation."""
        event = BattleEvent(
            event_type=EventType.DAMAGE,
            turn=1,
            side=0,
            slot=0,
            data={"damage": 30},
        )

        s = str(event)
        assert "[T1]" in s
        assert "DAMAGE" in s
        assert "p1" in s


# =============================================================================
# Event Factory Tests
# =============================================================================

class TestEventFactories:
    """Tests for event factory functions."""

    def test_create_switch_event(self):
        """Test creating switch event."""
        event = create_switch_event(
            turn=1,
            side=0,
            slot=0,
            species="Pikachu",
            nickname="Sparky",
            hp_percent=100,
        )

        assert event.event_type == EventType.SWITCH
        assert event.turn == 1
        assert event.side == 0
        assert event.slot == 0
        assert event.data["species"] == "Pikachu"
        assert event.data["nickname"] == "Sparky"
        assert event.data["hp_percent"] == 100

    def test_create_move_event(self):
        """Test creating move event."""
        event = create_move_event(
            turn=2,
            side=1,
            slot=0,
            move_name="Thunderbolt",
            move_id=85,
            target_side=0,
            target_slot=0,
        )

        assert event.event_type == EventType.MOVE
        assert event.data["move"] == "Thunderbolt"
        assert event.data["move_id"] == 85
        assert event.data["target_side"] == 0
        assert event.data["target_slot"] == 0

    def test_create_damage_event(self):
        """Test creating damage event."""
        event = create_damage_event(
            turn=2,
            side=0,
            slot=0,
            hp_before=100,
            hp_after=70,
            source="Earthquake",
        )

        assert event.event_type == EventType.DAMAGE
        assert event.data["hp_before"] == 100
        assert event.data["hp_after"] == 70
        assert event.data["damage"] == 30
        assert event.data["source"] == "Earthquake"

    def test_create_heal_event(self):
        """Test creating heal event."""
        event = create_heal_event(
            turn=3,
            side=1,
            slot=0,
            hp_before=50,
            hp_after=75,
            source="Leftovers",
        )

        assert event.event_type == EventType.HEAL
        assert event.data["hp_before"] == 50
        assert event.data["hp_after"] == 75
        assert event.data["healed"] == 25

    def test_create_faint_event(self):
        """Test creating faint event."""
        event = create_faint_event(
            turn=5,
            side=0,
            slot=1,
            species="Charizard",
        )

        assert event.event_type == EventType.FAINT
        assert event.data["species"] == "Charizard"

    def test_create_status_event(self):
        """Test creating status event."""
        event = create_status_event(
            turn=2,
            side=1,
            slot=0,
            status="par",
            source="Thunder Wave",
        )

        assert event.event_type == EventType.STATUS
        assert event.data["status"] == "par"
        assert event.data["source"] == "Thunder Wave"

    def test_create_boost_event_positive(self):
        """Test creating positive boost event."""
        event = create_boost_event(
            turn=1,
            side=0,
            slot=0,
            stat="atk",
            stages=2,
        )

        assert event.event_type == EventType.BOOST
        assert event.data["stat"] == "atk"
        assert event.data["stages"] == 2

    def test_create_boost_event_negative(self):
        """Test creating negative boost event (unboost)."""
        event = create_boost_event(
            turn=1,
            side=1,
            slot=0,
            stat="def",
            stages=-1,
        )

        assert event.event_type == EventType.UNBOOST
        assert event.data["stat"] == "def"
        assert event.data["stages"] == 1

    def test_create_weather_event(self):
        """Test creating weather event."""
        event = create_weather_event(
            turn=1,
            weather="Sandstorm",
            source="Sand Stream",
        )

        assert event.event_type == EventType.WEATHER_START
        assert event.data["weather"] == "Sandstorm"
        assert event.data["source"] == "Sand Stream"

    def test_create_weather_upkeep_event(self):
        """Test creating weather upkeep event."""
        event = create_weather_event(
            turn=2,
            weather="Rain",
            upkeep=True,
        )

        assert event.event_type == EventType.WEATHER_UPKEEP

    def test_create_terrain_event(self):
        """Test creating terrain event."""
        event = create_terrain_event(
            turn=1,
            terrain="Electric",
            source="Electric Surge",
        )

        assert event.event_type == EventType.TERRAIN_START
        assert event.data["terrain"] == "Electric"

    def test_create_win_event(self):
        """Test creating win event."""
        event = create_win_event(
            turn=10,
            winner_side=0,
            winner_name="Player1",
        )

        assert event.event_type == EventType.WIN
        assert event.side == 0
        assert event.data["winner"] == "Player1"

    def test_create_choice_move_event(self):
        """Test creating move choice event."""
        event = create_choice_event(
            turn=1,
            side=0,
            slot=0,
            choice_type="move",
            move_slot=0,
            target=1,
        )

        assert event.event_type == EventType.CHOICE_MOVE
        assert event.data["move_slot"] == 0
        assert event.data["target"] == 1

    def test_create_choice_switch_event(self):
        """Test creating switch choice event."""
        event = create_choice_event(
            turn=1,
            side=1,
            slot=0,
            choice_type="switch",
            switch_to=2,
        )

        assert event.event_type == EventType.CHOICE_SWITCH
        assert event.data["switch_to"] == 2

    def test_create_choice_pass_event(self):
        """Test creating pass choice event."""
        event = create_choice_event(
            turn=1,
            side=0,
            slot=1,
            choice_type="pass",
        )

        assert event.event_type == EventType.CHOICE_PASS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
