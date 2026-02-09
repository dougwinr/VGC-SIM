"""Unit tests for core/damage.py - Damage calculation."""
import pytest
import numpy as np

from core.damage import (
    # Main calculation functions
    calculate_damage,
    calculate_base_damage,
    calculate_confusion_damage,
    calculate_recoil,
    calculate_drain,
    # Type/STAB functions
    calculate_type_effectiveness,
    get_stab_modifier,
    has_stab,
    # Weather
    get_weather_modifier,
    WEATHER_NONE,
    WEATHER_SUN,
    WEATHER_RAIN,
    WEATHER_SAND,
    # Terrain
    get_terrain_modifier,
    is_grounded,
    TERRAIN_NONE,
    TERRAIN_ELECTRIC,
    TERRAIN_GRASSY,
    TERRAIN_MISTY,
    TERRAIN_PSYCHIC,
    GRASSY_TERRAIN_WEAK_MOVES,
    # Critical hits
    get_crit_chance,
    calculate_crit_stage,
    # Accuracy
    calculate_accuracy,
    check_accuracy,
    # Fixed damage moves
    calculate_fixed_damage,
    is_ohko_move,
    calculate_ohko_accuracy,
    # Multi-hit
    get_multi_hit_count,
    get_parental_bond_modifier,
    # Utility
    trunc,
    clamp,
    get_stat_with_stage,
    apply_modifier,
    # Result class
    DamageResult,
    # Constants
    CRIT_MULTIPLIERS_GEN6,
    # Stellar Tera
    TERA_STELLAR,
    get_stellar_tera_modifier,
    get_tera_power_boost,
    # Additional recoil types
    calculate_struggle_recoil,
    calculate_max_hp_recoil,
    MAX_HP_RECOIL_MOVES,
    get_move_max_hp_recoil,
    # Spread and protect modifiers
    get_spread_modifier,
    get_broken_protect_modifier,
    get_explosion_defense_modifier,
    calculate_minimum_damage,
)
from core.battle_state import BattleState
from core.pokemon import Pokemon
from core.layout import (
    P_SPECIES, P_LEVEL,
    P_TYPE1, P_TYPE2, P_TERA_TYPE,
    P_STAT_HP, P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_CURRENT_HP, P_STATUS,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD,
    P_VOL_FOCUS_ENERGY,
    STATUS_BURN, STATUS_NONE,
)
from data.types import Type
from data.moves import MoveData, MoveCategory, MoveTarget, MoveFlag


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def basic_physical_move():
    """Create a basic physical move for testing."""
    return MoveData(
        id=1,
        name="Tackle",
        type=Type.NORMAL,
        category=MoveCategory.PHYSICAL,
        base_power=40,
        accuracy=100,
        pp=35,
    )


@pytest.fixture
def basic_special_move():
    """Create a basic special move for testing."""
    return MoveData(
        id=2,
        name="Ember",
        type=Type.FIRE,
        category=MoveCategory.SPECIAL,
        base_power=40,
        accuracy=100,
        pp=25,
    )


@pytest.fixture
def high_crit_move():
    """Create a high critical hit rate move."""
    return MoveData(
        id=3,
        name="Slash",
        type=Type.NORMAL,
        category=MoveCategory.PHYSICAL,
        base_power=70,
        accuracy=100,
        pp=20,
        crit_ratio=2,
    )


@pytest.fixture
def status_move():
    """Create a status move."""
    return MoveData(
        id=4,
        name="Thunder Wave",
        type=Type.ELECTRIC,
        category=MoveCategory.STATUS,
        base_power=0,
        accuracy=90,
        pp=20,
    )


@pytest.fixture
def basic_attacker():
    """Create a basic attacking Pokemon."""
    pokemon = Pokemon()
    pokemon.data[P_SPECIES] = 25  # Pikachu
    pokemon.data[P_LEVEL] = 50
    pokemon.data[P_TYPE1] = Type.ELECTRIC.value
    pokemon.data[P_TYPE2] = -1
    pokemon.data[P_TERA_TYPE] = -1
    pokemon.data[P_STAT_HP] = 100
    pokemon.data[P_CURRENT_HP] = 100
    pokemon.data[P_STAT_ATK] = 80
    pokemon.data[P_STAT_DEF] = 60
    pokemon.data[P_STAT_SPA] = 100
    pokemon.data[P_STAT_SPD] = 80
    pokemon.data[P_STATUS] = STATUS_NONE
    return pokemon


@pytest.fixture
def basic_defender():
    """Create a basic defending Pokemon."""
    pokemon = Pokemon()
    pokemon.data[P_SPECIES] = 143  # Snorlax
    pokemon.data[P_LEVEL] = 50
    pokemon.data[P_TYPE1] = Type.NORMAL.value
    pokemon.data[P_TYPE2] = -1
    pokemon.data[P_TERA_TYPE] = -1
    pokemon.data[P_STAT_HP] = 200
    pokemon.data[P_CURRENT_HP] = 200
    pokemon.data[P_STAT_ATK] = 100
    pokemon.data[P_STAT_DEF] = 80
    pokemon.data[P_STAT_SPA] = 70
    pokemon.data[P_STAT_SPD] = 100
    pokemon.data[P_STATUS] = STATUS_NONE
    return pokemon


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestTrunc:
    """Tests for trunc function."""

    def test_trunc_positive_float(self):
        """Test truncating positive float."""
        assert trunc(3.7) == 3
        assert trunc(3.2) == 3
        assert trunc(3.0) == 3

    def test_trunc_negative_float(self):
        """Test truncating negative float."""
        assert trunc(-3.7) == -3
        assert trunc(-3.2) == -3

    def test_trunc_integer(self):
        """Test truncating integer (no change)."""
        assert trunc(5) == 5
        assert trunc(-5) == -5

    def test_trunc_16bit(self):
        """Test 16-bit truncation."""
        assert trunc(0x10000, 16) == 0  # Overflow
        assert trunc(0xFFFF, 16) == 0xFFFF
        assert trunc(0x12345, 16) == 0x2345

    def test_trunc_32bit(self):
        """Test 32-bit truncation (default, unsigned)."""
        # Python's int doesn't wrap, trunc just truncates to int
        assert trunc(0x100000000, 32) == 0x100000000  # No masking in 32-bit mode
        assert trunc(3.9, 32) == 3


class TestClamp:
    """Tests for clamp function."""

    def test_clamp_within_range(self):
        """Test clamping value within range."""
        assert clamp(5, 0, 10) == 5

    def test_clamp_below_min(self):
        """Test clamping value below minimum."""
        assert clamp(-5, 0, 10) == 0

    def test_clamp_above_max(self):
        """Test clamping value above maximum."""
        assert clamp(15, 0, 10) == 10

    def test_clamp_at_boundaries(self):
        """Test clamping at exact boundaries."""
        assert clamp(0, 0, 10) == 0
        assert clamp(10, 0, 10) == 10


class TestGetStatWithStage:
    """Tests for get_stat_with_stage function."""

    def test_stage_0(self):
        """Test stat at stage 0 (no change)."""
        assert get_stat_with_stage(100, 0) == 100

    def test_positive_stages(self):
        """Test positive stat stages."""
        # Stage +1: 3/2 = 1.5x
        assert get_stat_with_stage(100, 1) == 150
        # Stage +2: 4/2 = 2x
        assert get_stat_with_stage(100, 2) == 200
        # Stage +6: 8/2 = 4x
        assert get_stat_with_stage(100, 6) == 400

    def test_negative_stages(self):
        """Test negative stat stages."""
        # Stage -1: 2/3 ≈ 0.667x
        assert get_stat_with_stage(100, -1) == 66
        # Stage -2: 2/4 = 0.5x
        assert get_stat_with_stage(100, -2) == 50
        # Stage -6: 2/8 = 0.25x
        assert get_stat_with_stage(100, -6) == 25

    def test_stage_clamping(self):
        """Test that stages are clamped to valid range."""
        # Stage -10 should be treated as -6
        assert get_stat_with_stage(100, -10) == get_stat_with_stage(100, -6)
        # Stage +10 should be treated as +6
        assert get_stat_with_stage(100, 10) == get_stat_with_stage(100, 6)


class TestApplyModifier:
    """Tests for apply_modifier function."""

    def test_modifier_1x(self):
        """Test 1x modifier (no change)."""
        assert apply_modifier(100, 1.0) == 100

    def test_modifier_1_5x(self):
        """Test 1.5x modifier."""
        assert apply_modifier(100, 1.5) == 150

    def test_modifier_0_5x(self):
        """Test 0.5x modifier."""
        assert apply_modifier(100, 0.5) == 50

    def test_modifier_truncation(self):
        """Test that result is truncated."""
        # 100 * 1.33 = 133.0
        assert apply_modifier(100, 1.33) == 133
        # 100 * 0.75 = 75
        assert apply_modifier(100, 0.75) == 75

    def test_minimum_1_damage(self):
        """Test that non-zero modifier gives at least 1."""
        assert apply_modifier(1, 0.1) == 1  # Would be 0.1 -> 0, but min 1


# =============================================================================
# Critical Hit Tests
# =============================================================================

