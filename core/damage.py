"""Damage calculation formula for Pokemon battles.

This module implements the damage formula as specified in Pokemon games,
following the same calculation order as Pokemon Showdown.

Key formula (Gen 5+):
    Base damage = ((2 * Level / 5 + 2) * Power * A / D) / 50 + 2

Then apply modifiers:
    - Spread modifier (0.75 for multi-target in doubles)
    - Weather modifier
    - Critical hit (1.5x in Gen 6+, 2x in earlier gens)
    - Random factor (0.85-1.0)
    - STAB (1.5x, 2x with Adaptability)
    - Type effectiveness
    - Burn (0.5x for physical moves unless Guts)
    - Final modifiers (items, abilities)
"""
from dataclasses import dataclass
from typing import Optional, Tuple, TYPE_CHECKING

from .layout import (
    P_LEVEL, P_TYPE1, P_TYPE2, P_TERA_TYPE,
    P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD,
    P_STATUS, P_VOL_FOCUS_ENERGY,
    STATUS_BURN,
    STAGE_MULTIPLIERS,
)
from .pokemon import Pokemon
from data.types import Type, get_type_effectiveness, get_dual_type_effectiveness
from data.moves import MoveData, MoveCategory

if TYPE_CHECKING:
    from .battle_state import BattleState


# =============================================================================
# Damage Result
# =============================================================================

@dataclass
class DamageResult:
    """Result of a damage calculation.

    Attributes:
        damage: Final damage amount
        crit: Whether the hit was a critical hit
        type_effectiveness: Type effectiveness multiplier
        is_immune: Whether target is immune (0x multiplier)
        random_factor: The random factor applied (0.85-1.0)
    """
    damage: int
    crit: bool = False
    type_effectiveness: float = 1.0
    is_immune: bool = False
    random_factor: float = 1.0


# =============================================================================
# Utility Functions
# =============================================================================

def trunc(value: float, bits: int = 32) -> int:
    """Truncate a value to integer, optionally limiting bit width.

    Pokemon Showdown uses this for integer truncation in damage calculation.

    Args:
        value: Value to truncate
        bits: Maximum bit width (16 or 32)

    Returns:
        Truncated integer value
    """
    result = int(value)
    if bits == 16:
        result = result & 0xFFFF
    return result


def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp an integer to a range.

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def get_stat_with_stage(base_stat: int, stage: int) -> int:
    """Calculate stat value with stage modifier applied.

    Args:
        base_stat: Base stat value
        stage: Stage modifier (-6 to +6)

    Returns:
        Modified stat value
    """
    stage = clamp(stage, -6, 6)
    num, denom = STAGE_MULTIPLIERS[stage + 6]
    return trunc(base_stat * num / denom)


def apply_modifier(value: int, modifier: float) -> int:
    """Apply a modifier to a value using Pokemon rounding.

    Pokemon uses "round half to even" (banker's rounding) for some calculations,
    but damage calculations typically use truncation with a special rule.

    Args:
        value: Base value
        modifier: Modifier to apply

    Returns:
        Modified value
    """
    # Standard Pokemon modifier application: multiply, then round down
    # but if result would be 0 and modifier > 0, return 1
    result = trunc(value * modifier)
    if result == 0 and value > 0 and modifier > 0:
        result = 1
    return result


# =============================================================================
# Critical Hit Calculation
# =============================================================================

# Critical hit rate by stage (Gen 6+)
# Stage 0: 1/24, Stage 1: 1/8, Stage 2: 1/2, Stage 3+: 1/1
CRIT_MULTIPLIERS_GEN6 = [24, 8, 2, 1, 1]

# Critical hit rate by stage (Gen 2-5)
CRIT_MULTIPLIERS_GEN5 = [16, 8, 4, 3, 2, 1]


def get_crit_chance(crit_stage: int, gen: int = 9) -> Tuple[int, int]:
    """Get critical hit chance as a fraction.

    Args:
        crit_stage: Critical hit stage (0-4)
        gen: Generation for formula differences

    Returns:
        Tuple of (numerator, denominator) for random chance
    """
    if gen >= 6:
        crit_stage = clamp(crit_stage, 0, 4)
        denom = CRIT_MULTIPLIERS_GEN6[crit_stage]
    else:
        crit_stage = clamp(crit_stage, 0, 5)
        denom = CRIT_MULTIPLIERS_GEN5[crit_stage]

    return (1, denom)


