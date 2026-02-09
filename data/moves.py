"""Pokemon move data structures.

Moves have properties like base power, accuracy, type, category, etc.
This module defines the MoveData frozen dataclass and move flags.
"""
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import Dict, Optional, Set

from .types import Type


class MoveCategory(IntEnum):
    """Move damage category."""
    STATUS = 0
    PHYSICAL = 1
    SPECIAL = 2


class MoveTarget(IntEnum):
    """Move targeting options."""
    NORMAL = 0              # Single adjacent target
    SELF = 1                # User only
    ADJACENT_ALLY = 2       # Single adjacent ally
    ADJACENT_ALLY_OR_SELF = 3  # User or adjacent ally
    ADJACENT_FOE = 4        # Single adjacent foe
    ALL_ADJACENT = 5        # All adjacent Pokemon
    ALL_ADJACENT_FOES = 6   # All adjacent foes
    ALL_ALLIES = 7          # All allies (not self)
    ALL = 8                 # All Pokemon on field
    ANY = 9                 # Any single Pokemon
    ALLY_SIDE = 10          # User's side
    FOE_SIDE = 11           # Opponent's side
    ALLY_TEAM = 12          # User's entire team
    RANDOM_NORMAL = 13      # Random adjacent foe
    SCRIPTED = 14           # Determined by move effect


class MoveFlag(IntFlag):
    """Bitflags for move properties."""
    NONE = 0
    CONTACT = 1 << 0        # Makes contact
    PROTECT = 1 << 1        # Blocked by Protect/Detect
    MIRROR = 1 << 2         # Can be copied by Mirror Move
    SOUND = 1 << 3          # Sound-based move
    BULLET = 1 << 4         # Ballistics move
    BITE = 1 << 5           # Biting move (Strong Jaw)
    PUNCH = 1 << 6          # Punching move (Iron Fist)
    POWDER = 1 << 7         # Powder move (blocked by Grass/Overcoat)
    CHARGE = 1 << 8         # Charges first turn
    RECHARGE = 1 << 9       # Must recharge after
    HEAL = 1 << 10          # Healing move
    GRAVITY = 1 << 11       # Fails under Gravity
    DISTANCE = 1 << 12      # Can hit non-adjacent in Triples
    DEFROST = 1 << 13       # Thaws user if frozen
    BYPASSSUB = 1 << 14     # Bypasses Substitute
    REFLECTABLE = 1 << 15   # Can be reflected by Magic Coat/Bounce
    SNATCH = 1 << 16        # Can be stolen by Snatch
    NONSKY = 1 << 17        # Fails against airborne Pokemon
    DANCE = 1 << 18         # Dance move (Dancer ability)
    SLICING = 1 << 19       # Slicing move (Sharpness ability)
    WIND = 1 << 20          # Wind move (Wind Rider/Power abilities)
    METRONOME = 1 << 21     # Can be called by Metronome
    FAILENCORE = 1 << 22    # Cannot be Encored
    FAILMEFIRST = 1 << 23   # Cannot be used via Me First
    NOSLEEPTALK = 1 << 24   # Cannot be called by Sleep Talk
    NOASSIST = 1 << 25      # Cannot be called by Assist
    FAILCOPYCAT = 1 << 26   # Cannot be called by Copycat
    FAILINSTRUCT = 1 << 27  # Cannot be called by Instruct
    FAILMIMIC = 1 << 28     # Cannot be called by Mimic
    FUTUREMOVE = 1 << 29    # Future move (Future Sight, Doom Desire)
    MUSTPRESSURE = 1 << 30  # Pressure always applies extra PP cost


@dataclass(frozen=True)
class SecondaryEffect:
    """Secondary effect that may trigger on a move."""
    chance: int                  # Percent chance (0-100)
    status: Optional[str] = None # Status to inflict (brn, par, psn, etc.)
    volatile_status: Optional[str] = None  # Volatile status (confusion, etc.)
    boosts: Optional[Dict[str, int]] = None  # Stat boosts to apply
    self_boosts: Optional[Dict[str, int]] = None  # Boosts to apply to user


