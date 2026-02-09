"""Pokemon ability data and registry.

Abilities are passive effects that trigger on specific events during battle.
This module defines the AbilityData structure and a registry of common abilities.
"""
from dataclasses import dataclass
from enum import IntFlag
from typing import Callable, Dict, List, Optional, Set


class AbilityFlag(IntFlag):
    """Bitflags for ability properties."""
    NONE = 0
    BREAKABLE = 1 << 0      # Can be suppressed by Mold Breaker/etc.
    FAILROLEPLAY = 1 << 1   # Cannot be copied by Role Play
    NORECEIVER = 1 << 2     # Cannot be acquired by Receiver/Power of Alchemy
    NOENTRAIN = 1 << 3      # Cannot be given by Entrainment
    NOTRACE = 1 << 4        # Cannot be copied by Trace
    FAILSKILLSWAP = 1 << 5  # Cannot be Skill Swapped
    CANTSUPPRESS = 1 << 6   # Cannot be suppressed (Neutralizing Gas, etc.)


@dataclass(frozen=True)
class AbilityData:
    """Immutable data for a Pokemon ability.

    Attributes:
        id: Unique integer ID for this ability
        name: Display name of the ability
        description: Short description of what the ability does
        rating: Competitive rating (-1 to 5, higher is better)
        flags: Bitflags for ability properties
    """
    id: int
    name: str
    description: str
    rating: float = 3.0
    flags: AbilityFlag = AbilityFlag.BREAKABLE


# Registry of common abilities with their IDs
# IDs are assigned deterministically by sorting ability names
ABILITY_REGISTRY: Dict[int, AbilityData] = {}
ABILITY_BY_NAME: Dict[str, int] = {}

# Initialize with 10 common competitive abilities
_COMMON_ABILITIES = [
    # ID 0: No ability (placeholder)
    AbilityData(
        id=0,
        name="No Ability",
        description="This Pokemon has no ability.",
        rating=0.0,
        flags=AbilityFlag.NONE,
    ),

    # Intimidate - One of the most common and impactful abilities
    AbilityData(
        id=1,
        name="Intimidate",
        description="On switch-in, lowers the Attack of adjacent foes by 1 stage.",
        rating=3.5,
        flags=AbilityFlag.BREAKABLE,
    ),

    # Levitate - Grants Ground immunity
    AbilityData(
        id=2,
        name="Levitate",
        description="This Pokemon is immune to Ground-type moves.",
        rating=3.5,
        flags=AbilityFlag.BREAKABLE,
    ),

    # Prankster - Priority for status moves
    AbilityData(
        id=3,
        name="Prankster",
        description="This Pokemon's Status moves have +1 priority.",
        rating=4.0,
        flags=AbilityFlag.NONE,
    ),

    # Huge Power / Pure Power - Doubles Attack
    AbilityData(
        id=4,
        name="Huge Power",
        description="This Pokemon's Attack is doubled.",
        rating=5.0,
        flags=AbilityFlag.NONE,
    ),

    # Speed Boost - +1 Speed at end of turn
    AbilityData(
        id=5,
        name="Speed Boost",
        description="This Pokemon's Speed is raised by 1 stage at the end of each turn.",
        rating=4.5,
        flags=AbilityFlag.NONE,
    ),

    # Protean / Libero - Changes type to match move
    AbilityData(
        id=6,
        name="Protean",
        description="This Pokemon's type changes to match the type of the move it uses.",
        rating=4.5,
        flags=AbilityFlag.NONE,
    ),

    # Multiscale - Halves damage at full HP
    AbilityData(
        id=7,
        name="Multiscale",
        description="If at full HP, this Pokemon takes halved damage from attacks.",
        rating=4.0,
        flags=AbilityFlag.BREAKABLE,
    ),

    # Magic Guard - Immune to indirect damage
    AbilityData(
        id=8,
        name="Magic Guard",
        description="This Pokemon only takes damage from attacks.",
        rating=4.5,
        flags=AbilityFlag.NONE,
    ),

    # Sturdy - Cannot be OHKOed from full HP
    AbilityData(
        id=9,
        name="Sturdy",
        description="If at full HP, this Pokemon survives any attack with at least 1 HP.",
        rating=3.0,
        flags=AbilityFlag.BREAKABLE,
    ),

    # Clear Body / White Smoke / Full Metal Body - Prevents stat drops
    AbilityData(
        id=10,
        name="Clear Body",
        description="Prevents other Pokemon from lowering this Pokemon's stats.",
        rating=2.0,
        flags=AbilityFlag.BREAKABLE,
    ),
]

# Build registries
for ability in _COMMON_ABILITIES:
    ABILITY_REGISTRY[ability.id] = ability
    ABILITY_BY_NAME[ability.name.lower().replace(" ", "")] = ability.id


def get_ability(ability_id: int) -> Optional[AbilityData]:
    """Get ability data by ID.

    Args:
        ability_id: The unique ID of the ability

    Returns:
        AbilityData if found, None otherwise
    """
    return ABILITY_REGISTRY.get(ability_id)


def get_ability_id(name: str) -> Optional[int]:
    """Get ability ID by name.

    Args:
        name: The name of the ability (case-insensitive, spaces optional)

    Returns:
        Ability ID if found, None otherwise
    """
    normalized = name.lower().replace(" ", "").replace("-", "")
    return ABILITY_BY_NAME.get(normalized)


def register_ability(ability: AbilityData) -> None:
    """Register a new ability in the registry.

    Args:
        ability: The AbilityData to register
    """
    ABILITY_REGISTRY[ability.id] = ability
    ABILITY_BY_NAME[ability.name.lower().replace(" ", "")] = ability.id
