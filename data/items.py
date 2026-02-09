"""Pokemon item data and registry.

Items are held by Pokemon and provide various effects during battle.
This module defines the ItemData structure and a registry of common items.
"""
from dataclasses import dataclass
from enum import IntFlag
from typing import Dict, Optional

from .types import Type


class ItemFlag(IntFlag):
    """Bitflags for item properties."""
    NONE = 0
    CONSUMABLE = 1 << 0     # Item is consumed when used
    BERRY = 1 << 1          # Is a berry (Ripen, Unnerve interactions)
    GEM = 1 << 2            # Is a type gem
    PLATE = 1 << 3          # Is an Arceus plate
    DRIVE = 1 << 4          # Is a Genesect drive
    MEMORY = 1 << 5         # Is a Silvally memory
    MEGA_STONE = 1 << 6     # Is a Mega Stone
    Z_CRYSTAL = 1 << 7      # Is a Z-Crystal
    CHOICE = 1 << 8         # Is a Choice item (locks move)


@dataclass(frozen=True)
class ItemData:
    """Immutable data for a Pokemon item.

    Attributes:
        id: Unique integer ID for this item
        name: Display name of the item
        description: Short description of what the item does
        fling_power: Base power when used with Fling (0 if cannot be flung)
        flags: Bitflags for item properties
        type_boost: Type this item boosts (for plates, type-boosting items)
        boost_amount: Multiplier for type boost (1.2 for plates, 1.5 for gems)
    """
    id: int
    name: str
    description: str
    fling_power: int = 0
    flags: ItemFlag = ItemFlag.NONE
    type_boost: Optional[Type] = None
    boost_amount: float = 1.0


# Registry of common items with their IDs
ITEM_REGISTRY: Dict[int, ItemData] = {}
ITEM_BY_NAME: Dict[str, int] = {}

# Initialize with 10 common competitive items
_COMMON_ITEMS = [
    # ID 0: No item (placeholder)
    ItemData(
        id=0,
        name="No Item",
        description="This Pokemon is not holding an item.",
        fling_power=0,
        flags=ItemFlag.NONE,
    ),

    # Choice Band - Boosts Attack by 50%, locks move
    ItemData(
        id=1,
        name="Choice Band",
        description="Holder's Attack is 1.5x, but it can only use the first move it selects.",
        fling_power=10,
        flags=ItemFlag.CHOICE,
    ),

    # Choice Specs - Boosts Special Attack by 50%, locks move
    ItemData(
        id=2,
        name="Choice Specs",
        description="Holder's Sp. Atk is 1.5x, but it can only use the first move it selects.",
        fling_power=10,
        flags=ItemFlag.CHOICE,
    ),

    # Choice Scarf - Boosts Speed by 50%, locks move
    ItemData(
        id=3,
        name="Choice Scarf",
        description="Holder's Speed is 1.5x, but it can only use the first move it selects.",
        fling_power=10,
        flags=ItemFlag.CHOICE,
    ),

    # Life Orb - Boosts damage by 30%, costs 10% HP
    ItemData(
        id=4,
        name="Life Orb",
        description="Holder's attacks do 1.3x damage; loses 1/10 max HP after each attack.",
        fling_power=30,
        flags=ItemFlag.NONE,
    ),

    # Leftovers - Heals 1/16 HP each turn
    ItemData(
        id=5,
        name="Leftovers",
        description="Holder heals 1/16 of its max HP each turn.",
        fling_power=10,
        flags=ItemFlag.NONE,
    ),

    # Focus Sash - Survives any OHKO with 1 HP
    ItemData(
        id=6,
        name="Focus Sash",
        description="If at full HP, holder survives any single hit with 1 HP. Consumed on use.",
        fling_power=10,
        flags=ItemFlag.CONSUMABLE,
    ),

    # Assault Vest - Boosts Sp. Def by 50%, prevents status moves
    ItemData(
        id=7,
        name="Assault Vest",
        description="Holder's Sp. Def is 1.5x, but it can only use attacking moves.",
        fling_power=80,
        flags=ItemFlag.NONE,
    ),

    # Sitrus Berry - Heals 25% HP when below 50%
    ItemData(
        id=8,
        name="Sitrus Berry",
        description="Heals 1/4 max HP when at 1/2 HP or less. Consumed on use.",
        fling_power=10,
        flags=ItemFlag.CONSUMABLE | ItemFlag.BERRY,
    ),

    # Eviolite - Boosts Def and Sp. Def by 50% for NFE Pokemon
    ItemData(
        id=9,
        name="Eviolite",
        description="If holder can evolve, its Defense and Sp. Def are 1.5x.",
        fling_power=40,
        flags=ItemFlag.NONE,
    ),

    # Rocky Helmet - Deals 1/6 damage to attackers on contact
    ItemData(
        id=10,
        name="Rocky Helmet",
        description="If holder is hit by a contact move, attacker loses 1/6 of its max HP.",
        fling_power=60,
        flags=ItemFlag.NONE,
    ),
]

# Build registries
for item in _COMMON_ITEMS:
    ITEM_REGISTRY[item.id] = item
    ITEM_BY_NAME[item.name.lower().replace(" ", "")] = item.id


def get_item(item_id: int) -> Optional[ItemData]:
    """Get item data by ID.

    Args:
        item_id: The unique ID of the item

    Returns:
        ItemData if found, None otherwise
    """
    return ITEM_REGISTRY.get(item_id)


def get_item_id(name: str) -> Optional[int]:
    """Get item ID by name.

    Args:
        name: The name of the item (case-insensitive, spaces optional)

    Returns:
        Item ID if found, None otherwise
    """
    normalized = name.lower().replace(" ", "").replace("-", "")
    return ITEM_BY_NAME.get(normalized)


def register_item(item: ItemData) -> None:
    """Register a new item in the registry.

    Args:
        item: The ItemData to register
    """
    ITEM_REGISTRY[item.id] = item
    ITEM_BY_NAME[item.name.lower().replace(" ", "")] = item.id


def is_choice_item(item_id: int) -> bool:
    """Check if an item is a Choice item (Band/Specs/Scarf).

    Args:
        item_id: The item ID to check

    Returns:
        True if item locks the holder's move
    """
    item = get_item(item_id)
    return item is not None and bool(item.flags & ItemFlag.CHOICE)


def is_berry(item_id: int) -> bool:
    """Check if an item is a berry.

    Args:
        item_id: The item ID to check

    Returns:
        True if item is a berry
    """
    item = get_item(item_id)
    return item is not None and bool(item.flags & ItemFlag.BERRY)
