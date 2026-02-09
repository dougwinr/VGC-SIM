"""Pokemon class and stat calculation functions.

This module provides:
- Stat calculation functions using official Pokemon formulas
- Pokemon class that wraps NumPy arrays for efficient storage
"""
from typing import List, Optional, Tuple, Union, TYPE_CHECKING
import numpy as np

from .layout import (
    POKEMON_ARRAY_SIZE,
    P_SPECIES, P_LEVEL, P_NATURE, P_ABILITY, P_ITEM,
    P_TYPE1, P_TYPE2, P_TERA_TYPE,
    P_STAT_HP, P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_CURRENT_HP, P_STATUS, P_STATUS_COUNTER,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
    P_STAGE_ACC, P_STAGE_EVA,
    P_MOVE1, P_MOVE2, P_MOVE3, P_MOVE4,
    P_PP1, P_PP2, P_PP3, P_PP4,
    P_IV_HP, P_IV_ATK, P_IV_DEF, P_IV_SPA, P_IV_SPD, P_IV_SPE,
    P_EV_HP, P_EV_ATK, P_EV_DEF, P_EV_SPA, P_EV_SPD, P_EV_SPE,
    STATUS_NONE,
    STAT_INDICES, STAGE_INDICES, MOVE_INDICES, PP_INDICES, IV_INDICES, EV_INDICES,
)
from data.natures import get_nature_modifier, Nature, Stat
from data.abilities import get_ability_id

if TYPE_CHECKING:
    from data.species import SpeciesData


# =============================================================================
# Stat Calculation Functions
# =============================================================================

