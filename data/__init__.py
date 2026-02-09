"""Pokemon battle simulator data layer.

This package provides static game data: types, natures, moves, abilities, and items.
All data uses integer IDs for efficient lookup during battle simulation.
"""
from .types import (
    Type,
    TYPE_CHART,
    TYPE_BY_NAME,
    EFFECTIVENESS_MULTIPLIER,
    get_type_effectiveness,
    get_dual_type_effectiveness,
)

from .natures import (
    Stat,
    Nature,
    NatureData,
    NATURE_DATA,
    NATURE_BY_NAME,
    get_nature_modifier,
    get_nature_modifiers,
)

from .moves import (
    MoveCategory,
    MoveTarget,
    MoveFlag,
    SecondaryEffect,
    MoveData,
    TARGET_BY_NAME,
    CATEGORY_BY_NAME,
    FLAG_BY_NAME,
    STANDARD_ATTACK,
    SPECIAL_ATTACK,
    STATUS_MOVE,
)

from .abilities import (
    AbilityFlag,
    AbilityData,
    ABILITY_REGISTRY,
    ABILITY_BY_NAME,
    get_ability,
    get_ability_id,
    register_ability,
)

from .items import (
    ItemFlag,
    ItemData,
    ITEM_REGISTRY,
    ITEM_BY_NAME,
    get_item,
    get_item_id,
    register_item,
    is_choice_item,
    is_berry,
)

from .species import (
    BaseStats,
    EvolutionData,
    EvolutionType,
    FormData,
    FormType,
    SpeciesData,
    SPECIES_REGISTRY,
    SPECIES_BY_NAME,
    SPECIES_BY_DEX,
    get_species,
    get_species_id,
    get_species_by_name,
    get_species_by_dex,
    get_all_forms_by_dex,
    register_species,
    get_species_count,
    get_base_species_count,
    get_form_species_count,
)

from .species_loader import (
    load_species_from_ts,
    load_default_species,
    ensure_species_loaded,
)

__all__ = [
    # Types
    "Type",
    "TYPE_CHART",
    "TYPE_BY_NAME",
    "EFFECTIVENESS_MULTIPLIER",
    "get_type_effectiveness",
    "get_dual_type_effectiveness",
    # Natures
    "Stat",
    "Nature",
    "NatureData",
    "NATURE_DATA",
    "NATURE_BY_NAME",
    "get_nature_modifier",
    "get_nature_modifiers",
    # Moves
    "MoveCategory",
    "MoveTarget",
    "MoveFlag",
    "SecondaryEffect",
    "MoveData",
    "TARGET_BY_NAME",
    "CATEGORY_BY_NAME",
    "FLAG_BY_NAME",
    "STANDARD_ATTACK",
    "SPECIAL_ATTACK",
    "STATUS_MOVE",
    # Abilities
    "AbilityFlag",
    "AbilityData",
    "ABILITY_REGISTRY",
    "ABILITY_BY_NAME",
    "get_ability",
    "get_ability_id",
    "register_ability",
    # Items
    "ItemFlag",
    "ItemData",
    "ITEM_REGISTRY",
    "ITEM_BY_NAME",
    "get_item",
    "get_item_id",
    "register_item",
    "is_choice_item",
    "is_berry",
    # Species
    "BaseStats",
    "EvolutionData",
    "EvolutionType",
    "FormData",
    "FormType",
    "SpeciesData",
    "SPECIES_REGISTRY",
    "SPECIES_BY_NAME",
    "SPECIES_BY_DEX",
    "get_species",
    "get_species_id",
    "get_species_by_name",
    "get_species_by_dex",
    "get_all_forms_by_dex",
    "register_species",
    "get_species_count",
    "get_base_species_count",
    "get_form_species_count",
    # Species Loader
    "load_species_from_ts",
    "load_default_species",
    "ensure_species_loaded",
]
