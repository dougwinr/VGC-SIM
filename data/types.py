"""Pokemon type chart and effectiveness calculations.

Type effectiveness values:
- 0: Normal damage (1x)
- 1: Super effective (2x)
- 2: Not very effective (0.5x)
- 3: Immune (0x)
"""
from enum import IntEnum
from typing import Dict, Tuple


class Type(IntEnum):
    """Pokemon types as integer IDs for efficient lookup."""
    NORMAL = 0
    FIRE = 1
    WATER = 2
    ELECTRIC = 3
    GRASS = 4
    ICE = 5
    FIGHTING = 6
    POISON = 7
    GROUND = 8
    FLYING = 9
    PSYCHIC = 10
    BUG = 11
    ROCK = 12
    GHOST = 13
    DRAGON = 14
    DARK = 15
    STEEL = 16
    FAIRY = 17
    STELLAR = 18  # Gen 9 Tera type


# Type effectiveness chart: TYPE_CHART[defending_type][attacking_type] -> effectiveness
# Values: 0 = normal (1x), 1 = super effective (2x), 2 = not very effective (0.5x), 3 = immune (0x)
TYPE_CHART: Dict[Type, Dict[Type, int]] = {
    Type.BUG: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 2, Type.FIRE: 1, Type.FLYING: 1,
        Type.GHOST: 0, Type.GRASS: 2, Type.GROUND: 2, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 1,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.DARK: {
        Type.BUG: 1, Type.DARK: 2, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 1, Type.FIGHTING: 1, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 2, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 3, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.DRAGON: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 1, Type.ELECTRIC: 2,
        Type.FAIRY: 1, Type.FIGHTING: 0, Type.FIRE: 2, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 2, Type.GROUND: 0, Type.ICE: 1,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 2,
    },
    Type.ELECTRIC: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 2,
        Type.FAIRY: 0, Type.FIGHTING: 0, Type.FIRE: 0, Type.FLYING: 2,
        Type.GHOST: 0, Type.GRASS: 0, Type.GROUND: 1, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 2, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.FAIRY: {
        Type.BUG: 2, Type.DARK: 2, Type.DRAGON: 3, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 2, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 1, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 1, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.FIGHTING: {
        Type.BUG: 2, Type.DARK: 2, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 1, Type.FIGHTING: 0, Type.FIRE: 0, Type.FLYING: 1,
        Type.GHOST: 0, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 1, Type.ROCK: 2,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.FIRE: {
        Type.BUG: 2, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 2, Type.FIGHTING: 0, Type.FIRE: 2, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 2, Type.GROUND: 1, Type.ICE: 2,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 1,
        Type.STEEL: 2, Type.STELLAR: 0, Type.WATER: 1,
    },
    Type.FLYING: {
        Type.BUG: 2, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 1,
        Type.FAIRY: 0, Type.FIGHTING: 2, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 2, Type.GROUND: 3, Type.ICE: 1,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 1,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.GHOST: {
        Type.BUG: 2, Type.DARK: 1, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 3, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 1, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 0,
        Type.NORMAL: 3, Type.POISON: 2, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.GRASS: {
        Type.BUG: 1, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 2,
        Type.FAIRY: 0, Type.FIGHTING: 0, Type.FIRE: 1, Type.FLYING: 1,
        Type.GHOST: 0, Type.GRASS: 2, Type.GROUND: 2, Type.ICE: 1,
        Type.NORMAL: 0, Type.POISON: 1, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 2,
    },
    Type.GROUND: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 3,
        Type.FAIRY: 0, Type.FIGHTING: 0, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 1, Type.GROUND: 0, Type.ICE: 1,
        Type.NORMAL: 0, Type.POISON: 2, Type.PSYCHIC: 0, Type.ROCK: 2,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 1,
    },
    Type.ICE: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 1, Type.FIRE: 1, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 2,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 1,
        Type.STEEL: 1, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.NORMAL: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 1, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 3, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.POISON: {
        Type.BUG: 2, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 2, Type.FIGHTING: 2, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 2, Type.GROUND: 1, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 2, Type.PSYCHIC: 1, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.PSYCHIC: {
        Type.BUG: 1, Type.DARK: 1, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 2, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 1, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 2, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.ROCK: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 1, Type.FIRE: 2, Type.FLYING: 2,
        Type.GHOST: 0, Type.GRASS: 1, Type.GROUND: 1, Type.ICE: 0,
        Type.NORMAL: 2, Type.POISON: 2, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 1, Type.STELLAR: 0, Type.WATER: 1,
    },
    Type.STEEL: {
        Type.BUG: 2, Type.DARK: 0, Type.DRAGON: 2, Type.ELECTRIC: 0,
        Type.FAIRY: 2, Type.FIGHTING: 1, Type.FIRE: 1, Type.FLYING: 2,
        Type.GHOST: 0, Type.GRASS: 2, Type.GROUND: 1, Type.ICE: 2,
        Type.NORMAL: 2, Type.POISON: 3, Type.PSYCHIC: 2, Type.ROCK: 2,
        Type.STEEL: 2, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.STELLAR: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 0,
        Type.FAIRY: 0, Type.FIGHTING: 0, Type.FIRE: 0, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 0, Type.GROUND: 0, Type.ICE: 0,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 0, Type.STELLAR: 0, Type.WATER: 0,
    },
    Type.WATER: {
        Type.BUG: 0, Type.DARK: 0, Type.DRAGON: 0, Type.ELECTRIC: 1,
        Type.FAIRY: 0, Type.FIGHTING: 0, Type.FIRE: 2, Type.FLYING: 0,
        Type.GHOST: 0, Type.GRASS: 1, Type.GROUND: 0, Type.ICE: 2,
        Type.NORMAL: 0, Type.POISON: 0, Type.PSYCHIC: 0, Type.ROCK: 0,
        Type.STEEL: 2, Type.STELLAR: 0, Type.WATER: 2,
    },
}

# Effectiveness value to multiplier
EFFECTIVENESS_MULTIPLIER = {
    0: 1.0,   # Normal
    1: 2.0,   # Super effective
    2: 0.5,   # Not very effective
    3: 0.0,   # Immune
}


def get_type_effectiveness(attacking_type: Type, defending_type: Type) -> float:
    """Get the damage multiplier for an attacking type vs defending type.

    Args:
        attacking_type: The type of the attacking move
        defending_type: The type of the defending Pokemon

    Returns:
        Damage multiplier (0.0, 0.5, 1.0, or 2.0)
    """
    effectiveness = TYPE_CHART.get(defending_type, {}).get(attacking_type, 0)
    return EFFECTIVENESS_MULTIPLIER[effectiveness]


def get_dual_type_effectiveness(attacking_type: Type, type1: Type, type2: Type | None) -> float:
    """Get the damage multiplier for an attacking type vs a dual-type Pokemon.

    Args:
        attacking_type: The type of the attacking move
        type1: The first type of the defending Pokemon
        type2: The second type of the defending Pokemon (None if single-typed)

    Returns:
        Combined damage multiplier
    """
    multiplier = get_type_effectiveness(attacking_type, type1)
    if type2 is not None and type2 != type1:
        multiplier *= get_type_effectiveness(attacking_type, type2)
    return multiplier


# String to Type mapping for parsing
TYPE_BY_NAME: Dict[str, Type] = {
    "normal": Type.NORMAL,
    "fire": Type.FIRE,
    "water": Type.WATER,
    "electric": Type.ELECTRIC,
    "grass": Type.GRASS,
    "ice": Type.ICE,
    "fighting": Type.FIGHTING,
    "poison": Type.POISON,
    "ground": Type.GROUND,
    "flying": Type.FLYING,
    "psychic": Type.PSYCHIC,
    "bug": Type.BUG,
    "rock": Type.ROCK,
    "ghost": Type.GHOST,
    "dragon": Type.DRAGON,
    "dark": Type.DARK,
    "steel": Type.STEEL,
    "fairy": Type.FAIRY,
    "stellar": Type.STELLAR,
}