@dataclass(frozen=True)
class MoveData:
    """Immutable data for a Pokemon move.

    Attributes:
        id: Unique integer ID for this move
        name: Display name of the move
        type: Type of the move
        category: Physical, Special, or Status
        base_power: Base power (0 for status moves)
        accuracy: Accuracy percentage (0-100), or None for never-miss
        pp: Base PP for this move
        priority: Priority bracket (-7 to +5)
        target: Targeting mode
        flags: Bitflags for move properties
        crit_ratio: Critical hit ratio modifier (1 = normal, 2 = high crit)
        drain: Fraction of damage healed (0.5 for Drain Punch)
        recoil: Fraction of damage taken as recoil (0.33 for recoil moves)
        secondary: Optional secondary effect
        multi_hit: Tuple of (min, max) hits for multi-hit moves
        is_z_move: True if this is a Z-Move
        is_max_move: True if this is a Max Move
    """
    id: int
    name: str
    type: Type
    category: MoveCategory
    base_power: int = 0
    accuracy: Optional[int] = 100
    pp: int = 5
    priority: int = 0
    target: MoveTarget = MoveTarget.NORMAL
    flags: MoveFlag = MoveFlag.NONE
    crit_ratio: int = 1
    drain: float = 0.0
    recoil: float = 0.0
    secondary: Optional[SecondaryEffect] = None
    multi_hit: Optional[tuple] = None
    is_z_move: bool = False
    is_max_move: bool = False

    @property
    def is_status(self) -> bool:
        """Returns True if this is a status move."""
        return self.category == MoveCategory.STATUS

    @property
    def makes_contact(self) -> bool:
        """Returns True if this move makes contact."""
        return bool(self.flags & MoveFlag.CONTACT)

    @property
    def can_protect(self) -> bool:
        """Returns True if this move can be blocked by Protect."""
        return bool(self.flags & MoveFlag.PROTECT)


# Common move flag combinations
STANDARD_ATTACK = MoveFlag.CONTACT | MoveFlag.PROTECT | MoveFlag.MIRROR
SPECIAL_ATTACK = MoveFlag.PROTECT | MoveFlag.MIRROR
STATUS_MOVE = MoveFlag.REFLECTABLE


# Target string to enum mapping for parsing
TARGET_BY_NAME: Dict[str, MoveTarget] = {
    "normal": MoveTarget.NORMAL,
    "self": MoveTarget.SELF,
    "adjacentAlly": MoveTarget.ADJACENT_ALLY,
    "adjacentAllyOrSelf": MoveTarget.ADJACENT_ALLY_OR_SELF,
    "adjacentFoe": MoveTarget.ADJACENT_FOE,
    "allAdjacent": MoveTarget.ALL_ADJACENT,
    "allAdjacentFoes": MoveTarget.ALL_ADJACENT_FOES,
    "allies": MoveTarget.ALL_ALLIES,
    "all": MoveTarget.ALL,
    "any": MoveTarget.ANY,
    "allyTeam": MoveTarget.ALLY_TEAM,
    "allySide": MoveTarget.ALLY_SIDE,
    "foeSide": MoveTarget.FOE_SIDE,
    "randomNormal": MoveTarget.RANDOM_NORMAL,
    "scripted": MoveTarget.SCRIPTED,
}


# Category string to enum mapping
CATEGORY_BY_NAME: Dict[str, MoveCategory] = {
    "status": MoveCategory.STATUS,
    "physical": MoveCategory.PHYSICAL,
    "special": MoveCategory.SPECIAL,
}


# Flag string to enum mapping
FLAG_BY_NAME: Dict[str, MoveFlag] = {
    "contact": MoveFlag.CONTACT,
    "protect": MoveFlag.PROTECT,
    "mirror": MoveFlag.MIRROR,
    "sound": MoveFlag.SOUND,
    "bullet": MoveFlag.BULLET,
    "bite": MoveFlag.BITE,
    "punch": MoveFlag.PUNCH,
    "powder": MoveFlag.POWDER,
    "charge": MoveFlag.CHARGE,
    "recharge": MoveFlag.RECHARGE,
    "heal": MoveFlag.HEAL,
    "gravity": MoveFlag.GRAVITY,
    "distance": MoveFlag.DISTANCE,
    "defrost": MoveFlag.DEFROST,
    "bypasssub": MoveFlag.BYPASSSUB,
    "reflectable": MoveFlag.REFLECTABLE,
    "snatch": MoveFlag.SNATCH,
    "nonsky": MoveFlag.NONSKY,
    "dance": MoveFlag.DANCE,
    "slicing": MoveFlag.SLICING,
    "wind": MoveFlag.WIND,
    "metronome": MoveFlag.METRONOME,
    "failencore": MoveFlag.FAILENCORE,
    "failmefirst": MoveFlag.FAILMEFIRST,
    "nosleeptalk": MoveFlag.NOSLEEPTALK,
    "noassist": MoveFlag.NOASSIST,
    "failcopycat": MoveFlag.FAILCOPYCAT,
    "failinstruct": MoveFlag.FAILINSTRUCT,
    "failmimic": MoveFlag.FAILMIMIC,
    "futuremove": MoveFlag.FUTUREMOVE,
    "mustpressure": MoveFlag.MUSTPRESSURE,
}