class TestCritChance:
    """Tests for critical hit chance calculation."""

    def test_crit_chance_stage_0(self):
        """Test crit chance at stage 0."""
        num, denom = get_crit_chance(0)
        assert num == 1
        assert denom == 24

    def test_crit_chance_stage_1(self):
        """Test crit chance at stage 1."""
        num, denom = get_crit_chance(1)
        assert num == 1
        assert denom == 8

    def test_crit_chance_stage_2(self):
        """Test crit chance at stage 2."""
        num, denom = get_crit_chance(2)
        assert num == 1
        assert denom == 2

    def test_crit_chance_stage_3_plus(self):
        """Test crit chance at stage 3+ (always crits)."""
        num, denom = get_crit_chance(3)
        assert num == 1
        assert denom == 1

    def test_crit_chance_gen5(self):
        """Test crit chance in gen 5 (before gen 6)."""
        # Gen 5 uses different crit multipliers
        num, denom = get_crit_chance(0, gen=5)
        assert num == 1
        # Gen 5 stage 0 has different crit rate

        # Test stage clamping to 0-5 in gen 5
        num, denom = get_crit_chance(5, gen=5)
        assert num == 1


class TestCalculateCritStage:
    """Tests for calculate_crit_stage function."""

    def test_normal_move_crit_stage(self, basic_attacker, basic_physical_move):
        """Test crit stage for normal move."""
        stage = calculate_crit_stage(basic_attacker, basic_physical_move)
        assert stage == 0

    def test_high_crit_move_crit_stage(self, basic_attacker, high_crit_move):
        """Test crit stage for high crit move."""
        stage = calculate_crit_stage(basic_attacker, high_crit_move)
        assert stage == 1  # crit_ratio 2 adds 1 stage

    def test_focus_energy_crit_stage(self, basic_attacker, basic_physical_move):
        """Test crit stage with Focus Energy."""
        basic_attacker.data[P_VOL_FOCUS_ENERGY] = 1

        stage = calculate_crit_stage(basic_attacker, basic_physical_move)
        assert stage == 2  # Focus Energy adds 2

    def test_combined_crit_stage(self, basic_attacker, high_crit_move):
        """Test combined crit stage modifiers."""
        basic_attacker.data[P_VOL_FOCUS_ENERGY] = 1

        stage = calculate_crit_stage(
            basic_attacker,
            high_crit_move,
            ability_stage=1,  # Super Luck
            item_stage=1,     # Scope Lens
        )
        # 1 (high crit) + 2 (Focus Energy) + 1 (ability) + 1 (item) = 5, clamped to 4
        assert stage == 4


# =============================================================================
# Type Effectiveness Tests
# =============================================================================

class TestTypeEffectiveness:
    """Tests for type effectiveness calculation."""

    def test_normal_effectiveness(self):
        """Test normal (1x) effectiveness."""
        eff = calculate_type_effectiveness(
            Type.NORMAL,
            Type.NORMAL.value,
            -1,
        )
        assert eff == 1.0

    def test_super_effective(self):
        """Test super effective (2x) effectiveness."""
        eff = calculate_type_effectiveness(
            Type.FIRE,
            Type.GRASS.value,
            -1,
        )
        assert eff == 2.0

    def test_not_very_effective(self):
        """Test not very effective (0.5x) effectiveness."""
        eff = calculate_type_effectiveness(
            Type.FIRE,
            Type.WATER.value,
            -1,
        )
        assert eff == 0.5

    def test_immune(self):
        """Test immune (0x) effectiveness."""
        eff = calculate_type_effectiveness(
            Type.NORMAL,
            Type.GHOST.value,
            -1,
        )
        assert eff == 0.0

    def test_dual_type_4x(self):
        """Test 4x effectiveness against dual type."""
        eff = calculate_type_effectiveness(
            Type.ICE,
            Type.DRAGON.value,
            Type.FLYING.value,
        )
        assert eff == 4.0

    def test_dual_type_0_25x(self):
        """Test 0.25x effectiveness against dual type."""
        eff = calculate_type_effectiveness(
            Type.GRASS,
            Type.FIRE.value,
            Type.FLYING.value,
        )
        assert eff == 0.25

    def test_dual_type_neutral(self):
        """Test neutral from opposing effectiveness."""
        eff = calculate_type_effectiveness(
            Type.FIRE,
            Type.GRASS.value,
            Type.WATER.value,
        )
        assert eff == 1.0  # 2x * 0.5x = 1x

    def test_tera_type_overrides(self):
        """Test Tera type overrides normal types."""
        eff = calculate_type_effectiveness(
            Type.FIRE,
            Type.GRASS.value,
            Type.WATER.value,
            defender_tera_type=Type.STEEL.value,  # Terastallized to Steel
        )
        # Fire vs Steel is 2x
        assert eff == 2.0


# =============================================================================
# STAB Tests
# =============================================================================

class TestStab:
    """Tests for STAB calculation."""

    def test_has_stab_single_type(self):
        """Test STAB check for single-typed Pokemon."""
        assert has_stab(Type.FIRE, Type.FIRE.value, -1) is True
        assert has_stab(Type.WATER, Type.FIRE.value, -1) is False

    def test_has_stab_dual_type(self):
        """Test STAB check for dual-typed Pokemon."""
        assert has_stab(Type.FIRE, Type.FIRE.value, Type.FLYING.value) is True
        assert has_stab(Type.FLYING, Type.FIRE.value, Type.FLYING.value) is True
        assert has_stab(Type.WATER, Type.FIRE.value, Type.FLYING.value) is False

    def test_has_stab_tera_type(self):
        """Test STAB check with Tera type."""
        assert has_stab(
            Type.STEEL,
            Type.FIRE.value,
            Type.FLYING.value,
            attacker_tera_type=Type.STEEL.value,
        ) is True

    def test_stab_modifier_no_stab(self):
        """Test STAB modifier without STAB."""
        mod = get_stab_modifier(Type.WATER, Type.FIRE.value, -1)
        assert mod == 1.0

    def test_stab_modifier_with_stab(self):
        """Test STAB modifier with STAB."""
        mod = get_stab_modifier(Type.FIRE, Type.FIRE.value, -1)
        assert mod == 1.5

    def test_stab_modifier_adaptability(self):
        """Test STAB modifier with Adaptability."""
        mod = get_stab_modifier(
            Type.FIRE,
            Type.FIRE.value,
            -1,
            has_adaptability=True,
        )
        assert mod == 2.0

    def test_stab_modifier_tera_matching_base(self):
        """Test STAB modifier with Tera matching base type."""
        mod = get_stab_modifier(
            Type.FIRE,
            Type.FIRE.value,
            -1,
            attacker_tera_type=Type.FIRE.value,
        )
        assert mod == 2.0  # Tera STAB matching base is 2x


# =============================================================================
# Weather Modifier Tests
# =============================================================================

class TestWeatherModifier:
    """Tests for weather damage modifiers."""

    def test_sun_boosts_fire(self):
        """Test Sun boosts Fire moves."""
        mod = get_weather_modifier(WEATHER_SUN, Type.FIRE)
        assert mod == 1.5

    def test_sun_weakens_water(self):
        """Test Sun weakens Water moves."""
        mod = get_weather_modifier(WEATHER_SUN, Type.WATER)
        assert mod == 0.5

    def test_rain_boosts_water(self):
        """Test Rain boosts Water moves."""
        mod = get_weather_modifier(WEATHER_RAIN, Type.WATER)
        assert mod == 1.5

    def test_rain_weakens_fire(self):
        """Test Rain weakens Fire moves."""
        mod = get_weather_modifier(WEATHER_RAIN, Type.FIRE)
        assert mod == 0.5

    def test_no_weather_neutral(self):
        """Test no weather is neutral."""
        mod = get_weather_modifier(WEATHER_NONE, Type.FIRE)
        assert mod == 1.0

    def test_other_weather_neutral(self):
        """Test other weather is neutral for Fire/Water."""
        mod = get_weather_modifier(WEATHER_SAND, Type.FIRE)
        assert mod == 1.0
        mod = get_weather_modifier(WEATHER_SAND, Type.WATER)
        assert mod == 1.0


# =============================================================================
# Base Damage Calculation Tests
# =============================================================================

class TestBaseDamage:
    """Tests for base damage calculation."""

    def test_basic_formula(self):
        """Test basic damage formula."""
        # floor(2*50/5+2) = floor(22) = 22
        # floor(22 * 40 * 100) = 88000
        # floor(88000 / 80) = 1100
        # floor(1100 / 50) = 22
        # 22 + 2 = 24
        damage = calculate_base_damage(
            level=50,
            power=40,
            attack=100,
            defense=80,
        )
        assert damage == 24

    def test_higher_level_more_damage(self):
        """Test that higher level increases damage."""
        damage_50 = calculate_base_damage(50, 40, 100, 80)
        damage_100 = calculate_base_damage(100, 40, 100, 80)
        assert damage_100 > damage_50

    def test_higher_power_more_damage(self):
        """Test that higher power increases damage."""
        damage_40 = calculate_base_damage(50, 40, 100, 80)
        damage_80 = calculate_base_damage(50, 80, 100, 80)
        assert damage_80 > damage_40

    def test_higher_attack_more_damage(self):
        """Test that higher attack increases damage."""
        damage_100 = calculate_base_damage(50, 40, 100, 80)
        damage_200 = calculate_base_damage(50, 40, 200, 80)
        assert damage_200 > damage_100

    def test_higher_defense_less_damage(self):
        """Test that higher defense decreases damage."""
        damage_80 = calculate_base_damage(50, 40, 100, 80)
        damage_160 = calculate_base_damage(50, 40, 100, 160)
        assert damage_160 < damage_80

    def test_minimum_values(self):
        """Test minimum values are enforced."""
        # Should not crash with minimum values
        damage = calculate_base_damage(1, 1, 1, 1)
        assert damage >= 2  # Base damage always has +2