def calculate_crit_stage(
    pokemon: Pokemon,
    move: MoveData,
    ability_stage: int = 0,
    item_stage: int = 0,
) -> int:
    """Calculate the critical hit stage for an attack.

    Args:
        pokemon: Attacking Pokemon
        move: Move being used
        ability_stage: Additional crit stage from ability (e.g., Super Luck)
        item_stage: Additional crit stage from item (e.g., Scope Lens)

    Returns:
        Critical hit stage (0-4)
    """
    stage = 0

    # Move's crit ratio (1 = normal, 2+ = high crit)
    if move.crit_ratio >= 2:
        stage += move.crit_ratio - 1

    # Focus Energy adds 2 stages
    if pokemon.data[P_VOL_FOCUS_ENERGY] > 0:
        stage += 2

    # Ability and item bonuses
    stage += ability_stage
    stage += item_stage

    return clamp(stage, 0, 4)


# =============================================================================
# Type Effectiveness
# =============================================================================

def calculate_type_effectiveness(
    move_type: Type,
    defender_type1: int,
    defender_type2: int,
    defender_tera_type: int = -1,
) -> float:
    """Calculate type effectiveness multiplier.

    Args:
        move_type: Type of the attacking move
        defender_type1: Defender's primary type ID
        defender_type2: Defender's secondary type ID (-1 if single-typed)
        defender_tera_type: Defender's Tera type ID (-1 if not terastallized)

    Returns:
        Type effectiveness multiplier (0.0, 0.25, 0.5, 1.0, 2.0, or 4.0)
    """
    # If terastallized, use only tera type
    if defender_tera_type >= 0:
        tera_type = Type(defender_tera_type)
        return get_type_effectiveness(move_type, tera_type)

    # Otherwise use both types
    type1 = Type(defender_type1)
    type2 = Type(defender_type2) if defender_type2 >= 0 else None

    return get_dual_type_effectiveness(move_type, type1, type2)


# =============================================================================
# STAB Calculation
# =============================================================================

def has_stab(
    move_type: Type,
    attacker_type1: int,
    attacker_type2: int,
    attacker_tera_type: int = -1,
) -> bool:
    """Check if move gets Same-Type Attack Bonus.

    Args:
        move_type: Type of the move
        attacker_type1: Attacker's primary type ID
        attacker_type2: Attacker's secondary type ID
        attacker_tera_type: Attacker's Tera type ID

    Returns:
        True if move gets STAB
    """
    move_type_id = move_type.value

    # Check base types
    if attacker_type1 == move_type_id or attacker_type2 == move_type_id:
        return True

    # Check tera type (gives STAB for tera type)
    if attacker_tera_type >= 0 and attacker_tera_type == move_type_id:
        return True

    return False


def get_stab_modifier(
    move_type: Type,
    attacker_type1: int,
    attacker_type2: int,
    attacker_tera_type: int = -1,
    has_adaptability: bool = False,
) -> float:
    """Get STAB multiplier for a move.

    Args:
        move_type: Type of the move
        attacker_type1: Attacker's primary type ID
        attacker_type2: Attacker's secondary type ID
        attacker_tera_type: Attacker's Tera type ID
        has_adaptability: Whether attacker has Adaptability ability

    Returns:
        STAB multiplier (1.0, 1.5, or 2.0)
    """
    if not has_stab(move_type, attacker_type1, attacker_type2, attacker_tera_type):
        return 1.0

    # Adaptability boosts STAB to 2x
    if has_adaptability:
        return 2.0

    # Tera STAB when matching base type is 2x
    move_type_id = move_type.value
    if attacker_tera_type >= 0 and attacker_tera_type == move_type_id:
        # Check if it also matches a base type
        if attacker_type1 == move_type_id or attacker_type2 == move_type_id:
            return 2.0

    return 1.5


# Stellar Tera type constant (Type 19 in modern games)
TERA_STELLAR = 19


