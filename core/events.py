"""Battle events for Pokemon battle simulator.

This module provides:
- EventType enum for all battle event types
- BattleEvent dataclass for structured event data
- Event creation helpers for common events
"""
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any, Dict, List, Optional, Tuple, Union


class EventType(IntEnum):
    """Types of events that can occur during a battle.

    Events are categorized into:
    - Setup: Battle initialization and team preview
    - Turn: Turn markers and phase indicators
    - Actions: Player actions (moves, switches)
    - Effects: Results of actions (damage, status, boosts)
    - Field: Weather, terrain, and field conditions
    - End: Battle conclusion events
    """
    # Setup events (0-19)
    BATTLE_START = 0
    TEAM_PREVIEW = 1
    PLAYER_JOIN = 2
    TEAM_SIZE = 3

    # Turn events (20-29)
    TURN_START = 20
    TURN_END = 21
    UPKEEP = 22

    # Action events (30-49)
    SWITCH = 30
    SWITCH_OUT = 31
    MOVE = 32
    MEGA_EVOLVE = 33
    TERASTALLIZE = 34
    ULTRA_BURST = 35
    CANT_MOVE = 36  # Pokemon can't move (sleep, flinch, etc.)

    # Damage/HP events (50-69)
    DAMAGE = 50
    HEAL = 51
    SET_HP = 52
    FAINT = 53
    RECOIL = 54
    DRAIN = 55

    # Status events (70-89)
    STATUS = 70
    CURE_STATUS = 71
    VOLATILE_START = 72
    VOLATILE_END = 73
    CONFUSION_HIT = 74

    # Stat events (90-109)
    BOOST = 90
    UNBOOST = 91
    SET_BOOST = 92
    CLEAR_BOOST = 93
    SWAP_BOOST = 94
    COPY_BOOST = 95
    INVERT_BOOST = 96

    # Field events (110-129)
    WEATHER_START = 110
    WEATHER_END = 111
    WEATHER_UPKEEP = 112
    TERRAIN_START = 113
    TERRAIN_END = 114
    PSEUDO_WEATHER_START = 115
    PSEUDO_WEATHER_END = 116

    # Side condition events (130-149)
    SIDE_START = 130
    SIDE_END = 131
    HAZARD_DAMAGE = 132

    # Item/Ability events (150-169)
    ITEM_USE = 150
    ITEM_END = 151
    ITEM_CONSUME = 152
    ABILITY_TRIGGER = 153
    ABILITY_START = 154
    ABILITY_END = 155

    # Protection events (170-179)
    PROTECT = 170
    PROTECT_BREAK = 171
    WIDE_GUARD = 172
    QUICK_GUARD = 173
    IMMUNE = 174

    # Type effectiveness events (180-189)
    SUPER_EFFECTIVE = 180
    RESISTED = 181
    TYPE_IMMUNE = 182
    CRITICAL_HIT = 183

    # Move-specific events (190-209)
    MISS = 190
    FAIL = 191
    NO_EFFECT = 192
    ACTIVATE = 193
    SINGLE_TURN = 194  # Move effects that last one turn
    PREPARE = 195  # Two-turn move charge
    MULTI_HIT = 196

    # End events (210-219)
    WIN = 210
    TIE = 211
    FORFEIT = 212

    # Choice events (220-229)
    CHOICE_MOVE = 220
    CHOICE_SWITCH = 221
    CHOICE_PASS = 222

    # Debug/Other (230+)
    MESSAGE = 230
    DEBUG = 231


@dataclass
class BattleEvent:
    """A single event that occurred during a battle.

    Attributes:
        event_type: The type of event
        turn: Turn number when event occurred (-1 for pre-battle)
        side: Side index (0 or 1) if applicable, -1 otherwise
        slot: Active slot index if applicable, -1 otherwise
        data: Event-specific data dictionary
        timestamp: Event sequence number for ordering
    """
    event_type: EventType
    turn: int = -1
    side: int = -1
    slot: int = -1
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: int = 0

    def __post_init__(self):
        """Ensure data is a dict."""
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "type": self.event_type.name,
            "type_id": int(self.event_type),
            "turn": self.turn,
            "side": self.side,
            "slot": self.slot,
            "data": self.data,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BattleEvent":
        """Create event from dictionary."""
        return cls(
            event_type=EventType(d.get("type_id", 0)),
            turn=d.get("turn", -1),
            side=d.get("side", -1),
            slot=d.get("slot", -1),
            data=d.get("data", {}),
            timestamp=d.get("timestamp", 0),
        )

    def __str__(self) -> str:
        """Human-readable event string."""
        parts = [f"[T{self.turn}]" if self.turn >= 0 else "[PRE]"]
        parts.append(self.event_type.name)

        if self.side >= 0:
            parts.append(f"p{self.side + 1}")
            if self.slot >= 0:
                parts.append(f"slot{self.slot}")

        if self.data:
            data_str = ", ".join(f"{k}={v}" for k, v in self.data.items())
            parts.append(f"({data_str})")

        return " ".join(parts)


# =============================================================================
# Event Factory Functions
# =============================================================================