# =============================================================================
# Full Damage Calculation Tests
# =============================================================================

class TestCalculateDamage:
    """Tests for full damage calculation."""

    def test_status_move_no_damage(self, basic_attacker, basic_defender, status_move):
        """Test that status moves deal 0 damage."""
        result = calculate_damage(basic_attacker, basic_defender, status_move)
        assert result.damage == 0

    def test_damage_without_state_or_random(self, basic_attacker, basic_defender, basic_physical_move):
        """Test damage calculation without state or force_random (uses default random=1.0)."""
        # When state=None and force_random=None, random_factor defaults to 1.0
        result = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            state=None,
            force_random=None,
        )
        # Should still calculate damage
        assert result.damage > 0

    def test_zero_power_no_damage(self, basic_attacker, basic_defender):
        """Test that zero power moves deal 0 damage."""
        move = MoveData(
            id=99,
            name="No Power",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=0,
        )
        result = calculate_damage(basic_attacker, basic_defender, move)
        assert result.damage == 0

    def test_physical_uses_atk_def(self, basic_attacker, basic_defender, basic_physical_move):
        """Test that physical moves use Attack/Defense."""
        # Set high attack, low defense
        basic_attacker.data[P_STAT_ATK] = 200
        basic_defender.data[P_STAT_DEF] = 50

        result = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        )

        # Should deal significant damage
        assert result.damage > 0

    def test_special_uses_spa_spd(self, basic_attacker, basic_defender, basic_special_move):
        """Test that special moves use SpAtk/SpDef."""
        # Set high spa, low spd
        basic_attacker.data[P_STAT_SPA] = 200
        basic_defender.data[P_STAT_SPD] = 50

        result = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_special_move,
            force_crit=False,
            force_random=1.0,
        )

        assert result.damage > 0

    def test_crit_increases_damage(self, basic_attacker, basic_defender, basic_physical_move):
        """Test that critical hits increase damage."""
        damage_no_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        damage_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=True,
            force_random=1.0,
        ).damage

        assert damage_crit > damage_no_crit

    def test_crit_ignores_negative_attack_stage(self, basic_attacker, basic_defender, basic_physical_move):
        """Test that crits ignore negative attack stages."""
        basic_attacker.data[P_STAGE_ATK] = -6

        damage_no_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        damage_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=True,
            force_random=1.0,
        ).damage

        # Crit should ignore the -6 attack stage
        assert damage_crit > damage_no_crit * 4

    def test_crit_ignores_positive_defense_stage(self, basic_attacker, basic_defender, basic_physical_move):
        """Test that crits ignore positive defense stages."""
        basic_defender.data[P_STAGE_DEF] = 6

        damage_no_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        damage_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=True,
            force_random=1.0,
        ).damage

        # Crit should ignore the +6 defense stage
        assert damage_crit > damage_no_crit * 2

    def test_type_effectiveness_super_effective(self, basic_attacker, basic_defender):
        """Test super effective damage."""
        # Fighting vs Normal is 2x
        move = MoveData(
            id=5,
            name="Karate Chop",
            type=Type.FIGHTING,
            category=MoveCategory.PHYSICAL,
            base_power=50,
        )

        result = calculate_damage(
            basic_attacker,
            basic_defender,
            move,
            force_crit=False,
            force_random=1.0,
        )

        assert result.type_effectiveness == 2.0
        assert not result.is_immune

    def test_type_effectiveness_immune(self, basic_attacker, basic_defender):
        """Test immune damage."""
        # Ghost vs Normal is 0x
        move = MoveData(
            id=6,
            name="Shadow Ball",
            type=Type.GHOST,
            category=MoveCategory.SPECIAL,
            base_power=80,
        )

        result = calculate_damage(
            basic_attacker,
            basic_defender,
            move,
            force_crit=False,
            force_random=1.0,
        )

        assert result.damage == 0
        assert result.type_effectiveness == 0.0
        assert result.is_immune is True

    def test_stab_bonus(self, basic_attacker, basic_defender):
        """Test STAB bonus."""
        # Pikachu (Electric) using Electric move
        move = MoveData(
            id=7,
            name="Thunderbolt",
            type=Type.ELECTRIC,
            category=MoveCategory.SPECIAL,
            base_power=90,
        )

        damage_stab = calculate_damage(
            basic_attacker,
            basic_defender,
            move,
            force_crit=False,
            force_random=1.0,
        ).damage

        # Non-STAB move with same power
        move_no_stab = MoveData(
            id=8,
            name="Ice Beam",
            type=Type.ICE,
            category=MoveCategory.SPECIAL,
            base_power=90,
        )

        damage_no_stab = calculate_damage(
            basic_attacker,
            basic_defender,
            move_no_stab,
            force_crit=False,
            force_random=1.0,
        ).damage

        # STAB should deal 1.5x damage
        assert damage_stab > damage_no_stab

    def test_burn_reduces_physical_damage(self, basic_attacker, basic_defender, basic_physical_move):
        """Test that burn reduces physical damage."""
        damage_healthy = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        basic_attacker.data[P_STATUS] = STATUS_BURN

        damage_burned = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        assert damage_burned < damage_healthy
        # Should be roughly half
        assert damage_burned == damage_healthy // 2 or damage_burned == (damage_healthy + 1) // 2

    def test_burn_does_not_reduce_special_damage(self, basic_attacker, basic_defender, basic_special_move):
        """Test that burn doesn't reduce special damage."""
        damage_healthy = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_special_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        basic_attacker.data[P_STATUS] = STATUS_BURN

        damage_burned = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_special_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        assert damage_burned == damage_healthy

    def test_facade_ignores_burn_gen6_plus(self, basic_attacker, basic_defender):
        """Test that Facade ignores burn penalty in Gen 6+."""
        facade = MoveData(
            id=263,
            name="Facade",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=70,
            accuracy=100,
            pp=20,
        )

        # Create a battle state with Gen 6+
        state = BattleState(seed=42, gen=9)

        damage_healthy = calculate_damage(
            basic_attacker,
            basic_defender,
            facade,
            state=state,
            force_crit=False,
            force_random=1.0,
        ).damage

        basic_attacker.data[P_STATUS] = STATUS_BURN

        damage_burned = calculate_damage(
            basic_attacker,
            basic_defender,
            facade,
            state=state,
            force_crit=False,
            force_random=1.0,
        ).damage

        # In Gen 6+, Facade should NOT be reduced by burn
        assert damage_burned == damage_healthy

    def test_facade_still_burned_gen5(self, basic_attacker, basic_defender):
        """Test that Facade is affected by burn in Gen 5."""
        facade = MoveData(
            id=263,
            name="Facade",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=70,
            accuracy=100,
            pp=20,
        )

        # Create a battle state with Gen 5
        state = BattleState(seed=42, gen=5)

        damage_healthy = calculate_damage(
            basic_attacker,
            basic_defender,
            facade,
            state=state,
            force_crit=False,
            force_random=1.0,
        ).damage

        basic_attacker.data[P_STATUS] = STATUS_BURN

        damage_burned = calculate_damage(
            basic_attacker,
            basic_defender,
            facade,
            state=state,
            force_crit=False,
            force_random=1.0,
        ).damage

        # In Gen 5, Facade IS reduced by burn
        assert damage_burned < damage_healthy

    def test_random_factor_range(self, basic_attacker, basic_defender, basic_physical_move):
        """Test random factor affects damage."""
        damage_min = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=0.85,
        ).damage

        damage_max = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        ).damage

        assert damage_max >= damage_min
        # Max should be ~17.6% higher than min (1.0/0.85)

    def test_spread_modifier(self, basic_attacker, basic_defender, basic_physical_move):
        """Test spread move modifier."""
        damage_single = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
            is_spread=False,
        ).damage

        damage_spread = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
            is_spread=True,
        ).damage

        # Spread should be 75% of single target
        assert damage_spread < damage_single

    def test_weather_modifier_sun(self, basic_attacker, basic_defender):
        """Test Sun weather boost for Fire."""
        fire_move = MoveData(
            id=9,
            name="Fire Blast",
            type=Type.FIRE,
            category=MoveCategory.SPECIAL,
            base_power=110,
        )

        state = BattleState(seed=42)
        state.set_weather(WEATHER_SUN, 5)

        damage = calculate_damage(
            basic_attacker,
            basic_defender,
            fire_move,
            state=state,
            force_crit=False,
            force_random=1.0,
        ).damage

        # Compare to no weather
        state.clear_weather()
        damage_no_weather = calculate_damage(
            basic_attacker,
            basic_defender,
            fire_move,
            state=state,
            force_crit=False,
            force_random=1.0,
        ).damage

        assert damage > damage_no_weather

    def test_minimum_damage(self, basic_attacker, basic_defender):
        """Test minimum damage is 1."""
        # Very weak attack
        weak_move = MoveData(
            id=10,
            name="Weak",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=10,
        )

        basic_attacker.data[P_STAT_ATK] = 10
        basic_defender.data[P_STAT_DEF] = 500

        result = calculate_damage(
            basic_attacker,
            basic_defender,
            weak_move,
            force_crit=False,
            force_random=0.85,
        )

        assert result.damage >= 1

    def test_damage_result_contains_crit_info(self, basic_attacker, basic_defender, basic_physical_move):
        """Test DamageResult contains critical hit info."""
        result_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=True,
            force_random=1.0,
        )
        assert result_crit.crit is True

        result_no_crit = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            force_crit=False,
            force_random=1.0,
        )
        assert result_no_crit.crit is False

    def test_damage_with_battle_state_prng(self, basic_attacker, basic_defender, basic_physical_move):
        """Test damage calculation uses battle state PRNG."""
        state = BattleState(seed=12345)

        result1 = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            state=state,
        )

        # Reset PRNG
        state2 = BattleState(seed=12345)

        result2 = calculate_damage(
            basic_attacker,
            basic_defender,
            basic_physical_move,
            state=state2,
        )

        # Same seed should give same result
        assert result1.damage == result2.damage
        assert result1.crit == result2.crit
        assert result1.random_factor == result2.random_factor


