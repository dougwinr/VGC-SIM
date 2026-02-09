"""Pokemon natures and stat modifiers.

Natures affect 5 stats (Attack, Defense, Special Attack, Special Defense, Speed).
HP is never affected by nature.

Each nature has:
- A boosted stat (+10%, 1.1x multiplier)
- A hindered stat (-10%, 0.9x multiplier)
- 5 natures are "neutral" (same stat boosted and hindered, resulting in 1x)
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional, Tuple


class Stat(IntEnum):
    """Stats that can be affected by natures."""
    HP = 0       # Never modified by nature
    ATK = 1      # Attack
    DEF = 2      # Defense
    SPA = 3      # Special Attack
    SPD = 4      # Special Defense
    SPE = 5      # Speed


class Nature(IntEnum):
    """All 25 Pokemon natures as integer IDs."""
    # Neutral natures (no effect)
    HARDY = 0     # Atk/Atk
    DOCILE = 1    # Def/Def
    SERIOUS = 2   # Spe/Spe
    BASHFUL = 3   # SpA/SpA
    QUIRKY = 4    # SpD/SpD

    # Attack boosting
    LONELY = 5    # +Atk, -Def
    BRAVE = 6     # +Atk, -Spe
    ADAMANT = 7   # +Atk, -SpA
    NAUGHTY = 8   # +Atk, -SpD

    # Defense boosting
    BOLD = 9      # +Def, -Atk
    RELAXED = 10  # +Def, -Spe
    IMPISH = 11   # +Def, -SpA
    LAX = 12      # +Def, -SpD

    # Special Attack boosting
    MODEST = 13   # +SpA, -Atk
    MILD = 14     # +SpA, -Def
    QUIET = 15    # +SpA, -Spe
    RASH = 16     # +SpA, -SpD

    # Special Defense boosting
    CALM = 17     # +SpD, -Atk
    GENTLE = 18   # +SpD, -Def
    SASSY = 19    # +SpD, -Spe
    CAREFUL = 20  # +SpD, -SpA

    # Speed boosting
    TIMID = 21    # +Spe, -Atk
    HASTY = 22    # +Spe, -Def
    JOLLY = 23    # +Spe, -SpA
    NAIVE = 24    # +Spe, -SpD


@dataclass(frozen=True)
class NatureData:
    """Data about a nature's stat modifications."""
    name: str
    boosted: Stat      # Stat increased by 10%
    hindered: Stat     # Stat decreased by 10%

    @property
    def is_neutral(self) -> bool:
        """Returns True if this nature has no net effect."""
        return self.boosted == self.hindered


# Nature definitions: (boosted_stat, hindered_stat)
NATURE_DATA: Dict[Nature, NatureData] = {
    # Neutral natures
    Nature.HARDY: NatureData("Hardy", Stat.ATK, Stat.ATK),
    Nature.DOCILE: NatureData("Docile", Stat.DEF, Stat.DEF),
    Nature.SERIOUS: NatureData("Serious", Stat.SPE, Stat.SPE),
    Nature.BASHFUL: NatureData("Bashful", Stat.SPA, Stat.SPA),
    Nature.QUIRKY: NatureData("Quirky", Stat.SPD, Stat.SPD),

    # Attack boosting
    Nature.LONELY: NatureData("Lonely", Stat.ATK, Stat.DEF),
    Nature.BRAVE: NatureData("Brave", Stat.ATK, Stat.SPE),
    Nature.ADAMANT: NatureData("Adamant", Stat.ATK, Stat.SPA),
    Nature.NAUGHTY: NatureData("Naughty", Stat.ATK, Stat.SPD),

    # Defense boosting
    Nature.BOLD: NatureData("Bold", Stat.DEF, Stat.ATK),
    Nature.RELAXED: NatureData("Relaxed", Stat.DEF, Stat.SPE),
    Nature.IMPISH: NatureData("Impish", Stat.DEF, Stat.SPA),
    Nature.LAX: NatureData("Lax", Stat.DEF, Stat.SPD),

    # Special Attack boosting
    Nature.MODEST: NatureData("Modest", Stat.SPA, Stat.ATK),
    Nature.MILD: NatureData("Mild", Stat.SPA, Stat.DEF),
    Nature.QUIET: NatureData("Quiet", Stat.SPA, Stat.SPE),
    Nature.RASH: NatureData("Rash", Stat.SPA, Stat.SPD),

    # Special Defense boosting
    Nature.CALM: NatureData("Calm", Stat.SPD, Stat.ATK),
    Nature.GENTLE: NatureData("Gentle", Stat.SPD, Stat.DEF),
    Nature.SASSY: NatureData("Sassy", Stat.SPD, Stat.SPE),
    Nature.CAREFUL: NatureData("Careful", Stat.SPD, Stat.SPA),

    # Speed boosting
    Nature.TIMID: NatureData("Timid", Stat.SPE, Stat.ATK),
    Nature.HASTY: NatureData("Hasty", Stat.SPE, Stat.DEF),
    Nature.JOLLY: NatureData("Jolly", Stat.SPE, Stat.SPA),
    Nature.NAIVE: NatureData("Naive", Stat.SPE, Stat.SPD),
}


def get_nature_modifier(nature: Nature, stat: Stat) -> float:
    """Get the stat modifier for a given nature and stat.

    Args:
        nature: The Pokemon's nature
        stat: The stat to get the modifier for

    Returns:
        1.1 if boosted, 0.9 if hindered, 1.0 otherwise
    """
    if stat == Stat.HP:
        return 1.0

    data = NATURE_DATA[nature]
    if data.boosted == stat and data.hindered != stat:
        return 1.1
    elif data.hindered == stat and data.boosted != stat:
        return 0.9
    return 1.0


def get_nature_modifiers(nature: Nature) -> Dict[Stat, float]:
    """Get all stat modifiers for a nature.

    Args:
        nature: The Pokemon's nature

    Returns:
        Dictionary mapping each stat to its modifier
    """
    return {
        stat: get_nature_modifier(nature, stat)
        for stat in Stat
    }


# String to Nature mapping for parsing
NATURE_BY_NAME: Dict[str, Nature] = {
    data.name.lower(): nature
    for nature, data in NATURE_DATA.items()
}