def create_switch_event(
    turn: int,
    side: int,
    slot: int,
    species: str,
    nickname: str = "",
    hp_percent: int = 100,
    from_slot: int = -1,
    timestamp: int = 0,
) -> BattleEvent:
    """Create a switch event."""
    return BattleEvent(
        event_type=EventType.SWITCH,
        turn=turn,
        side=side,
        slot=slot,
        data={
            "species": species,
            "nickname": nickname or species,
            "hp_percent": hp_percent,
            "from_slot": from_slot,
        },
        timestamp=timestamp,
    )


def create_move_event(
    turn: int,
    side: int,
    slot: int,
    move_name: str,
    move_id: int = 0,
    target_side: int = -1,
    target_slot: int = -1,
    spread: bool = False,
    timestamp: int = 0,
) -> BattleEvent:
    """Create a move event."""
    return BattleEvent(
        event_type=EventType.MOVE,
        turn=turn,
        side=side,
        slot=slot,
        data={
            "move": move_name,
            "move_id": move_id,
            "target_side": target_side,
            "target_slot": target_slot,
            "spread": spread,
        },
        timestamp=timestamp,
    )


def create_damage_event(
    turn: int,
    side: int,
    slot: int,
    hp_before: int,
    hp_after: int,
    source: str = "",
    timestamp: int = 0,
) -> BattleEvent:
    """Create a damage event."""
    return BattleEvent(
        event_type=EventType.DAMAGE,
        turn=turn,
        side=side,
        slot=slot,
        data={
            "hp_before": hp_before,
            "hp_after": hp_after,
            "damage": hp_before - hp_after,
            "source": source,
        },
        timestamp=timestamp,
    )


def create_heal_event(
    turn: int,
    side: int,
    slot: int,
    hp_before: int,
    hp_after: int,
    source: str = "",
    timestamp: int = 0,
) -> BattleEvent:
    """Create a heal event."""
    return BattleEvent(
        event_type=EventType.HEAL,
        turn=turn,
        side=side,
        slot=slot,
        data={
            "hp_before": hp_before,
            "hp_after": hp_after,
            "healed": hp_after - hp_before,
            "source": source,
        },
        timestamp=timestamp,
    )


def create_faint_event(
    turn: int,
    side: int,
    slot: int,
    species: str = "",
    timestamp: int = 0,
) -> BattleEvent:
    """Create a faint event."""
    return BattleEvent(
        event_type=EventType.FAINT,
        turn=turn,
        side=side,
        slot=slot,
        data={"species": species},
        timestamp=timestamp,
    )


def create_status_event(
    turn: int,
    side: int,
    slot: int,
    status: str,
    source: str = "",
    timestamp: int = 0,
) -> BattleEvent:
    """Create a status event."""
    return BattleEvent(
        event_type=EventType.STATUS,
        turn=turn,
        side=side,
        slot=slot,
        data={"status": status, "source": source},
        timestamp=timestamp,
    )


def create_boost_event(
    turn: int,
    side: int,
    slot: int,
    stat: str,
    stages: int,
    timestamp: int = 0,
) -> BattleEvent:
    """Create a stat boost event."""
    event_type = EventType.BOOST if stages > 0 else EventType.UNBOOST
    return BattleEvent(
        event_type=event_type,
        turn=turn,
        side=side,
        slot=slot,
        data={"stat": stat, "stages": abs(stages)},
        timestamp=timestamp,
    )


def create_weather_event(
    turn: int,
    weather: str,
    source: str = "",
    upkeep: bool = False,
    timestamp: int = 0,
) -> BattleEvent:
    """Create a weather event."""
    event_type = EventType.WEATHER_UPKEEP if upkeep else EventType.WEATHER_START
    return BattleEvent(
        event_type=event_type,
        turn=turn,
        data={"weather": weather, "source": source},
        timestamp=timestamp,
    )


def create_terrain_event(
    turn: int,
    terrain: str,
    source: str = "",
    timestamp: int = 0,
) -> BattleEvent:
    """Create a terrain event."""
    return BattleEvent(
        event_type=EventType.TERRAIN_START,
        turn=turn,
        data={"terrain": terrain, "source": source},
        timestamp=timestamp,
    )


def create_win_event(
    turn: int,
    winner_side: int,
    winner_name: str = "",
    timestamp: int = 0,
) -> BattleEvent:
    """Create a win event."""
    return BattleEvent(
        event_type=EventType.WIN,
        turn=turn,
        side=winner_side,
        data={"winner": winner_name},
        timestamp=timestamp,
    )


def create_choice_event(
    turn: int,
    side: int,
    slot: int,
    choice_type: str,
    move_slot: int = -1,
    target: int = 0,
    switch_to: int = -1,
    timestamp: int = 0,
) -> BattleEvent:
    """Create a choice (input) event for replay."""
    if choice_type == "move":
        event_type = EventType.CHOICE_MOVE
        data = {"move_slot": move_slot, "target": target}
    elif choice_type == "switch":
        event_type = EventType.CHOICE_SWITCH
        data = {"switch_to": switch_to}
    else:
        event_type = EventType.CHOICE_PASS
        data = {}

    return BattleEvent(
        event_type=event_type,
        turn=turn,
        side=side,
        slot=slot,
        data=data,
        timestamp=timestamp,
    )