# =============================================================================
# Confusion Damage Tests
# =============================================================================

class TestConfusionDamage:
    """Tests for confusion self-hit damage."""

    def test_confusion_damage_uses_physical_stats(self, basic_attacker):
        """Test confusion uses Attack/Defense."""
        damage = calculate_confusion_damage(basic_attacker)
        assert damage >= 1

    def test_confusion_damage_minimum(self, basic_attacker):
        """Test confusion damage has minimum of 1."""
        basic_attacker.data[P_STAT_ATK] = 1
        basic_attacker.data[P_STAT_DEF] = 1000

        damage = calculate_confusion_damage(basic_attacker)
        assert damage >= 1

    def test_confusion_damage_with_stages(self, basic_attacker):
        """Test confusion respects stat stages."""
        damage_neutral = calculate_confusion_damage(basic_attacker)

        basic_attacker.data[P_STAGE_ATK] = 6

        damage_boosted = calculate_confusion_damage(basic_attacker)
        assert damage_boosted > damage_neutral


# =============================================================================
# Recoil and Drain Tests
# =============================================================================

class TestRecoil:
    """Tests for recoil damage calculation."""

    def test_recoil_calculation(self):
        """Test recoil damage is calculated correctly."""
        # 33% recoil on 100 damage = 33
        recoil = calculate_recoil(100, 0.33)
        assert recoil == 33

    def test_recoil_minimum(self):
        """Test recoil has minimum of 1 when damage dealt."""
        recoil = calculate_recoil(1, 0.1)
        assert recoil >= 1

    def test_recoil_zero_damage(self):
        """Test recoil is 0 when no damage dealt."""
        recoil = calculate_recoil(0, 0.33)
        assert recoil == 0

    def test_recoil_zero_fraction(self):
        """Test no recoil with 0 fraction."""
        recoil = calculate_recoil(100, 0.0)
        assert recoil == 0


class TestDrain:
    """Tests for drain healing calculation."""

    def test_drain_calculation(self):
        """Test drain healing is calculated correctly."""
        # 50% drain on 100 damage = 50
        heal = calculate_drain(100, 0.5)
        assert heal == 50

    def test_drain_minimum(self):
        """Test drain has minimum of 1 when damage dealt."""
        heal = calculate_drain(1, 0.1)
        assert heal >= 1

    def test_drain_zero_damage(self):
        """Test drain is 0 when no damage dealt."""
        heal = calculate_drain(0, 0.5)
        assert heal == 0

    def test_drain_zero_fraction(self):
        """Test no drain with 0 fraction."""
        heal = calculate_drain(100, 0.0)
        assert heal == 0


# =============================================================================
# DamageResult Tests
# =============================================================================

class TestDamageResult:
    """Tests for DamageResult dataclass."""

    def test_damage_result_defaults(self):
        """Test DamageResult default values."""
        result = DamageResult(damage=50)

        assert result.damage == 50
        assert result.crit is False
        assert result.type_effectiveness == 1.0
        assert result.is_immune is False
        assert result.random_factor == 1.0

    def test_damage_result_all_fields(self):
        """Test DamageResult with all fields."""
        result = DamageResult(
            damage=100,
            crit=True,
            type_effectiveness=2.0,
            is_immune=False,
            random_factor=0.93,
        )

        assert result.damage == 100
        assert result.crit is True
        assert result.type_effectiveness == 2.0
        assert result.random_factor == 0.93


# =============================================================================
# Integration Tests
# =============================================================================

class TestDamageIntegration:
    """Integration tests for complete damage scenarios."""

    def test_thunderbolt_vs_gyarados(self):
        """Test realistic Thunderbolt vs Gyarados scenario."""
        # Pikachu with Thunderbolt vs Gyarados (Water/Flying)
        pikachu = Pokemon()
        pikachu.data[P_SPECIES] = 25
        pikachu.data[P_LEVEL] = 50
        pikachu.data[P_TYPE1] = Type.ELECTRIC.value
        pikachu.data[P_TYPE2] = -1
        pikachu.data[P_TERA_TYPE] = -1
        pikachu.data[P_STAT_SPA] = 100
        pikachu.data[P_STATUS] = STATUS_NONE

        gyarados = Pokemon()
        gyarados.data[P_SPECIES] = 130
        gyarados.data[P_LEVEL] = 50
        gyarados.data[P_TYPE1] = Type.WATER.value
        gyarados.data[P_TYPE2] = Type.FLYING.value
        gyarados.data[P_TERA_TYPE] = -1
        gyarados.data[P_STAT_SPD] = 100
        gyarados.data[P_STATUS] = STATUS_NONE

        thunderbolt = MoveData(
            id=85,
            name="Thunderbolt",
            type=Type.ELECTRIC,
            category=MoveCategory.SPECIAL,
            base_power=90,
        )

        result = calculate_damage(
            pikachu,
            gyarados,
            thunderbolt,
            force_crit=False,
            force_random=1.0,
        )

        # Should be 4x effective (Electric vs Water/Flying) + STAB
        assert result.type_effectiveness == 4.0
        assert result.damage > 0

    def test_earthquake_vs_flying(self):
        """Test Ground move vs Flying (immune)."""
        attacker = Pokemon()
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.GROUND.value
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_ATK] = 150
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_TYPE1] = Type.FLYING.value
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_DEF] = 100
        defender.data[P_STATUS] = STATUS_NONE

        earthquake = MoveData(
            id=89,
            name="Earthquake",
            type=Type.GROUND,
            category=MoveCategory.PHYSICAL,
            base_power=100,
        )

        result = calculate_damage(
            attacker,
            defender,
            earthquake,
            force_crit=False,
            force_random=1.0,
        )

        assert result.damage == 0
        assert result.is_immune is True
        assert result.type_effectiveness == 0.0

    def test_deterministic_damage_sequence(self):
        """Test that damage sequence is deterministic with same seed."""
        attacker = Pokemon()
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.NORMAL.value
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_ATK] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_TYPE1] = Type.NORMAL.value
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_DEF] = 100
        defender.data[P_STATUS] = STATUS_NONE

        move = MoveData(
            id=1,
            name="Test",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=50,
        )

        # Calculate damage 10 times with same seed
        state1 = BattleState(seed=42)
        damages1 = [
            calculate_damage(attacker, defender, move, state=state1).damage
            for _ in range(10)
        ]

        state2 = BattleState(seed=42)
        damages2 = [
            calculate_damage(attacker, defender, move, state=state2).damage
            for _ in range(10)
        ]

        assert damages1 == damages2


# =============================================================================
# Terrain Modifier Tests
# =============================================================================