def get_stellar_tera_modifier(
    move_type: Type,
    attacker_type1: int,
    attacker_type2: int,
    attacker_tera_type: int,
    stellar_used_types: Optional[set] = None,
) -> float:
    """Get Stellar Tera type modifier for a move.

    Stellar Tera type gives a 1.2x (4915/4096) boost for non-STAB moves
    the first time each type is used.

    Args:
        move_type: Type of the move
        attacker_type1: Attacker's primary type ID
        attacker_type2: Attacker's secondary type ID
        attacker_tera_type: Attacker's Tera type ID
        stellar_used_types: Set of types already boosted by Stellar

    Returns:
        Stellar modifier (1.0 or ~1.2)
    """
    if attacker_tera_type != TERA_STELLAR:
        return 1.0

    move_type_id = move_type.value

    # Check if already used this type's stellar boost
    if stellar_used_types is not None and move_type_id in stellar_used_types:
        return 1.0

    # STAB types get 2.0x boost instead of stellar
    if attacker_type1 == move_type_id or attacker_type2 == move_type_id:
        return 2.0

    # Non-STAB types get 4915/4096 ≈ 1.2x boost
    return 4915 / 4096


def get_tera_power_boost(
    base_power: int,
    move_type: Type,
    attacker_tera_type: int,
) -> int:
    """Get Tera-boosted base power for low BP moves.

    When Terastallized and using a move matching Tera type,
    moves with base power below 60 are boosted to 60.

    Args:
        base_power: Original base power
        move_type: Type of the move
        attacker_tera_type: Attacker's Tera type ID

    Returns:
        Potentially boosted base power
    """
    if attacker_tera_type < 0:
        return base_power

    # Stellar type doesn't get this boost
    if attacker_tera_type == TERA_STELLAR:
        return base_power

    # Must match Tera type
    if move_type.value != attacker_tera_type:
        return base_power

    # Boost low BP moves to 60
    if base_power > 0 and base_power < 60:
        return 60

    return base_power


# =============================================================================
# Weather Modifiers
# =============================================================================

# Weather IDs (imported from battle_state)
WEATHER_NONE = 0
WEATHER_SUN = 1
WEATHER_RAIN = 2
WEATHER_SAND = 3
WEATHER_HAIL = 4
WEATHER_SNOW = 5

# Terrain IDs
TERRAIN_NONE = 0
TERRAIN_ELECTRIC = 1
TERRAIN_GRASSY = 2
TERRAIN_MISTY = 3
TERRAIN_PSYCHIC = 4


def get_weather_modifier(weather: int, move_type: Type) -> float:
    """Get weather damage modifier for a move type.

    Args:
        weather: Current weather ID
        move_type: Type of the move

    Returns:
        Weather modifier (0.5, 1.0, or 1.5)
    """
    if weather == WEATHER_SUN:
        if move_type == Type.FIRE:
            return 1.5
        elif move_type == Type.WATER:
            return 0.5
    elif weather == WEATHER_RAIN:
        if move_type == Type.WATER:
            return 1.5
        elif move_type == Type.FIRE:
            return 0.5

    return 1.0


def get_terrain_modifier(
    terrain: int,
    move_type: Type,
    attacker_grounded: bool = True,
    defender_grounded: bool = True,
    move_name: str = '',
) -> float:
    """Get terrain damage modifier for a move.

    Args:
        terrain: Current terrain ID
        move_type: Type of the move
        attacker_grounded: Whether the attacker is grounded
        defender_grounded: Whether the defender is grounded
        move_name: Name of the move (for specific move checks)

    Returns:
        Terrain modifier (0.5, 1.0, or 1.3)
    """
    if terrain == TERRAIN_ELECTRIC and attacker_grounded:
        if move_type == Type.ELECTRIC:
            return 1.3  # 1.5 in Gen 7, 1.3 in Gen 8+
    elif terrain == TERRAIN_GRASSY:
        if attacker_grounded and move_type == Type.GRASS:
            return 1.3
        # Grassy Terrain weakens Earthquake, Bulldoze, and Magnitude
        if defender_grounded:
            move_lower = move_name.lower().replace(' ', '').replace('-', '')
            if move_lower in ('earthquake', 'bulldoze', 'magnitude'):
                return 0.5
    elif terrain == TERRAIN_PSYCHIC and attacker_grounded:
        if move_type == Type.PSYCHIC:
            return 1.3
    elif terrain == TERRAIN_MISTY and defender_grounded:
        if move_type == Type.DRAGON:
            return 0.5

    return 1.0