def calculate_hp(base: int, iv: int, ev: int, level: int) -> int:
    """Calculate HP stat using the official Pokemon formula.

    Formula: floor(((2*Base + IV + EV/4) * Level) / 100) + Level + 10

    Special case: Shedinja always has 1 HP regardless of formula.

    Args:
        base: Base HP stat (1-255)
        iv: Individual Value (0-31)
        ev: Effort Value (0-252)
        level: Pokemon level (1-100)

    Returns:
        Calculated HP stat
    """
    # Shedinja special case (base HP of 1)
    if base == 1:
        return 1

    return int(((2 * base + iv + ev // 4) * level) // 100 + level + 10)


def calculate_stat(
    base: int,
    iv: int,
    ev: int,
    level: int,
    nature_multiplier: float = 1.0
) -> int:
    """Calculate a non-HP stat using the official Pokemon formula.

    Formula: floor((floor(((2*Base + IV + EV/4) * Level) / 100) + 5) * Nature)

    Args:
        base: Base stat (1-255)
        iv: Individual Value (0-31)
        ev: Effort Value (0-252)
        level: Pokemon level (1-100)
        nature_multiplier: Nature modifier (0.9, 1.0, or 1.1)

    Returns:
        Calculated stat value
    """
    raw = ((2 * base + iv + ev // 4) * level) // 100 + 5
    return int(raw * nature_multiplier)


def calculate_all_stats(
    base_stats: Tuple[int, int, int, int, int, int],
    ivs: Tuple[int, int, int, int, int, int],
    evs: Tuple[int, int, int, int, int, int],
    level: int,
    nature: Nature,
) -> Tuple[int, int, int, int, int, int]:
    """Calculate all six stats for a Pokemon.

    Args:
        base_stats: Base stats tuple (HP, Atk, Def, SpA, SpD, Spe)
        ivs: IV tuple (HP, Atk, Def, SpA, SpD, Spe)
        evs: EV tuple (HP, Atk, Def, SpA, SpD, Spe)
        level: Pokemon level (1-100)
        nature: Nature enum value

    Returns:
        Tuple of calculated stats (HP, Atk, Def, SpA, SpD, Spe)
    """
    # Calculate HP (no nature modifier)
    hp = calculate_hp(base_stats[0], ivs[0], evs[0], level)

    # Calculate other stats with nature modifiers
    atk = calculate_stat(base_stats[1], ivs[1], evs[1], level, get_nature_modifier(nature, Stat.ATK))
    def_ = calculate_stat(base_stats[2], ivs[2], evs[2], level, get_nature_modifier(nature, Stat.DEF))
    spa = calculate_stat(base_stats[3], ivs[3], evs[3], level, get_nature_modifier(nature, Stat.SPA))
    spd = calculate_stat(base_stats[4], ivs[4], evs[4], level, get_nature_modifier(nature, Stat.SPD))
    spe = calculate_stat(base_stats[5], ivs[5], evs[5], level, get_nature_modifier(nature, Stat.SPE))

    return (hp, atk, def_, spa, spd, spe)


# =============================================================================
# Pokemon Class
# =============================================================================

class Pokemon:
    """A Pokemon instance backed by a packed NumPy array.

    This class provides a high-level interface for Pokemon data while
    storing everything in a dense NumPy array for cache efficiency.

    Attributes:
        data: The underlying NumPy array containing all Pokemon data
    """

    __slots__ = ('data',)

    def __init__(self, data: Optional[np.ndarray] = None):
        """Initialize a Pokemon with optional existing data.

        Args:
            data: Existing NumPy array, or None to create a new one
        """
        if data is not None:
            self.data = data
        else:
            self.data = np.zeros(POKEMON_ARRAY_SIZE, dtype=np.int32)

    @classmethod
    def from_species(
        cls,
        species: 'SpeciesData',
        level: int = 100,
        nature: Nature = Nature.HARDY,
        ability_id: Optional[Union[int, str]] = None,
        item_id: int = 0,
        ivs: Optional[Tuple[int, int, int, int, int, int]] = None,
        evs: Optional[Tuple[int, int, int, int, int, int]] = None,
        moves: Optional[List[int]] = None,
        move_pp: Optional[List[int]] = None,
    ) -> 'Pokemon':
        """Create a Pokemon from species data.

        Args:
            species: SpeciesData for this Pokemon's species
            level: Level 1-100 (default 100)
            nature: Nature enum value (default Hardy/neutral)
            ability_id: Ability ID (int) or name (str), or None to use first ability from species
            item_id: Item ID (0 = no item)
            ivs: IV tuple (default all 31s)
            evs: EV tuple (default all 0s)
            moves: List of move IDs (up to 4)
            move_pp: List of PP values for each move

        Returns:
            New Pokemon instance
        """
        pokemon = cls()

        # Default IVs to perfect (31s)
        if ivs is None:
            ivs = (31, 31, 31, 31, 31, 31)

        # Default EVs to zero
        if evs is None:
            evs = (0, 0, 0, 0, 0, 0)

        # Default ability to first in species list
        if ability_id is None:
            ability_id = species.abilities[0] if species.abilities else 0

        # Convert ability name to ID if string
        if isinstance(ability_id, str):
            resolved_id = get_ability_id(ability_id)
            ability_id = resolved_id if resolved_id is not None else 0

        # Store identity data
        pokemon.data[P_SPECIES] = species.id
        pokemon.data[P_LEVEL] = level
        pokemon.data[P_NATURE] = nature.value
        pokemon.data[P_ABILITY] = ability_id
        pokemon.data[P_ITEM] = item_id

        # Store types
        pokemon.data[P_TYPE1] = species.type1.value
        pokemon.data[P_TYPE2] = species.type2.value if species.type2 else -1
        pokemon.data[P_TERA_TYPE] = -1  # Not terastallized

        # Store IVs
        pokemon.data[P_IV_HP] = ivs[0]
        pokemon.data[P_IV_ATK] = ivs[1]
        pokemon.data[P_IV_DEF] = ivs[2]
        pokemon.data[P_IV_SPA] = ivs[3]
        pokemon.data[P_IV_SPD] = ivs[4]
        pokemon.data[P_IV_SPE] = ivs[5]

        # Store EVs
        pokemon.data[P_EV_HP] = evs[0]
        pokemon.data[P_EV_ATK] = evs[1]
        pokemon.data[P_EV_DEF] = evs[2]
        pokemon.data[P_EV_SPA] = evs[3]
        pokemon.data[P_EV_SPD] = evs[4]
        pokemon.data[P_EV_SPE] = evs[5]

        # Calculate and store stats
        base_stats = species.base_stats.as_tuple()
        stats = calculate_all_stats(base_stats, ivs, evs, level, nature)

        pokemon.data[P_STAT_HP] = stats[0]
        pokemon.data[P_STAT_ATK] = stats[1]
        pokemon.data[P_STAT_DEF] = stats[2]
        pokemon.data[P_STAT_SPA] = stats[3]
        pokemon.data[P_STAT_SPD] = stats[4]
        pokemon.data[P_STAT_SPE] = stats[5]

        # Set current HP to max HP
        pokemon.data[P_CURRENT_HP] = stats[0]

        # Initialize status
        pokemon.data[P_STATUS] = STATUS_NONE
        pokemon.data[P_STATUS_COUNTER] = 0

        # Initialize stat stages to 0 (neutral)
        pokemon.data[P_STAGE_ATK] = 0
        pokemon.data[P_STAGE_DEF] = 0
        pokemon.data[P_STAGE_SPA] = 0
        pokemon.data[P_STAGE_SPD] = 0
        pokemon.data[P_STAGE_SPE] = 0
        pokemon.data[P_STAGE_ACC] = 0
        pokemon.data[P_STAGE_EVA] = 0

        # Store moves
        if moves:
            for i, move_id in enumerate(moves[:4]):
                pokemon.data[P_MOVE1 + i] = move_id
                # Default PP if not provided
                if move_pp and i < len(move_pp):
                    pokemon.data[P_PP1 + i] = move_pp[i]
                else:
                    pokemon.data[P_PP1 + i] = 0  # Will need to look up from move data

        return pokemon

    # -------------------------------------------------------------------------
    # Property accessors for common fields
    # -------------------------------------------------------------------------

    @property
    def species_id(self) -> int:
        """Get the species ID."""
        return int(self.data[P_SPECIES])

    @property
    def level(self) -> int:
        """Get the level."""
        return int(self.data[P_LEVEL])

    @property
    def nature_id(self) -> int:
        """Get the nature ID."""
        return int(self.data[P_NATURE])

    @property
    def ability_id(self) -> int:
        """Get the ability ID."""
        return int(self.data[P_ABILITY])

    @property
    def item_id(self) -> int:
        """Get the held item ID."""
        return int(self.data[P_ITEM])

    @property
    def type1(self) -> int:
        """Get primary type ID."""
        return int(self.data[P_TYPE1])

    @property
    def type2(self) -> int:
        """Get secondary type ID (-1 if single-typed)."""
        return int(self.data[P_TYPE2])

    @property
    def max_hp(self) -> int:
        """Get maximum HP."""
        return int(self.data[P_STAT_HP])

    @property
    def current_hp(self) -> int:
        """Get current HP."""
        return int(self.data[P_CURRENT_HP])

    @current_hp.setter
    def current_hp(self, value: int) -> None:
        """Set current HP (clamped to 0 to max_hp)."""
        self.data[P_CURRENT_HP] = max(0, min(value, self.max_hp))

    @property
    def hp_fraction(self) -> float:
        """Get HP as a fraction of max HP."""
        max_hp = self.max_hp
        if max_hp == 0:
            return 0.0
        return self.current_hp / max_hp

    @property
    def is_fainted(self) -> bool:
        """Check if the Pokemon has fainted."""
        return self.current_hp <= 0

    @property
    def status(self) -> int:
        """Get non-volatile status condition."""
        return int(self.data[P_STATUS])

    @status.setter
    def status(self, value: int) -> None:
        """Set non-volatile status condition."""
        self.data[P_STATUS] = value

    @property
    def status_counter(self) -> int:
        """Get status duration counter."""
        return int(self.data[P_STATUS_COUNTER])

    @status_counter.setter
    def status_counter(self, value: int) -> None:
        """Set status duration counter."""
        self.data[P_STATUS_COUNTER] = value

    # -------------------------------------------------------------------------
    # Stat accessors
    # -------------------------------------------------------------------------

    @property
    def attack(self) -> int:
        """Get Attack stat."""
        return int(self.data[P_STAT_ATK])

    @property
    def defense(self) -> int:
        """Get Defense stat."""
        return int(self.data[P_STAT_DEF])

    @property
    def special_attack(self) -> int:
        """Get Special Attack stat."""
        return int(self.data[P_STAT_SPA])

    @property
    def special_defense(self) -> int:
        """Get Special Defense stat."""
        return int(self.data[P_STAT_SPD])

    @property
    def speed(self) -> int:
        """Get Speed stat."""
        return int(self.data[P_STAT_SPE])

    def get_stat(self, stat_index: int) -> int:
        """Get a stat by index (8-13 for HP through Speed)."""
        return int(self.data[stat_index])

    # -------------------------------------------------------------------------
    # Stage accessors
    # -------------------------------------------------------------------------

    def get_stage(self, stage_index: int) -> int:
        """Get a stat stage by index."""
        return int(self.data[stage_index])

    def set_stage(self, stage_index: int, value: int) -> None:
        """Set a stat stage (clamped to -6 to +6)."""
        self.data[stage_index] = max(-6, min(6, value))

    def modify_stage(self, stage_index: int, delta: int) -> int:
        """Modify a stat stage and return the actual change.

        Args:
            stage_index: The stage index to modify
            delta: Amount to change (+/-)

        Returns:
            Actual change applied (may be less if at bounds)
        """
        old_value = int(self.data[stage_index])
        new_value = max(-6, min(6, old_value + delta))
        self.data[stage_index] = new_value
        return new_value - old_value

    def reset_stages(self) -> None:
        """Reset all stat stages to 0."""
        for idx in STAGE_INDICES:
            self.data[idx] = 0
        self.data[P_STAGE_ACC] = 0
        self.data[P_STAGE_EVA] = 0

    # -------------------------------------------------------------------------
    # Move accessors
    # -------------------------------------------------------------------------

    def get_move(self, slot: int) -> int:
        """Get move ID in slot (0-3)."""
        if 0 <= slot < 4:
            return int(self.data[P_MOVE1 + slot])
        return 0

    def get_pp(self, slot: int) -> int:
        """Get PP for move slot (0-3)."""
        if 0 <= slot < 4:
            return int(self.data[P_PP1 + slot])
        return 0

    def set_pp(self, slot: int, value: int) -> None:
        """Set PP for move slot (0-3)."""
        if 0 <= slot < 4:
            self.data[P_PP1 + slot] = max(0, value)

    def use_pp(self, slot: int, amount: int = 1) -> bool:
        """Use PP from a move slot.

        Args:
            slot: Move slot (0-3)
            amount: PP to use

        Returns:
            True if successful, False if not enough PP
        """
        if 0 <= slot < 4:
            current = int(self.data[P_PP1 + slot])
            if current >= amount:
                self.data[P_PP1 + slot] = current - amount
                return True
        return False

    @property
    def moves(self) -> Tuple[int, int, int, int]:
        """Get all four move IDs."""
        return (
            int(self.data[P_MOVE1]),
            int(self.data[P_MOVE2]),
            int(self.data[P_MOVE3]),
            int(self.data[P_MOVE4]),
        )

    # -------------------------------------------------------------------------
    # IV/EV accessors
    # -------------------------------------------------------------------------

    @property
    def ivs(self) -> Tuple[int, int, int, int, int, int]:
        """Get all IVs as a tuple."""
        return tuple(int(self.data[idx]) for idx in IV_INDICES)

    @property
    def evs(self) -> Tuple[int, int, int, int, int, int]:
        """Get all EVs as a tuple."""
        return tuple(int(self.data[idx]) for idx in EV_INDICES)

    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------

    def take_damage(self, amount: int) -> int:
        """Apply damage to the Pokemon.

        Args:
            amount: Damage to deal (positive number)

        Returns:
            Actual damage dealt (may be less if would overkill)
        """
        if amount <= 0:
            return 0

        old_hp = self.current_hp
        self.current_hp = old_hp - amount
        return old_hp - self.current_hp

    def heal(self, amount: int) -> int:
        """Heal the Pokemon.

        Args:
            amount: HP to restore (positive number)

        Returns:
            Actual HP restored
        """
        if amount <= 0:
            return 0

        old_hp = self.current_hp
        self.current_hp = old_hp + amount
        return self.current_hp - old_hp

    def copy(self) -> 'Pokemon':
        """Create a copy of this Pokemon."""
        return Pokemon(self.data.copy())

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Pokemon(species={self.species_id}, lv={self.level}, "
            f"hp={self.current_hp}/{self.max_hp})"
        )