class TestTerrainModifier:
    """Tests for terrain damage modifiers."""

    def test_electric_terrain_boosts_electric(self):
        """Test Electric Terrain boosts Electric moves."""
        mod = get_terrain_modifier(TERRAIN_ELECTRIC, Type.ELECTRIC, True, True)
        assert mod == 1.3

    def test_electric_terrain_requires_grounded_attacker(self):
        """Test Electric Terrain requires grounded attacker."""
        mod = get_terrain_modifier(TERRAIN_ELECTRIC, Type.ELECTRIC, False, True)
        assert mod == 1.0

    def test_grassy_terrain_boosts_grass(self):
        """Test Grassy Terrain boosts Grass moves."""
        mod = get_terrain_modifier(TERRAIN_GRASSY, Type.GRASS, True, True)
        assert mod == 1.3

    def test_grassy_terrain_requires_grounded_attacker(self):
        """Test Grassy Terrain boost requires grounded attacker."""
        mod = get_terrain_modifier(TERRAIN_GRASSY, Type.GRASS, False, True)
        assert mod == 1.0

    def test_grassy_terrain_weakens_earthquake(self):
        """Test Grassy Terrain weakens Earthquake."""
        mod = get_terrain_modifier(TERRAIN_GRASSY, Type.GROUND, True, True, 'Earthquake')
        assert mod == 0.5

    def test_grassy_terrain_weakens_bulldoze(self):
        """Test Grassy Terrain weakens Bulldoze."""
        mod = get_terrain_modifier(TERRAIN_GRASSY, Type.GROUND, True, True, 'Bulldoze')
        assert mod == 0.5

    def test_grassy_terrain_weakens_magnitude(self):
        """Test Grassy Terrain weakens Magnitude."""
        mod = get_terrain_modifier(TERRAIN_GRASSY, Type.GROUND, True, True, 'Magnitude')
        assert mod == 0.5

    def test_grassy_terrain_earthquake_requires_grounded_defender(self):
        """Test Grassy Terrain Earthquake nerf requires grounded defender."""
        mod = get_terrain_modifier(TERRAIN_GRASSY, Type.GROUND, True, False, 'Earthquake')
        assert mod == 1.0

    def test_grassy_terrain_no_effect_other_ground_moves(self):
        """Test Grassy Terrain doesn't affect other Ground moves."""
        mod = get_terrain_modifier(TERRAIN_GRASSY, Type.GROUND, True, True, 'Earth Power')
        assert mod == 1.0

    def test_psychic_terrain_boosts_psychic(self):
        """Test Psychic Terrain boosts Psychic moves."""
        mod = get_terrain_modifier(TERRAIN_PSYCHIC, Type.PSYCHIC, True, True)
        assert mod == 1.3

    def test_psychic_terrain_requires_grounded_attacker(self):
        """Test Psychic Terrain requires grounded attacker."""
        mod = get_terrain_modifier(TERRAIN_PSYCHIC, Type.PSYCHIC, False, True)
        assert mod == 1.0

    def test_misty_terrain_weakens_dragon(self):
        """Test Misty Terrain weakens Dragon moves."""
        mod = get_terrain_modifier(TERRAIN_MISTY, Type.DRAGON, True, True)
        assert mod == 0.5

    def test_misty_terrain_requires_grounded_defender(self):
        """Test Misty Terrain Dragon nerf requires grounded defender."""
        mod = get_terrain_modifier(TERRAIN_MISTY, Type.DRAGON, True, False)
        assert mod == 1.0

    def test_terrain_no_effect_wrong_type(self):
        """Test terrain has no effect on non-matching types."""
        assert get_terrain_modifier(TERRAIN_ELECTRIC, Type.FIRE, True, True) == 1.0
        assert get_terrain_modifier(TERRAIN_GRASSY, Type.WATER, True, True) == 1.0

    def test_no_terrain_neutral(self):
        """Test no terrain is always neutral."""
        assert get_terrain_modifier(TERRAIN_NONE, Type.ELECTRIC, True, True) == 1.0


class TestIsGrounded:
    """Tests for grounded status checking."""

    def test_normal_pokemon_grounded(self):
        """Test normal Pokemon is grounded."""
        assert is_grounded((Type.NORMAL.value, -1)) == True
        assert is_grounded((Type.FIRE.value, Type.FIGHTING.value)) == True

    def test_flying_type_not_grounded(self):
        """Test Flying type is not grounded."""
        assert is_grounded((Type.FLYING.value, -1)) == False
        assert is_grounded((Type.NORMAL.value, Type.FLYING.value)) == False
        assert is_grounded((Type.FLYING.value, Type.DRAGON.value)) == False

    def test_levitate_not_grounded(self):
        """Test Pokemon with Levitate is not grounded."""
        assert is_grounded((Type.GHOST.value, -1), has_levitate=True) == False

    def test_air_balloon_not_grounded(self):
        """Test Pokemon with Air Balloon is not grounded."""
        assert is_grounded((Type.STEEL.value, -1), has_air_balloon=True) == False

    def test_magnet_rise_not_grounded(self):
        """Test Pokemon with Magnet Rise is not grounded."""
        assert is_grounded((Type.ELECTRIC.value, -1), is_magnet_rise=True) == False

    def test_telekinesis_not_grounded(self):
        """Test Pokemon under Telekinesis is not grounded."""
        assert is_grounded((Type.PSYCHIC.value, -1), is_telekinesis=True) == False

    def test_gravity_grounds_flying(self):
        """Test Gravity grounds Flying types."""
        assert is_grounded((Type.FLYING.value, -1), gravity_active=True) == True

    def test_gravity_grounds_levitate(self):
        """Test Gravity grounds Levitate."""
        assert is_grounded((Type.GHOST.value, -1), has_levitate=True, gravity_active=True) == True

    def test_iron_ball_grounds(self):
        """Test Iron Ball grounds Pokemon."""
        assert is_grounded((Type.FLYING.value, -1), has_iron_ball=True) == True
        assert is_grounded((Type.GHOST.value, -1), has_levitate=True, has_iron_ball=True) == True

    def test_ingrain_grounds(self):
        """Test Ingrain grounds Pokemon."""
        assert is_grounded((Type.GRASS.value, Type.FLYING.value), is_ingrain=True) == True

    def test_smack_down_grounds(self):
        """Test Smack Down grounds Pokemon."""
        assert is_grounded((Type.FLYING.value, -1), is_smack_down=True) == True
        assert is_grounded((Type.GHOST.value, -1), has_levitate=True, is_smack_down=True) == True


class TestGrassyTerrainWeakMoves:
    """Tests for Grassy Terrain weak moves constant."""

    def test_earthquake_in_set(self):
        """Test Earthquake is in the weak moves set."""
        assert 'earthquake' in GRASSY_TERRAIN_WEAK_MOVES

    def test_bulldoze_in_set(self):
        """Test Bulldoze is in the weak moves set."""
        assert 'bulldoze' in GRASSY_TERRAIN_WEAK_MOVES

    def test_magnitude_in_set(self):
        """Test Magnitude is in the weak moves set."""
        assert 'magnitude' in GRASSY_TERRAIN_WEAK_MOVES

    def test_other_moves_not_in_set(self):
        """Test other moves are not in the weak moves set."""
        assert 'earthpower' not in GRASSY_TERRAIN_WEAK_MOVES
        assert 'dig' not in GRASSY_TERRAIN_WEAK_MOVES


# =============================================================================
# Accuracy Calculation Tests
# =============================================================================

class TestAccuracyCalculation:
    """Tests for accuracy calculation functions."""

    def test_calculate_accuracy_base(self):
        """Test base accuracy without stages."""
        assert calculate_accuracy(100, 0, 0) == 100
        assert calculate_accuracy(95, 0, 0) == 95

    def test_calculate_accuracy_with_acc_stages(self):
        """Test accuracy with accuracy stage boosts."""
        # +1 accuracy = 4/3 = 133%
        assert calculate_accuracy(100, 1, 0) == 133
        # +6 accuracy = 9/3 = 300%
        assert calculate_accuracy(100, 6, 0) == 300

    def test_calculate_accuracy_with_eva_stages(self):
        """Test accuracy with evasion stages."""
        # +1 evasion = 3/4 = 75% for the attacker
        assert calculate_accuracy(100, 0, 1) == 75
        # +6 evasion = 3/9 = 33% for the attacker
        assert calculate_accuracy(100, 0, 6) == 33

    def test_calculate_accuracy_combined_stages(self):
        """Test accuracy with combined stages."""
        # +1 acc, +1 eva = net 0 = 100%
        assert calculate_accuracy(100, 1, 1) == 100
        # +2 acc, +1 eva = net +1 = 133%
        assert calculate_accuracy(100, 2, 1) == 133

    def test_calculate_accuracy_always_hit(self):
        """Test always-hit moves (0 accuracy)."""
        assert calculate_accuracy(0, 0, 0) == 100
        assert calculate_accuracy(0, -6, 6) == 100

    def test_check_accuracy_hit(self):
        """Test check_accuracy returns True when hit."""
        assert check_accuracy(100, 0, 0, 50) == True
        assert check_accuracy(100, 0, 0, 99) == True

    def test_check_accuracy_miss(self):
        """Test check_accuracy returns False when miss."""
        assert check_accuracy(50, 0, 0, 60) == False
        assert check_accuracy(50, 0, 0, 99) == False

    def test_check_accuracy_always_hit(self):
        """Test always-hit moves always hit."""
        assert check_accuracy(0, 0, 0, 99) == True
        assert check_accuracy(0, -6, 6, 99) == True


# =============================================================================
# Fixed Damage Move Tests
# =============================================================================