# Moves affected by Grassy Terrain damage reduction
GRASSY_TERRAIN_WEAK_MOVES = {'earthquake', 'bulldoze', 'magnitude'}


def is_grounded(pokemon_types: Tuple[int, int], has_levitate: bool = False,
                has_air_balloon: bool = False, is_magnet_rise: bool = False,
                is_telekinesis: bool = False, gravity_active: bool = False,
                has_iron_ball: bool = False, is_ingrain: bool = False,
                is_smack_down: bool = False) -> bool:
    """Check if a Pokemon is grounded (affected by terrain).

    Args:
        pokemon_types: Tuple of (type1_id, type2_id)
        has_levitate: Whether the Pokemon has Levitate ability
        has_air_balloon: Whether the Pokemon is holding Air Balloon
        is_magnet_rise: Whether Magnet Rise is active
        is_telekinesis: Whether Telekinesis is active
        gravity_active: Whether Gravity is active on the field
        has_iron_ball: Whether the Pokemon is holding Iron Ball
        is_ingrain: Whether Ingrain is active
        is_smack_down: Whether Smack Down/Thousand Arrows was used

    Returns:
        True if grounded, False if not grounded
    """
    # These effects always ground the Pokemon
    if gravity_active or has_iron_ball or is_ingrain or is_smack_down:
        return True

    # Flying type is not grounded
    if pokemon_types[0] == Type.FLYING.value or pokemon_types[1] == Type.FLYING.value:
        return False

    # Levitate makes Pokemon not grounded
    if has_levitate:
        return False

    # Air Balloon makes Pokemon not grounded
    if has_air_balloon:
        return False

    # Magnet Rise makes Pokemon not grounded
    if is_magnet_rise:
        return False

    # Telekinesis makes Pokemon not grounded
    if is_telekinesis:
        return False

    return True


# =============================================================================
# Accuracy Calculation
# =============================================================================

# Accuracy stage multipliers (stage -6 to +6)
# Stage 0 is index 6
ACC_STAGE_MULTIPLIERS = [
    (3, 9),   # -6: 3/9 = 33%
    (3, 8),   # -5: 3/8 = 37.5%
    (3, 7),   # -4: 3/7 = 43%
    (3, 6),   # -3: 3/6 = 50%
    (3, 5),   # -2: 3/5 = 60%
    (3, 4),   # -1: 3/4 = 75%
    (3, 3),   #  0: 3/3 = 100%
    (4, 3),   # +1: 4/3 = 133%
    (5, 3),   # +2: 5/3 = 167%
    (6, 3),   # +3: 6/3 = 200%
    (7, 3),   # +4: 7/3 = 233%
    (8, 3),   # +5: 8/3 = 267%
    (9, 3),   # +6: 9/3 = 300%
]


def calculate_accuracy(
    base_accuracy: int,
    acc_stage: int = 0,
    eva_stage: int = 0,
) -> int:
    """Calculate final accuracy after stage modifiers.

    Args:
        base_accuracy: Move's base accuracy (0-100, or 0 for always-hit)
        acc_stage: Attacker's accuracy stage (-6 to +6)
        eva_stage: Defender's evasion stage (-6 to +6)

    Returns:
        Final accuracy value (0-100+)
    """
    if base_accuracy == 0:  # Always-hit moves
        return 100

    # Combine stages: effective = accuracy - evasion
    effective_stage = clamp(acc_stage - eva_stage, -6, 6)

    num, denom = ACC_STAGE_MULTIPLIERS[effective_stage + 6]
    return trunc(base_accuracy * num / denom)