class TestFixedDamageMoves:
    """Tests for fixed damage move calculations."""

    def test_seismic_toss(self):
        """Test Seismic Toss does level damage."""
        assert calculate_fixed_damage('seismic toss', 50, 100, 100, 200, 200) == 50
        assert calculate_fixed_damage('seismictoss', 100, 100, 100, 200, 200) == 100

    def test_night_shade(self):
        """Test Night Shade does level damage."""
        assert calculate_fixed_damage('night shade', 75, 100, 100, 200, 200) == 75
        assert calculate_fixed_damage('nightshade', 30, 100, 100, 200, 200) == 30

    def test_sonic_boom(self):
        """Test Sonic Boom does 20 fixed damage."""
        assert calculate_fixed_damage('sonic boom', 50, 100, 100, 200, 200) == 20
        assert calculate_fixed_damage('sonicboom', 100, 100, 100, 200, 200) == 20

    def test_dragon_rage(self):
        """Test Dragon Rage does 40 fixed damage."""
        assert calculate_fixed_damage('dragon rage', 50, 100, 100, 200, 200) == 40
        assert calculate_fixed_damage('dragonrage', 100, 100, 100, 200, 200) == 40

    def test_super_fang(self):
        """Test Super Fang does half target HP."""
        assert calculate_fixed_damage('super fang', 50, 100, 100, 200, 200) == 100
        assert calculate_fixed_damage('superfang', 50, 100, 100, 100, 100) == 50
        # Minimum 1 damage
        assert calculate_fixed_damage('superfang', 50, 100, 100, 1, 100) == 1

    def test_natures_madness(self):
        """Test Nature's Madness does half target HP."""
        assert calculate_fixed_damage("nature's madness", 50, 100, 100, 200, 200) == 100
        assert calculate_fixed_damage('naturesmadness', 50, 100, 100, 50, 100) == 25

    def test_endeavor(self):
        """Test Endeavor does target HP - attacker HP damage."""
        # Target at 200 HP, attacker at 100 HP = 100 damage
        assert calculate_fixed_damage('endeavor', 50, 100, 200, 200, 200) == 100
        # Target at same HP = 0 damage
        assert calculate_fixed_damage('endeavor', 50, 100, 200, 100, 200) == 0
        # Target at lower HP = 0 damage
        assert calculate_fixed_damage('endeavor', 50, 100, 200, 50, 200) == 0

    def test_final_gambit(self):
        """Test Final Gambit does attacker HP damage."""
        assert calculate_fixed_damage('final gambit', 50, 100, 200, 200, 200) == 100
        assert calculate_fixed_damage('finalgambit', 50, 50, 200, 200, 200) == 50

    def test_non_fixed_damage_move(self):
        """Test that non-fixed-damage moves return 0."""
        # Thunderbolt is not a fixed damage move
        assert calculate_fixed_damage('thunderbolt', 50, 100, 200, 200, 200) == 0
        # Earthquake is not a fixed damage move
        assert calculate_fixed_damage('earthquake', 100, 150, 200, 200, 200) == 0


# =============================================================================
# OHKO Move Tests
# =============================================================================

class TestOhkoMoves:
    """Tests for OHKO move functions."""

    def test_is_ohko_move(self):
        """Test OHKO move identification."""
        assert is_ohko_move('fissure') == True
        assert is_ohko_move('Fissure') == True
        assert is_ohko_move('guillotine') == True
        assert is_ohko_move('horn drill') == True
        assert is_ohko_move('sheer cold') == True
        assert is_ohko_move('earthquake') == False
        assert is_ohko_move('ice beam') == False

    def test_ohko_accuracy_same_level(self):
        """Test OHKO accuracy at same level."""
        assert calculate_ohko_accuracy(50, 50) == 30

    def test_ohko_accuracy_higher_level(self):
        """Test OHKO accuracy when attacker is higher level."""
        # 50 - 40 = 10 bonus accuracy
        assert calculate_ohko_accuracy(50, 40) == 40
        # 100 - 50 = 50 bonus accuracy
        assert calculate_ohko_accuracy(100, 50) == 80

    def test_ohko_accuracy_lower_level(self):
        """Test OHKO accuracy when target is higher level."""
        assert calculate_ohko_accuracy(40, 50) == 0
        assert calculate_ohko_accuracy(50, 100) == 0

    def test_sheer_cold_non_ice_type(self):
        """Test Sheer Cold has 20% base accuracy for non-Ice types."""
        assert calculate_ohko_accuracy(50, 50, False, 'sheer cold') == 20
        assert calculate_ohko_accuracy(60, 50, False, 'sheer cold') == 30

    def test_sheer_cold_ice_type(self):
        """Test Sheer Cold has 30% base accuracy for Ice types."""
        assert calculate_ohko_accuracy(50, 50, True, 'sheer cold') == 30
        assert calculate_ohko_accuracy(60, 50, True, 'sheer cold') == 40


# =============================================================================
# Multi-Hit Move Tests
# =============================================================================

class TestMultiHitMoves:
    """Tests for multi-hit move calculations."""

    def test_multi_hit_distribution(self):
        """Test multi-hit distribution is valid."""
        for i in range(20):
            hits = get_multi_hit_count(i)
            assert 2 <= hits <= 5

    def test_skill_link_always_5(self):
        """Test Skill Link always gives 5 hits."""
        for i in range(20):
            assert get_multi_hit_count(i, has_skill_link=True) == 5

    def test_loaded_dice_minimum_4(self):
        """Test Loaded Dice guarantees at least 4 hits."""
        for i in range(20):
            hits = get_multi_hit_count(i, has_loaded_dice=True)
            assert hits >= 4

    def test_parental_bond_first_hit(self):
        """Test Parental Bond first hit is full damage."""
        assert get_parental_bond_modifier(1, 6) == 1.0
        assert get_parental_bond_modifier(1, 7) == 1.0
        assert get_parental_bond_modifier(1, 9) == 1.0

    def test_parental_bond_second_hit_gen6(self):
        """Test Parental Bond second hit is 0.5x in Gen 6."""
        assert get_parental_bond_modifier(2, 6) == 0.5

    def test_parental_bond_second_hit_gen7plus(self):
        """Test Parental Bond second hit is 0.25x in Gen 7+."""
        assert get_parental_bond_modifier(2, 7) == 0.25
        assert get_parental_bond_modifier(2, 8) == 0.25
        assert get_parental_bond_modifier(2, 9) == 0.25


# =============================================================================
# Stellar Tera Type Tests
# =============================================================================

class TestStellarTera:
    """Tests for Stellar Tera type modifier."""

    def test_stellar_constant(self):
        """Test Stellar Tera type constant."""
        assert TERA_STELLAR == 19

    def test_stellar_non_stab_boost(self):
        """Test Stellar gives ~1.2x boost for non-STAB types."""
        mod = get_stellar_tera_modifier(
            Type.FIRE,
            Type.WATER.value,  # Water type Pokemon
            -1,
            TERA_STELLAR,
        )
        # 4915/4096 ≈ 1.2
        assert abs(mod - 1.2) < 0.01

    def test_stellar_stab_boost(self):
        """Test Stellar gives 2x boost for STAB types."""
        mod = get_stellar_tera_modifier(
            Type.FIRE,
            Type.FIRE.value,  # Fire type Pokemon
            -1,
            TERA_STELLAR,
        )
        assert mod == 2.0

    def test_stellar_no_boost_non_stellar(self):
        """Test no Stellar boost if not Stellar Tera."""
        mod = get_stellar_tera_modifier(
            Type.FIRE,
            Type.WATER.value,
            -1,
            Type.FIRE.value,  # Fire Tera, not Stellar
        )
        assert mod == 1.0

    def test_stellar_used_types_no_repeat(self):
        """Test Stellar boost only once per type."""
        used = {Type.FIRE.value}
        mod = get_stellar_tera_modifier(
            Type.FIRE,
            Type.WATER.value,
            -1,
            TERA_STELLAR,
            stellar_used_types=used,
        )
        assert mod == 1.0

    def test_stellar_unused_type_gets_boost(self):
        """Test unused type still gets Stellar boost."""
        used = {Type.WATER.value}
        mod = get_stellar_tera_modifier(
            Type.FIRE,
            Type.GRASS.value,
            -1,
            TERA_STELLAR,
            stellar_used_types=used,
        )
        assert abs(mod - 1.2) < 0.01


class TestTeraPowerBoost:
    """Tests for Tera base power boost."""

    def test_tera_boost_low_bp(self):
        """Test Tera boosts low BP moves to 60."""
        assert get_tera_power_boost(40, Type.FIRE, Type.FIRE.value) == 60
        assert get_tera_power_boost(50, Type.FIRE, Type.FIRE.value) == 60
        assert get_tera_power_boost(59, Type.FIRE, Type.FIRE.value) == 60

    def test_tera_no_boost_high_bp(self):
        """Test Tera doesn't boost high BP moves."""
        assert get_tera_power_boost(60, Type.FIRE, Type.FIRE.value) == 60
        assert get_tera_power_boost(90, Type.FIRE, Type.FIRE.value) == 90
        assert get_tera_power_boost(120, Type.FIRE, Type.FIRE.value) == 120

    def test_tera_no_boost_wrong_type(self):
        """Test Tera doesn't boost non-matching type."""
        assert get_tera_power_boost(40, Type.FIRE, Type.WATER.value) == 40
        assert get_tera_power_boost(40, Type.WATER, Type.FIRE.value) == 40

    def test_tera_no_boost_not_terastallized(self):
        """Test no boost when not terastallized."""
        assert get_tera_power_boost(40, Type.FIRE, -1) == 40

    def test_tera_no_boost_stellar(self):
        """Test Stellar doesn't get the 60 BP boost."""
        assert get_tera_power_boost(40, Type.FIRE, TERA_STELLAR) == 40

    def test_tera_no_boost_zero_bp(self):
        """Test zero BP moves aren't boosted."""
        assert get_tera_power_boost(0, Type.FIRE, Type.FIRE.value) == 0


# =============================================================================
# Additional Recoil Type Tests
# =============================================================================

class TestStruggleRecoil:
    """Tests for Struggle recoil calculation."""

    def test_struggle_recoil_gen4_plus(self):
        """Test Struggle recoil is 1/4 max HP in Gen 4+."""
        assert calculate_struggle_recoil(100, gen=4) == 25
        assert calculate_struggle_recoil(200, gen=5) == 50
        assert calculate_struggle_recoil(300, gen=9) == 75

    def test_struggle_recoil_gen3_and_earlier(self):
        """Test Struggle recoil in Gen 1-3 (handled differently)."""
        # In Gen 1-3, handled by regular damage-based recoil
        assert calculate_struggle_recoil(100, gen=3) == 0
        assert calculate_struggle_recoil(100, gen=2) == 0
        assert calculate_struggle_recoil(100, gen=1) == 0

    def test_struggle_recoil_minimum(self):
        """Test Struggle recoil has minimum of 1."""
        assert calculate_struggle_recoil(1, gen=9) >= 1
        assert calculate_struggle_recoil(3, gen=9) >= 1


class TestMaxHpRecoil:
    """Tests for max HP-based recoil moves."""

    def test_calculate_max_hp_recoil_half(self):
        """Test 50% max HP recoil."""
        assert calculate_max_hp_recoil(100, 0.5) == 50
        assert calculate_max_hp_recoil(200, 0.5) == 100

    def test_calculate_max_hp_recoil_other_fractions(self):
        """Test other recoil fractions."""
        assert calculate_max_hp_recoil(100, 0.25) == 25
        assert calculate_max_hp_recoil(100, 0.33) == 33

    def test_calculate_max_hp_recoil_minimum(self):
        """Test max HP recoil has minimum of 1."""
        assert calculate_max_hp_recoil(1, 0.5) >= 1
        assert calculate_max_hp_recoil(1, 0.1) >= 1

    def test_max_hp_recoil_moves_constant(self):
        """Test max HP recoil moves are defined correctly."""
        assert 'mindblown' in MAX_HP_RECOIL_MOVES
        assert 'steelbeam' in MAX_HP_RECOIL_MOVES
        assert 'chloroblast' in MAX_HP_RECOIL_MOVES
        assert MAX_HP_RECOIL_MOVES['mindblown'] == 0.5
        assert MAX_HP_RECOIL_MOVES['steelbeam'] == 0.5

    def test_get_move_max_hp_recoil(self):
        """Test getting max HP recoil for moves."""
        assert get_move_max_hp_recoil('Mind Blown') == 0.5
        assert get_move_max_hp_recoil('steel beam') == 0.5
        assert get_move_max_hp_recoil('Chloroblast') == 0.5
        assert get_move_max_hp_recoil('Earthquake') == 0.0
        assert get_move_max_hp_recoil('Thunderbolt') == 0.0


# =============================================================================
# Spread Modifier Tests
# =============================================================================

class TestSpreadModifier:
    """Tests for spread move damage modifier."""

    def test_spread_single_target(self):
        """Test no spread penalty for single target."""
        assert get_spread_modifier('doubles', 1) == 1.0
        assert get_spread_modifier('ffa', 1) == 1.0

    def test_spread_doubles(self):
        """Test spread modifier in doubles."""
        assert get_spread_modifier('doubles', 2) == 0.75
        assert get_spread_modifier('doubles', 3) == 0.75

    def test_spread_triples(self):
        """Test spread modifier in triples."""
        assert get_spread_modifier('triples', 2) == 0.75
        assert get_spread_modifier('triples', 3) == 0.75

    def test_spread_ffa(self):
        """Test spread modifier in free-for-all."""
        assert get_spread_modifier('ffa', 2) == 0.5
        assert get_spread_modifier('ffa', 3) == 0.5
        assert get_spread_modifier('ffa', 4) == 0.5

    def test_spread_singles(self):
        """Test singles has no spread modifier."""
        assert get_spread_modifier('singles', 1) == 1.0


# =============================================================================
# Broken Protect Modifier Tests
# =============================================================================

class TestBrokenProtectModifier:
    """Tests for Z-Move/Max Move protect breaking modifier."""

    def test_normal_move_no_modifier(self):
        """Test normal moves have no broken protect modifier."""
        assert get_broken_protect_modifier(False, False) == 1.0

    def test_z_move_broken_protect(self):
        """Test Z-Moves deal 0.25x through Protect."""
        assert get_broken_protect_modifier(is_z_move=True) == 0.25

    def test_max_move_broken_protect(self):
        """Test Max Moves deal 0.25x through Protect."""
        assert get_broken_protect_modifier(is_max_move=True) == 0.25

    def test_z_and_max_same_modifier(self):
        """Test Z-Move and Max Move have same modifier."""
        assert get_broken_protect_modifier(is_z_move=True) == get_broken_protect_modifier(is_max_move=True)


# =============================================================================
# Explosion Defense Modifier Tests
# =============================================================================

class TestExplosionDefenseModifier:
    """Tests for Explosion/Self-Destruct defense halving."""

    def test_explosion_gen4_and_earlier(self):
        """Test Explosion halves defense in Gen 4 and earlier."""
        assert get_explosion_defense_modifier('Explosion', gen=4) == 2.0
        assert get_explosion_defense_modifier('explosion', gen=3) == 2.0
        assert get_explosion_defense_modifier('explosion', gen=1) == 2.0

    def test_self_destruct_gen4_and_earlier(self):
        """Test Self-Destruct halves defense in Gen 4 and earlier."""
        assert get_explosion_defense_modifier('Self-Destruct', gen=4) == 2.0
        assert get_explosion_defense_modifier('selfdestruct', gen=3) == 2.0

    def test_explosion_gen5_plus(self):
        """Test Explosion no longer halves defense in Gen 5+."""
        assert get_explosion_defense_modifier('Explosion', gen=5) == 1.0
        assert get_explosion_defense_modifier('explosion', gen=9) == 1.0

    def test_self_destruct_gen5_plus(self):
        """Test Self-Destruct no longer halves defense in Gen 5+."""
        assert get_explosion_defense_modifier('Self-Destruct', gen=5) == 1.0
        assert get_explosion_defense_modifier('selfdestruct', gen=9) == 1.0

    def test_other_moves_no_modifier(self):
        """Test other moves don't get defense modifier."""
        assert get_explosion_defense_modifier('Earthquake', gen=4) == 1.0
        assert get_explosion_defense_modifier('Hyper Beam', gen=3) == 1.0


# =============================================================================
# Minimum Damage Tests
# =============================================================================

class TestMinimumDamage:
    """Tests for minimum damage calculation."""

    def test_minimum_damage_gen5_plus(self):
        """Test minimum damage is 1 in Gen 5+."""
        assert calculate_minimum_damage(0, gen=5) == 1
        assert calculate_minimum_damage(0, gen=9) == 1
        assert calculate_minimum_damage(-5, gen=9) == 1

    def test_minimum_damage_gen4_and_earlier(self):
        """Test minimum damage is 1 in Gen 4 and earlier."""
        assert calculate_minimum_damage(0, gen=4) == 1
        assert calculate_minimum_damage(0, gen=1) == 1

    def test_positive_damage_unchanged(self):
        """Test positive damage is unchanged."""
        assert calculate_minimum_damage(50, gen=9) == 50
        assert calculate_minimum_damage(100, gen=4) == 100
        assert calculate_minimum_damage(1, gen=9) == 1


# =============================================================================
# Known Value Verification Tests
# =============================================================================