def check_accuracy(
    base_accuracy: int,
    acc_stage: int,
    eva_stage: int,
    random_roll: int,
) -> bool:
    """Check if an attack hits based on accuracy.

    Args:
        base_accuracy: Move's base accuracy
        acc_stage: Attacker's accuracy stage
        eva_stage: Defender's evasion stage
        random_roll: Random value from 0-99

    Returns:
        True if the attack hits
    """
    if base_accuracy == 0:  # Always-hit moves
        return True

    final_accuracy = calculate_accuracy(base_accuracy, acc_stage, eva_stage)
    return random_roll < final_accuracy


# =============================================================================
# Fixed Damage Moves
# =============================================================================

def calculate_fixed_damage(
    move_name: str,
    attacker_level: int,
    attacker_hp: int,
    attacker_max_hp: int,
    target_hp: int,
    target_max_hp: int,
) -> int:
    """Calculate damage for fixed-damage moves.

    Args:
        move_name: Name of the move (lowercase)
        attacker_level: Attacker's level
        attacker_hp: Attacker's current HP
        attacker_max_hp: Attacker's max HP
        target_hp: Target's current HP
        target_max_hp: Target's max HP

    Returns:
        Fixed damage amount
    """
    move_lower = move_name.lower().replace(' ', '').replace('-', '').replace("'", '')

    # Level-based damage
    if move_lower in ('seismictoss', 'nightshade'):
        return attacker_level

    # Flat damage
    if move_lower == 'sonicboom':
        return 20
    if move_lower == 'dragonrage':
        return 40

    # HP-based damage
    if move_lower == 'superfang':
        return max(1, target_hp // 2)
    if move_lower == 'naturesmadness':
        return max(1, target_hp // 2)

    # Counter/Mirror Coat handled elsewhere (based on last_damage)

    # Endeavor
    if move_lower == 'endeavor':
        if target_hp > attacker_hp:
            return target_hp - attacker_hp
        return 0

    # Final Gambit
    if move_lower == 'finalgambit':
        return attacker_hp

    # Psywave (Gen 1-4 random damage)
    # Handled in calculate_damage with random

    return 0


def is_ohko_move(move_name: str) -> bool:
    """Check if a move is a one-hit KO move.

    Args:
        move_name: Name of the move

    Returns:
        True if it's an OHKO move
    """
    move_lower = move_name.lower().replace(' ', '').replace('-', '')
    return move_lower in ('fissure', 'guillotine', 'horndrill', 'sheercold')


def calculate_ohko_accuracy(
    attacker_level: int,
    target_level: int,
    is_ice_type_user: bool = False,
    move_name: str = '',
) -> int:
    """Calculate accuracy for OHKO moves.

    OHKO moves have base 30% accuracy + (attacker level - target level)%.
    Sheer Cold has 20% accuracy if used by a non-Ice type in Gen 7+.

    Args:
        attacker_level: Attacker's level
        target_level: Target's level
        is_ice_type_user: Whether the attacker is Ice-type
        move_name: Name of the move

    Returns:
        OHKO accuracy (0 if target is higher level)
    """
    if target_level > attacker_level:
        return 0

    base_acc = 30
    if move_name.lower().replace(' ', '') == 'sheercold' and not is_ice_type_user:
        base_acc = 20

    return base_acc + (attacker_level - target_level)


# =============================================================================
# Multi-Hit Move Support
# =============================================================================

MULTI_HIT_DISTRIBUTION = [
    # Gen 5+: 35% for 2-3 hits, 15% for 4-5 hits
    # 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 5, 5, 5
    2, 2, 2, 2, 2, 2, 2,  # 35%
    3, 3, 3, 3, 3, 3, 3,  # 35%
    4, 4, 4,              # 15%
    5, 5, 5,              # 15%
]


def get_multi_hit_count(
    random_index: int,
    has_skill_link: bool = False,
    has_loaded_dice: bool = False,
) -> int:
    """Get the number of hits for a multi-hit move.

    Args:
        random_index: Random index (0-19)
        has_skill_link: Whether the attacker has Skill Link
        has_loaded_dice: Whether the attacker has Loaded Dice

    Returns:
        Number of hits (2-5)
    """
    if has_skill_link:
        return 5

    hits = MULTI_HIT_DISTRIBUTION[random_index % len(MULTI_HIT_DISTRIBUTION)]

    if has_loaded_dice and hits < 4:
        # Loaded Dice guarantees 4-5 hits
        return 4 + (random_index % 2)

    return hits


def get_parental_bond_modifier(hit_number: int, gen: int = 9) -> float:
    """Get the Parental Bond modifier for a hit.

    Args:
        hit_number: Which hit (1 or 2)
        gen: Generation (affects second hit damage)

    Returns:
        Damage modifier for this hit
    """
    if hit_number == 1:
        return 1.0

    # Second hit is weaker
    if gen <= 6:
        return 0.5
    else:
        return 0.25


def get_spread_modifier(
    game_type: str = 'doubles',
    num_targets: int = 2,
) -> float:
    """Get spread move damage modifier.

    Args:
        game_type: Battle format ('singles', 'doubles', 'triples', 'ffa')
        num_targets: Number of targets being hit

    Returns:
        Spread modifier (1.0, 0.75, or 0.5)
    """
    if num_targets <= 1:
        return 1.0

    # Free-for-all uses 0.5x spread modifier
    if game_type == 'ffa':
        return 0.5

    # Standard doubles/triples uses 0.75x
    return 0.75


def get_broken_protect_modifier(
    is_z_move: bool = False,
    is_max_move: bool = False,
) -> float:
    """Get the damage modifier when breaking through Protect.

    Z-Moves and Max Moves deal reduced damage through Protect.

    Args:
        is_z_move: Whether this is a Z-Move
        is_max_move: Whether this is a Max Move (Dynamax)

    Returns:
        Modifier for broken protect damage (1.0 or 0.25)
    """
    if is_z_move or is_max_move:
        return 0.25
    return 1.0


def get_explosion_defense_modifier(
    move_name: str,
    gen: int = 9,
) -> float:
    """Get defense modifier for Explosion/Self-Destruct.

    In Gen 1-4, Explosion and Self-Destruct halved the target's defense.

    Args:
        move_name: Name of the move
        gen: Generation number

    Returns:
        Defense modifier (1.0 or 2.0 for effectively halving defense)
    """
    if gen >= 5:
        return 1.0

    move_lower = move_name.lower().replace(' ', '').replace('-', '')
    if move_lower in ('explosion', 'selfdestruct'):
        return 2.0  # Attacker's attack effectively doubled (defense halved)

    return 1.0


def calculate_minimum_damage(base_damage: int, gen: int = 9) -> int:
    """Apply generation-specific minimum damage rules.

    Args:
        base_damage: Calculated damage before minimum
        gen: Generation number

    Returns:
        Damage with minimum applied
    """
    if gen <= 4:
        # Gen 1-4: minimum damage is 1 after all modifiers
        return max(1, base_damage)

    # Gen 5+: minimum damage is 1
    return max(1, base_damage)


# =============================================================================
# Main Damage Calculation
# =============================================================================

def calculate_base_damage(
    level: int,
    power: int,
    attack: int,
    defense: int,
) -> int:
    """Calculate base damage before modifiers.

    Formula: floor(floor(floor(floor(2 * level / 5 + 2) * power * attack) / defense) / 50) + 2

    Args:
        level: Attacker's level
        power: Move's base power
        attack: Attacker's relevant attack stat
        defense: Defender's relevant defense stat

    Returns:
        Base damage value
    """
    # Ensure minimum values
    level = max(1, level)
    power = max(1, power)
    attack = max(1, attack)
    defense = max(1, defense)

    # Calculate using Pokemon's truncation order
    damage = trunc(2 * level / 5 + 2)
    damage = trunc(damage * power * attack)
    damage = trunc(damage / defense)
    damage = trunc(damage / 50)
    damage += 2

    return damage


def calculate_damage(
    attacker: Pokemon,
    defender: Pokemon,
    move: MoveData,
    state: Optional['BattleState'] = None,
    force_crit: Optional[bool] = None,
    force_random: Optional[float] = None,
    is_spread: bool = False,
) -> DamageResult:
    """Calculate damage for an attack.

    Args:
        attacker: Attacking Pokemon
        defender: Defending Pokemon
        move: Move being used
        state: Battle state (for weather, terrain, etc.)
        force_crit: Force critical hit (True/False) or use random (None)
        force_random: Force random factor (0.85-1.0) or use random (None)
        is_spread: Whether this is a spread move hitting multiple targets

    Returns:
        DamageResult with final damage and hit details
    """
    # Status moves do no damage
    if move.category == MoveCategory.STATUS:
        return DamageResult(damage=0)

    # Get basic stats
    level = attacker.data[P_LEVEL]
    power = move.base_power

    # Zero power moves do no damage
    if power <= 0:
        return DamageResult(damage=0)

    # Determine which stats to use
    is_physical = move.category == MoveCategory.PHYSICAL

    if is_physical:
        attack_stat = attacker.data[P_STAT_ATK]
        attack_stage = attacker.data[P_STAGE_ATK]
        defense_stat = defender.data[P_STAT_DEF]
        defense_stage = defender.data[P_STAGE_DEF]
    else:
        attack_stat = attacker.data[P_STAT_SPA]
        attack_stage = attacker.data[P_STAGE_SPA]
        defense_stat = defender.data[P_STAT_SPD]
        defense_stage = defender.data[P_STAGE_SPD]

    # Calculate critical hit
    crit = False
    if force_crit is not None:
        crit = force_crit
    elif state is not None:
        crit_stage = calculate_crit_stage(attacker, move)
        num, denom = get_crit_chance(crit_stage)
        crit = state.prng.random_chance(num, denom)

    # On critical hit, ignore negative attack stages and positive defense stages
    if crit:
        if attack_stage < 0:
            attack_stage = 0
        if defense_stage > 0:
            defense_stage = 0

    # Apply stage modifiers to stats
    attack = get_stat_with_stage(attack_stat, attack_stage)
    defense = get_stat_with_stage(defense_stat, defense_stage)

    # Ensure minimum values
    attack = max(1, attack)
    defense = max(1, defense)

    # Calculate base damage
    base_damage = calculate_base_damage(level, power, attack, defense)

    # Apply spread modifier (0.75 for multi-target moves)
    if is_spread:
        base_damage = apply_modifier(base_damage, 0.75)

    # Apply weather modifier
    weather = state.weather if state else WEATHER_NONE
    weather_mod = get_weather_modifier(weather, move.type)
    if weather_mod != 1.0:
        base_damage = apply_modifier(base_damage, weather_mod)

    # Apply critical hit modifier (1.5x in Gen 6+)
    if crit:
        base_damage = apply_modifier(base_damage, 1.5)

    # Apply random factor (0.85-1.0)
    if force_random is not None:
        random_factor = force_random
    elif state is not None:
        # Random value from 85 to 100
        random_roll = state.prng.random(85, 100)
        random_factor = random_roll / 100.0
    else:
        random_factor = 1.0

    base_damage = trunc(base_damage * random_factor)

    # Apply STAB
    stab_mod = get_stab_modifier(
        move.type,
        attacker.data[P_TYPE1],
        attacker.data[P_TYPE2],
        attacker.data[P_TERA_TYPE],
    )
    if stab_mod != 1.0:
        base_damage = apply_modifier(base_damage, stab_mod)

    # Calculate type effectiveness
    type_eff = calculate_type_effectiveness(
        move.type,
        defender.data[P_TYPE1],
        defender.data[P_TYPE2],
        defender.data[P_TERA_TYPE],
    )

    # Check immunity
    if type_eff == 0.0:
        return DamageResult(
            damage=0,
            crit=crit,
            type_effectiveness=0.0,
            is_immune=True,
            random_factor=random_factor,
        )

    # Apply type effectiveness
    if type_eff >= 2.0:
        # Super effective: multiply for each 2x
        multiplier = type_eff
        while multiplier >= 2.0:
            base_damage *= 2
            multiplier /= 2.0
    elif type_eff <= 0.5:
        # Not very effective: divide for each 0.5x
        multiplier = type_eff
        while multiplier <= 0.5:
            base_damage = trunc(base_damage / 2)
            multiplier *= 2.0

    # Apply burn penalty for physical moves
    # Note: Facade ignores burn penalty in Gen 6+
    is_facade = move.name.lower() == 'facade'
    gen = state.gen if state and hasattr(state, 'gen') else 9
    if is_physical and attacker.data[P_STATUS] == STATUS_BURN:
        # Facade ignores burn penalty in Gen 6+
        # TODO: Check for Guts ability
        if not (is_facade and gen >= 6):
            base_damage = apply_modifier(base_damage, 0.5)

    # Ensure minimum damage of 1
    final_damage = max(1, base_damage)

    return DamageResult(
        damage=final_damage,
        crit=crit,
        type_effectiveness=type_eff,
        is_immune=False,
        random_factor=random_factor,
    )


def calculate_confusion_damage(pokemon: Pokemon, base_power: int = 40) -> int:
    """Calculate confusion self-hit damage.

    Confusion damage uses a simplified formula without most modifiers.

    Args:
        pokemon: Pokemon hitting itself
        base_power: Base power (40 in Gen 7+)

    Returns:
        Confusion damage
    """
    level = pokemon.data[P_LEVEL]

    # Use physical stats with stages
    attack = get_stat_with_stage(
        pokemon.data[P_STAT_ATK],
        pokemon.data[P_STAGE_ATK]
    )
    defense = get_stat_with_stage(
        pokemon.data[P_STAT_DEF],
        pokemon.data[P_STAGE_DEF]
    )

    # Calculate base damage (16-bit context)
    base_damage = calculate_base_damage(level, base_power, attack, defense)
    base_damage = trunc(base_damage, 16)

    # No random factor in confusion damage in modern games
    return max(1, base_damage)


def calculate_recoil(damage_dealt: int, recoil_fraction: float) -> int:
    """Calculate recoil damage.

    Args:
        damage_dealt: Damage dealt to target
        recoil_fraction: Fraction of damage taken as recoil (e.g., 0.33)

    Returns:
        Recoil damage to attacker
    """
    if recoil_fraction <= 0:
        return 0

    recoil = trunc(damage_dealt * recoil_fraction)
    return max(1, recoil) if damage_dealt > 0 else 0


def calculate_struggle_recoil(attacker_max_hp: int, gen: int = 9) -> int:
    """Calculate Struggle recoil damage.

    Struggle has special recoil based on max HP:
    - Gen 1-3: 1/4 of damage dealt
    - Gen 4+: 1/4 of user's max HP

    Args:
        attacker_max_hp: Attacker's maximum HP
        gen: Generation for formula differences

    Returns:
        Recoil damage
    """
    if gen <= 3:
        # Gen 1-3: Handled by regular recoil with damage dealt
        return 0

    # Gen 4+: 1/4 of max HP
    return max(1, attacker_max_hp // 4)


def calculate_max_hp_recoil(attacker_max_hp: int, fraction: float = 0.5) -> int:
    """Calculate max HP-based recoil damage.

    Used by moves like Mind Blown, Steel Beam, Chloroblast.

    Args:
        attacker_max_hp: Attacker's maximum HP
        fraction: Fraction of max HP (default 0.5 for Mind Blown/Steel Beam)

    Returns:
        Recoil damage
    """
    return max(1, trunc(attacker_max_hp * fraction))


# Moves with max HP-based recoil
MAX_HP_RECOIL_MOVES = {
    'mindblown': 0.5,      # 50% max HP
    'steelbeam': 0.5,      # 50% max HP
    'chloroblast': 0.5,    # 50% max HP
}


def get_move_max_hp_recoil(move_name: str) -> float:
    """Get the max HP recoil fraction for a move.

    Args:
        move_name: Name of the move

    Returns:
        Fraction of max HP as recoil, or 0 if no max HP recoil
    """
    move_lower = move_name.lower().replace(' ', '').replace('-', '')
    return MAX_HP_RECOIL_MOVES.get(move_lower, 0.0)


def calculate_drain(damage_dealt: int, drain_fraction: float) -> int:
    """Calculate HP recovered from drain moves.

    Args:
        damage_dealt: Damage dealt to target
        drain_fraction: Fraction of damage healed (e.g., 0.5)

    Returns:
        HP to recover
    """
    if drain_fraction <= 0:
        return 0

    heal = trunc(damage_dealt * drain_fraction)
    return max(1, heal) if damage_dealt > 0 else 0