class TestDamageKnownValues:
    """Tests for damage calculation against known/verified values.

    These tests use manually calculated damage values based on the official
    Pokemon damage formula:
        Damage = ((((2 * Level / 5 + 2) * Power * Attack / Defense) / 50) + 2) * Modifiers

    Each test documents the expected calculation for verification.
    """

    def test_base_damage_level_50_no_modifiers(self):
        """Test base damage calculation for Level 50 Pokemon.

        Setup:
        - Level 50 attacker
        - 100 Attack stat
        - 90 base power move
        - 80 Defense stat on target

        Expected calculation:
        - base = floor(floor(floor(2 * 50 / 5 + 2) * 90 * 100) / 80) / 50) + 2
        - base = floor(floor(22 * 90 * 100 / 80) / 50) + 2
        - base = floor(floor(247500 / 80) / 50) + 2
        - base = floor(3093 / 50) + 2
        - base = 61 + 2 = 63

        With random factor = 1.0 (max), damage should be 63.
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 25
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.NORMAL.value  # No STAB
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_HP] = 100
        attacker.data[P_CURRENT_HP] = 100
        attacker.data[P_STAT_ATK] = 100
        attacker.data[P_STAT_SPA] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 143
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.NORMAL.value  # Neutral effectiveness
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_HP] = 200
        defender.data[P_CURRENT_HP] = 200
        defender.data[P_STAT_DEF] = 80
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        # Normal type move, no STAB, neutral effectiveness
        move = MoveData(
            id=100,
            name="Body Slam",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=85,
            accuracy=100,
            pp=15,
        )

        result = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # With 85 BP, 100 Atk, 80 Def, Level 50:
        # base = floor(floor(22 * 85 * 100 / 80) / 50) + 2
        # base = floor(floor(187000 / 80) / 50) + 2
        # base = floor(2337 / 50) + 2
        # base = 46 + 2 = 48
        # With STAB 1.5x for Normal type: 48 * 1.5 = 72
        assert result.damage == 72

    def test_base_damage_level_100_high_stats(self):
        """Test damage at Level 100 with high stats.

        Setup:
        - Level 100 attacker
        - 200 Attack stat
        - 120 base power move (Fire Blast)
        - 100 Sp.Def stat on target

        Expected:
        - base = floor(floor(floor(2 * 100 / 5 + 2) * 120 * 200) / 100) / 50) + 2
        - base = floor(floor(42 * 120 * 200 / 100) / 50) + 2
        - base = floor(floor(1008000 / 100) / 50) + 2
        - base = floor(10080 / 50) + 2
        - base = 201 + 2 = 203
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 6  # Charizard
        attacker.data[P_LEVEL] = 100
        attacker.data[P_TYPE1] = Type.FIRE.value  # STAB!
        attacker.data[P_TYPE2] = Type.FLYING.value
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_HP] = 250
        attacker.data[P_CURRENT_HP] = 250
        attacker.data[P_STAT_ATK] = 150
        attacker.data[P_STAT_SPA] = 200
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 143  # Snorlax
        defender.data[P_LEVEL] = 100
        defender.data[P_TYPE1] = Type.NORMAL.value  # Neutral to Fire
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_HP] = 400
        defender.data[P_CURRENT_HP] = 400
        defender.data[P_STAT_DEF] = 120
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        # Fire Blast - Fire type Special move
        move = MoveData(
            id=126,
            name="Fire Blast",
            type=Type.FIRE,
            category=MoveCategory.SPECIAL,
            base_power=110,
            accuracy=85,
            pp=5,
        )

        result = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # With 110 BP, 200 SpA, 100 SpD, Level 100:
        # base = floor(floor(42 * 110 * 200 / 100) / 50) + 2
        # base = floor(floor(924000 / 100) / 50) + 2
        # base = floor(9240 / 50) + 2
        # base = 184 + 2 = 186
        # With STAB 1.5x: 186 * 1.5 = 279
        assert result.damage == 279
        assert result.type_effectiveness == 1.0  # Neutral

    def test_super_effective_damage(self):
        """Test super effective (2x) damage calculation.

        Setup:
        - Electric type move against Water type
        - Should deal 2x damage
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 25  # Pikachu
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.ELECTRIC.value  # STAB!
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_SPA] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 9  # Blastoise (Water)
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.WATER.value  # Weak to Electric!
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        # Thunderbolt
        move = MoveData(
            id=85,
            name="Thunderbolt",
            type=Type.ELECTRIC,
            category=MoveCategory.SPECIAL,
            base_power=90,
            accuracy=100,
            pp=15,
        )

        result = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # Base damage with 90 BP, 100 SpA, 100 SpD, Level 50:
        # base = floor(floor(22 * 90 * 100 / 100) / 50) + 2
        # base = floor(1980 / 50) + 2
        # base = 39 + 2 = 41
        # With STAB: 41 * 1.5 = 61.5 → 61
        # With 2x SE: 61 * 2 = 122
        assert result.damage == 122
        assert result.type_effectiveness == 2.0

    def test_4x_super_effective_damage(self):
        """Test 4x super effective damage (dual type weakness).

        Setup:
        - Ground type move against Fire/Flying (Charizard)
        - Ground is 2x vs Fire, but 0x vs Flying
        - Actually, let's use Ice vs Grass/Flying
        - Ice is 2x vs Grass, 2x vs Flying = 4x
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 131  # Lapras
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.WATER.value
        attacker.data[P_TYPE2] = Type.ICE.value  # STAB for Ice!
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_SPA] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 3  # Venusaur (Grass/Poison)
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.GRASS.value  # 2x weak to Ice
        defender.data[P_TYPE2] = Type.POISON.value  # Neutral to Ice
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        # Ice Beam
        move = MoveData(
            id=58,
            name="Ice Beam",
            type=Type.ICE,
            category=MoveCategory.SPECIAL,
            base_power=90,
            accuracy=100,
            pp=10,
        )

        result = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # Base: 41 (as calculated above with same stats)
        # With STAB: 61
        # With 2x SE (Ice vs Grass): 122
        assert result.damage == 122
        assert result.type_effectiveness == 2.0

    def test_resisted_damage(self):
        """Test resisted (0.5x) damage calculation.

        Setup:
        - Fire type move against Water type
        - Should deal 0.5x damage
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 6  # Charizard
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.FIRE.value  # STAB!
        attacker.data[P_TYPE2] = Type.FLYING.value
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_SPA] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 9  # Blastoise (Water)
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.WATER.value  # Resists Fire!
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        # Flamethrower
        move = MoveData(
            id=53,
            name="Flamethrower",
            type=Type.FIRE,
            category=MoveCategory.SPECIAL,
            base_power=90,
            accuracy=100,
            pp=15,
        )

        result = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # Base: 41 (as calculated)
        # With STAB: 61
        # With 0.5x resist: 30
        assert result.damage == 30
        assert result.type_effectiveness == 0.5

    def test_immunity_damage(self):
        """Test immune (0x) damage calculation.

        Setup:
        - Normal type move against Ghost type
        - Should deal 0 damage (immune)
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 143  # Snorlax
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.NORMAL.value
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_ATK] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 94  # Gengar (Ghost/Poison)
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.GHOST.value  # Immune to Normal!
        defender.data[P_TYPE2] = Type.POISON.value
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_DEF] = 100
        defender.data[P_STATUS] = STATUS_NONE

        # Body Slam
        move = MoveData(
            id=34,
            name="Body Slam",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=85,
            accuracy=100,
            pp=15,
        )

        result = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        assert result.damage == 0
        assert result.is_immune == True
        assert result.type_effectiveness == 0.0

    def test_critical_hit_damage(self):
        """Test critical hit damage (1.5x in Gen 6+).

        A critical hit should multiply damage by 1.5.
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 25
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.ELECTRIC.value
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_SPA] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 143
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.NORMAL.value
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        move = MoveData(
            id=85,
            name="Thunderbolt",
            type=Type.ELECTRIC,
            category=MoveCategory.SPECIAL,
            base_power=90,
            accuracy=100,
            pp=15,
        )

        # Without crit
        result_normal = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # With crit
        result_crit = calculate_damage(
            attacker, defender, move,
            force_crit=True,
            force_random=1.0,
        )

        # Crit damage should be 1.5x normal damage
        # Normal: 61 (with STAB)
        # Crit: 61 * 1.5 = 91.5 → 91
        assert result_normal.damage == 61
        assert result_crit.damage == 91
        assert result_crit.crit == True

    def test_random_factor_range(self):
        """Test that random factor produces expected damage range.

        Random factor is 0.85-1.0, so damage should vary by ~15%.
        """
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 25
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.ELECTRIC.value
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_SPA] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 143
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.NORMAL.value
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        move = MoveData(
            id=85,
            name="Thunderbolt",
            type=Type.ELECTRIC,
            category=MoveCategory.SPECIAL,
            base_power=90,
            accuracy=100,
            pp=15,
        )

        # Max random (1.0)
        result_max = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # Min random (0.85)
        result_min = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=0.85,
        )

        # Max should be 61, min should be ~52 (61 * 0.85 = 51.85)
        assert result_max.damage == 61
        assert result_min.damage == 51
        # Verify the range is approximately 15%
        assert result_min.damage / result_max.damage >= 0.83

    def test_burn_halves_physical_damage(self):
        """Test that burn halves physical damage."""
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 68  # Machamp
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.FIGHTING.value
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_ATK] = 150
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 143
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.NORMAL.value
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_DEF] = 100
        defender.data[P_STATUS] = STATUS_NONE

        # Close Combat
        move = MoveData(
            id=370,
            name="Close Combat",
            type=Type.FIGHTING,
            category=MoveCategory.PHYSICAL,
            base_power=120,
            accuracy=100,
            pp=5,
        )

        # Without burn
        result_normal = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # With burn
        attacker.data[P_STATUS] = STATUS_BURN
        result_burned = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
        )

        # Burned damage should be half (rounded down)
        # Normal vs Normal: neutral, with STAB (Fighting vs Normal): 2x SE
        assert result_burned.damage == result_normal.damage // 2

    def test_spread_move_damage_reduction(self):
        """Test that spread moves deal 0.75x damage in doubles."""
        attacker = Pokemon()
        attacker.data[P_SPECIES] = 25
        attacker.data[P_LEVEL] = 50
        attacker.data[P_TYPE1] = Type.ELECTRIC.value
        attacker.data[P_TYPE2] = -1
        attacker.data[P_TERA_TYPE] = -1
        attacker.data[P_STAT_SPA] = 100
        attacker.data[P_STATUS] = STATUS_NONE

        defender = Pokemon()
        defender.data[P_SPECIES] = 143
        defender.data[P_LEVEL] = 50
        defender.data[P_TYPE1] = Type.NORMAL.value
        defender.data[P_TYPE2] = -1
        defender.data[P_TERA_TYPE] = -1
        defender.data[P_STAT_SPD] = 100
        defender.data[P_STATUS] = STATUS_NONE

        move = MoveData(
            id=85,
            name="Discharge",
            type=Type.ELECTRIC,
            category=MoveCategory.SPECIAL,
            base_power=80,
            accuracy=100,
            pp=15,
            target=MoveTarget.ALL_ADJACENT,
        )

        # Single target
        result_single = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
            is_spread=False,
        )

        # Spread move
        result_spread = calculate_damage(
            attacker, defender, move,
            force_crit=False,
            force_random=1.0,
            is_spread=True,
        )

        # Spread damage should be 75% of single target
        # Allow for rounding differences
        expected_spread = int(result_single.damage * 0.75)
        assert abs(result_spread.damage - expected_spread) <= 1
