"""Tests for core/layout.py - Packed Pokemon array layout definitions.

Tests cover:
- Pokemon array index constants
- Status constants
- Stat stage multiplier functions
- Accuracy/evasion multiplier functions
- Index ranges (STAT_INDICES, STAGE_INDICES, etc.)
"""
import pytest

from core.layout import (
    # Array size
    POKEMON_ARRAY_SIZE,
    # Identity indices
    P_SPECIES, P_LEVEL, P_NATURE, P_ABILITY, P_ITEM,
    P_TYPE1, P_TYPE2, P_TERA_TYPE,
    # Stat indices
    P_STAT_HP, P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    # Battle state indices
    P_CURRENT_HP, P_STATUS, P_STATUS_COUNTER,
    # Stage indices
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
    P_STAGE_ACC, P_STAGE_EVA,
    # Move indices
    P_MOVE1, P_MOVE2, P_MOVE3, P_MOVE4,
    # PP indices
    P_PP1, P_PP2, P_PP3, P_PP4,
    # IV indices
    P_IV_HP, P_IV_ATK, P_IV_DEF, P_IV_SPA, P_IV_SPD, P_IV_SPE,
    # EV indices
    P_EV_HP, P_EV_ATK, P_EV_DEF, P_EV_SPA, P_EV_SPD, P_EV_SPE,
    # Volatile flags
    P_VOL_PROTECT, P_VOL_SUBSTITUTE, P_VOL_SUBSTITUTE_HP,
    P_VOL_ENCORE, P_VOL_TAUNT, P_VOL_TORMENT,
    P_VOL_DISABLE, P_VOL_DISABLE_TURNS, P_VOL_CONFUSION,
    P_VOL_ATTRACT, P_VOL_FLINCH, P_VOL_FOCUS_ENERGY,
    P_VOL_LEECH_SEED, P_VOL_CURSE, P_VOL_PERISH_COUNT,
    P_VOL_TRAPPED, P_VOL_TRAPPED_TURNS, P_VOL_MUST_RECHARGE,
    P_VOL_BIDE, P_VOL_BIDE_DAMAGE, P_VOL_CHARGING, P_VOL_CHARGING_MOVE,
    P_VOL_CHOICE_LOCKED, P_VOL_LAST_MOVE, P_VOL_LAST_MOVE_TURN,
    P_VOL_TIMES_ATTACKED, P_VOL_STOCKPILE, P_VOL_FLASH_FIRE,
    P_VOL_ABILITY_SUPPRESSED, P_VOL_TRANSFORM, P_VOL_MINIMIZE,
    P_VOL_DEFENSE_CURL, P_VOL_DESTINY_BOND, P_VOL_GRUDGE,
    P_VOL_INGRAIN, P_VOL_MAGNET_RISE, P_VOL_AQUA_RING,
    P_VOL_HEAL_BLOCK, P_VOL_EMBARGO, P_VOL_POWER_TRICK,
    P_VOL_TYPE_ADDED, P_VOL_SMACKED_DOWN, P_VOL_TELEKINESIS,
    # Status constants
    STATUS_NONE, STATUS_BURN, STATUS_FREEZE, STATUS_PARALYSIS,
    STATUS_POISON, STATUS_BADLY_POISONED, STATUS_SLEEP,
    STATUS_NAMES,
    # Multiplier tables and functions
    STAGE_MULTIPLIERS, ACC_EVA_MULTIPLIERS,
    get_stage_multiplier, get_acc_eva_multiplier,
    # Index ranges
    STAT_INDICES, STAGE_INDICES, MOVE_INDICES, PP_INDICES,
    IV_INDICES, EV_INDICES,
)


class TestArraySize:
    """Tests for POKEMON_ARRAY_SIZE constant."""

    def test_array_size_value(self):
        """Array size should be 87 per docstring."""
        assert POKEMON_ARRAY_SIZE == 87

    def test_array_size_covers_all_volatile_flags(self):
        """Array size should accommodate all defined volatile flags."""
        # The last volatile flag is P_VOL_TELEKINESIS at index 86
        assert P_VOL_TELEKINESIS < POKEMON_ARRAY_SIZE


class TestIdentityIndices:
    """Tests for identity index constants (0-7)."""

    def test_identity_indices_range(self):
        """Identity indices should be 0-7."""
        assert P_SPECIES == 0
        assert P_LEVEL == 1
        assert P_NATURE == 2
        assert P_ABILITY == 3
        assert P_ITEM == 4
        assert P_TYPE1 == 5
        assert P_TYPE2 == 6
        assert P_TERA_TYPE == 7

    def test_identity_indices_are_sequential(self):
        """Identity indices should be sequential."""
        indices = [P_SPECIES, P_LEVEL, P_NATURE, P_ABILITY, P_ITEM,
                   P_TYPE1, P_TYPE2, P_TERA_TYPE]
        assert indices == list(range(8))


class TestStatIndices:
    """Tests for calculated stat index constants (8-13)."""

    def test_stat_indices_range(self):
        """Stat indices should be 8-13."""
        assert P_STAT_HP == 8
        assert P_STAT_ATK == 9
        assert P_STAT_DEF == 10
        assert P_STAT_SPA == 11
        assert P_STAT_SPD == 12
        assert P_STAT_SPE == 13

    def test_stat_indices_are_sequential(self):
        """Stat indices should be sequential."""
        indices = [P_STAT_HP, P_STAT_ATK, P_STAT_DEF,
                   P_STAT_SPA, P_STAT_SPD, P_STAT_SPE]
        assert indices == list(range(8, 14))

    def test_stat_indices_tuple(self):
        """STAT_INDICES should contain all stat indices."""
        assert STAT_INDICES == (P_STAT_HP, P_STAT_ATK, P_STAT_DEF,
                                P_STAT_SPA, P_STAT_SPD, P_STAT_SPE)


class TestBattleStateIndices:
    """Tests for battle state index constants (14-16)."""

    def test_battle_state_indices_range(self):
        """Battle state indices should be 14-16."""
        assert P_CURRENT_HP == 14
        assert P_STATUS == 15
        assert P_STATUS_COUNTER == 16


class TestStageIndices:
    """Tests for stat stage index constants (17-23)."""

    def test_stage_indices_range(self):
        """Stage indices should be 17-23."""
        assert P_STAGE_ATK == 17
        assert P_STAGE_DEF == 18
        assert P_STAGE_SPA == 19
        assert P_STAGE_SPD == 20
        assert P_STAGE_SPE == 21
        assert P_STAGE_ACC == 22
        assert P_STAGE_EVA == 23

    def test_stage_indices_tuple(self):
        """STAGE_INDICES should contain combat stat stages (not Acc/Eva)."""
        assert STAGE_INDICES == (P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA,
                                 P_STAGE_SPD, P_STAGE_SPE)


class TestMoveIndices:
    """Tests for move slot index constants (24-27)."""

    def test_move_indices_range(self):
        """Move indices should be 24-27."""
        assert P_MOVE1 == 24
        assert P_MOVE2 == 25
        assert P_MOVE3 == 26
        assert P_MOVE4 == 27

    def test_move_indices_tuple(self):
        """MOVE_INDICES should contain all move slot indices."""
        assert MOVE_INDICES == (P_MOVE1, P_MOVE2, P_MOVE3, P_MOVE4)


class TestPPIndices:
    """Tests for PP index constants (28-31)."""

    def test_pp_indices_range(self):
        """PP indices should be 28-31."""
        assert P_PP1 == 28
        assert P_PP2 == 29
        assert P_PP3 == 30
        assert P_PP4 == 31

    def test_pp_indices_tuple(self):
        """PP_INDICES should contain all PP slot indices."""
        assert PP_INDICES == (P_PP1, P_PP2, P_PP3, P_PP4)

    def test_pp_indices_match_move_indices(self):
        """PP indices should have same offset from move indices."""
        for i in range(4):
            assert PP_INDICES[i] == MOVE_INDICES[i] + 4


class TestIVIndices:
    """Tests for IV index constants (32-37)."""

    def test_iv_indices_range(self):
        """IV indices should be 32-37."""
        assert P_IV_HP == 32
        assert P_IV_ATK == 33
        assert P_IV_DEF == 34
        assert P_IV_SPA == 35
        assert P_IV_SPD == 36
        assert P_IV_SPE == 37

    def test_iv_indices_tuple(self):
        """IV_INDICES should contain all IV indices."""
        assert IV_INDICES == (P_IV_HP, P_IV_ATK, P_IV_DEF,
                              P_IV_SPA, P_IV_SPD, P_IV_SPE)


class TestEVIndices:
    """Tests for EV index constants (38-43)."""

    def test_ev_indices_range(self):
        """EV indices should be 38-43."""
        assert P_EV_HP == 38
        assert P_EV_ATK == 39
        assert P_EV_DEF == 40
        assert P_EV_SPA == 41
        assert P_EV_SPD == 42
        assert P_EV_SPE == 43

    def test_ev_indices_tuple(self):
        """EV_INDICES should contain all EV indices."""
        assert EV_INDICES == (P_EV_HP, P_EV_ATK, P_EV_DEF,
                              P_EV_SPA, P_EV_SPD, P_EV_SPE)

    def test_ev_indices_follow_iv_indices(self):
        """EV indices should immediately follow IV indices."""
        for i in range(6):
            assert EV_INDICES[i] == IV_INDICES[i] + 6


class TestVolatileFlagIndices:
    """Tests for volatile flag index constants (44+)."""

    def test_volatile_flags_start_at_44(self):
        """Volatile flags should start at index 44."""
        assert P_VOL_PROTECT == 44

    def test_volatile_flags_are_sequential(self):
        """Volatile flags should be sequential without gaps."""
        volatile_flags = [
            P_VOL_PROTECT, P_VOL_SUBSTITUTE, P_VOL_SUBSTITUTE_HP,
            P_VOL_ENCORE, P_VOL_TAUNT, P_VOL_TORMENT,
            P_VOL_DISABLE, P_VOL_DISABLE_TURNS, P_VOL_CONFUSION,
            P_VOL_ATTRACT, P_VOL_FLINCH, P_VOL_FOCUS_ENERGY,
            P_VOL_LEECH_SEED, P_VOL_CURSE, P_VOL_PERISH_COUNT,
            P_VOL_TRAPPED, P_VOL_TRAPPED_TURNS, P_VOL_MUST_RECHARGE,
            P_VOL_BIDE, P_VOL_BIDE_DAMAGE, P_VOL_CHARGING, P_VOL_CHARGING_MOVE,
            P_VOL_CHOICE_LOCKED, P_VOL_LAST_MOVE, P_VOL_LAST_MOVE_TURN,
            P_VOL_TIMES_ATTACKED, P_VOL_STOCKPILE, P_VOL_FLASH_FIRE,
            P_VOL_ABILITY_SUPPRESSED, P_VOL_TRANSFORM, P_VOL_MINIMIZE,
            P_VOL_DEFENSE_CURL, P_VOL_DESTINY_BOND, P_VOL_GRUDGE,
            P_VOL_INGRAIN, P_VOL_MAGNET_RISE, P_VOL_AQUA_RING,
            P_VOL_HEAL_BLOCK, P_VOL_EMBARGO, P_VOL_POWER_TRICK,
            P_VOL_TYPE_ADDED, P_VOL_SMACKED_DOWN, P_VOL_TELEKINESIS,
        ]
        expected = list(range(44, 44 + len(volatile_flags)))
        assert volatile_flags == expected

    def test_last_volatile_flag(self):
        """Last volatile flag should be P_VOL_TELEKINESIS at 86."""
        assert P_VOL_TELEKINESIS == 86


class TestNoIndexOverlap:
    """Tests ensuring no index constants overlap."""

    def test_all_indices_unique(self):
        """All index constants should be unique."""
        all_indices = [
            # Identity
            P_SPECIES, P_LEVEL, P_NATURE, P_ABILITY, P_ITEM,
            P_TYPE1, P_TYPE2, P_TERA_TYPE,
            # Stats
            P_STAT_HP, P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
            # Battle state
            P_CURRENT_HP, P_STATUS, P_STATUS_COUNTER,
            # Stages
            P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
            P_STAGE_ACC, P_STAGE_EVA,
            # Moves
            P_MOVE1, P_MOVE2, P_MOVE3, P_MOVE4,
            # PP
            P_PP1, P_PP2, P_PP3, P_PP4,
            # IVs
            P_IV_HP, P_IV_ATK, P_IV_DEF, P_IV_SPA, P_IV_SPD, P_IV_SPE,
            # EVs
            P_EV_HP, P_EV_ATK, P_EV_DEF, P_EV_SPA, P_EV_SPD, P_EV_SPE,
            # Volatile flags (just a sample)
            P_VOL_PROTECT, P_VOL_SUBSTITUTE, P_VOL_TELEKINESIS,
        ]
        assert len(all_indices) == len(set(all_indices))

    def test_indices_are_non_negative(self):
        """All indices should be non-negative."""
        indices = list(STAT_INDICES) + list(STAGE_INDICES) + list(MOVE_INDICES)
        indices += list(PP_INDICES) + list(IV_INDICES) + list(EV_INDICES)
        for idx in indices:
            assert idx >= 0


class TestStatusConstants:
    """Tests for status condition constants."""

    def test_status_values(self):
        """Status constants should have correct values."""
        assert STATUS_NONE == 0
        assert STATUS_BURN == 1
        assert STATUS_FREEZE == 2
        assert STATUS_PARALYSIS == 3
        assert STATUS_POISON == 4
        assert STATUS_BADLY_POISONED == 5
        assert STATUS_SLEEP == 6

    def test_status_values_are_unique(self):
        """All status values should be unique."""
        statuses = [STATUS_NONE, STATUS_BURN, STATUS_FREEZE, STATUS_PARALYSIS,
                    STATUS_POISON, STATUS_BADLY_POISONED, STATUS_SLEEP]
        assert len(statuses) == len(set(statuses))

    def test_status_names_mapping(self):
        """STATUS_NAMES should map all status values to names."""
        assert STATUS_NAMES[STATUS_NONE] == "none"
        assert STATUS_NAMES[STATUS_BURN] == "brn"
        assert STATUS_NAMES[STATUS_FREEZE] == "frz"
        assert STATUS_NAMES[STATUS_PARALYSIS] == "par"
        assert STATUS_NAMES[STATUS_POISON] == "psn"
        assert STATUS_NAMES[STATUS_BADLY_POISONED] == "tox"
        assert STATUS_NAMES[STATUS_SLEEP] == "slp"

    def test_all_statuses_have_names(self):
        """All status constants should have name mappings."""
        statuses = [STATUS_NONE, STATUS_BURN, STATUS_FREEZE, STATUS_PARALYSIS,
                    STATUS_POISON, STATUS_BADLY_POISONED, STATUS_SLEEP]
        for status in statuses:
            assert status in STATUS_NAMES


class TestStageMultipliers:
    """Tests for STAGE_MULTIPLIERS table."""

    def test_stage_multipliers_length(self):
        """STAGE_MULTIPLIERS should have 13 entries (-6 to +6)."""
        assert len(STAGE_MULTIPLIERS) == 13

    def test_stage_multipliers_structure(self):
        """Each entry should be a (numerator, denominator) tuple."""
        for entry in STAGE_MULTIPLIERS:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            assert entry[0] > 0
            assert entry[1] > 0

    def test_stage_zero_is_neutral(self):
        """Stage 0 (index 6) should give 1.0x multiplier."""
        num, denom = STAGE_MULTIPLIERS[6]
        assert num / denom == 1.0

    def test_stage_plus_six_is_max(self):
        """Stage +6 (index 12) should give 4.0x multiplier."""
        num, denom = STAGE_MULTIPLIERS[12]
        assert num / denom == 4.0

    def test_stage_minus_six_is_min(self):
        """Stage -6 (index 0) should give 0.25x multiplier."""
        num, denom = STAGE_MULTIPLIERS[0]
        assert num / denom == 0.25

    def test_stage_multipliers_increasing(self):
        """Stage multipliers should increase with stage."""
        prev_mult = 0
        for num, denom in STAGE_MULTIPLIERS:
            mult = num / denom
            assert mult > prev_mult
            prev_mult = mult


class TestAccEvaMultipliers:
    """Tests for ACC_EVA_MULTIPLIERS table."""

    def test_acc_eva_multipliers_length(self):
        """ACC_EVA_MULTIPLIERS should have 13 entries (-6 to +6)."""
        assert len(ACC_EVA_MULTIPLIERS) == 13

    def test_acc_eva_multipliers_structure(self):
        """Each entry should be a (numerator, denominator) tuple."""
        for entry in ACC_EVA_MULTIPLIERS:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            assert entry[0] > 0
            assert entry[1] > 0

    def test_acc_eva_zero_is_neutral(self):
        """Stage 0 (index 6) should give 1.0x multiplier."""
        num, denom = ACC_EVA_MULTIPLIERS[6]
        assert num / denom == 1.0

    def test_acc_eva_plus_six_is_max(self):
        """Stage +6 (index 12) should give 3.0x multiplier."""
        num, denom = ACC_EVA_MULTIPLIERS[12]
        assert num / denom == 3.0

    def test_acc_eva_minus_six_is_min(self):
        """Stage -6 (index 0) should give 0.33x multiplier."""
        num, denom = ACC_EVA_MULTIPLIERS[0]
        assert abs(num / denom - (3/9)) < 0.01

    def test_acc_eva_different_from_stat(self):
        """Accuracy/Evasion multipliers should differ from stat multipliers."""
        # At +6, acc/eva is 3.0x but stat is 4.0x
        stat_mult = STAGE_MULTIPLIERS[12][0] / STAGE_MULTIPLIERS[12][1]
        acc_mult = ACC_EVA_MULTIPLIERS[12][0] / ACC_EVA_MULTIPLIERS[12][1]
        assert stat_mult != acc_mult


class TestGetStageMultiplier:
    """Tests for get_stage_multiplier function."""

    def test_get_stage_multiplier_zero(self):
        """Stage 0 should return 1.0."""
        assert get_stage_multiplier(0) == 1.0

    def test_get_stage_multiplier_positive(self):
        """Positive stages should return > 1.0."""
        for stage in range(1, 7):
            assert get_stage_multiplier(stage) > 1.0

    def test_get_stage_multiplier_negative(self):
        """Negative stages should return < 1.0."""
        for stage in range(-6, 0):
            assert get_stage_multiplier(stage) < 1.0

    def test_get_stage_multiplier_plus_one(self):
        """Stage +1 should return 1.5."""
        assert get_stage_multiplier(1) == 1.5

    def test_get_stage_multiplier_minus_one(self):
        """Stage -1 should return 0.667 (2/3)."""
        assert abs(get_stage_multiplier(-1) - (2/3)) < 0.001

    def test_get_stage_multiplier_plus_two(self):
        """Stage +2 should return 2.0."""
        assert get_stage_multiplier(2) == 2.0

    def test_get_stage_multiplier_minus_two(self):
        """Stage -2 should return 0.5."""
        assert get_stage_multiplier(-2) == 0.5

    def test_get_stage_multiplier_plus_six(self):
        """Stage +6 should return 4.0."""
        assert get_stage_multiplier(6) == 4.0

    def test_get_stage_multiplier_minus_six(self):
        """Stage -6 should return 0.25."""
        assert get_stage_multiplier(-6) == 0.25

    def test_get_stage_multiplier_clamps_high(self):
        """Stages above +6 should be clamped to +6."""
        assert get_stage_multiplier(7) == get_stage_multiplier(6)
        assert get_stage_multiplier(10) == get_stage_multiplier(6)
        assert get_stage_multiplier(100) == get_stage_multiplier(6)

    def test_get_stage_multiplier_clamps_low(self):
        """Stages below -6 should be clamped to -6."""
        assert get_stage_multiplier(-7) == get_stage_multiplier(-6)
        assert get_stage_multiplier(-10) == get_stage_multiplier(-6)
        assert get_stage_multiplier(-100) == get_stage_multiplier(-6)


class TestGetAccEvaMultiplier:
    """Tests for get_acc_eva_multiplier function."""

    def test_get_acc_eva_multiplier_zero(self):
        """Stage 0 should return 1.0."""
        assert get_acc_eva_multiplier(0) == 1.0

    def test_get_acc_eva_multiplier_positive(self):
        """Positive stages should return > 1.0."""
        for stage in range(1, 7):
            assert get_acc_eva_multiplier(stage) > 1.0

    def test_get_acc_eva_multiplier_negative(self):
        """Negative stages should return < 1.0."""
        for stage in range(-6, 0):
            assert get_acc_eva_multiplier(stage) < 1.0

    def test_get_acc_eva_multiplier_plus_one(self):
        """Stage +1 should return 1.333 (4/3)."""
        assert abs(get_acc_eva_multiplier(1) - (4/3)) < 0.001

    def test_get_acc_eva_multiplier_minus_one(self):
        """Stage -1 should return 0.75 (3/4)."""
        assert get_acc_eva_multiplier(-1) == 0.75

    def test_get_acc_eva_multiplier_plus_six(self):
        """Stage +6 should return 3.0."""
        assert get_acc_eva_multiplier(6) == 3.0

    def test_get_acc_eva_multiplier_minus_six(self):
        """Stage -6 should return 0.333 (3/9)."""
        assert abs(get_acc_eva_multiplier(-6) - (3/9)) < 0.001

    def test_get_acc_eva_multiplier_clamps_high(self):
        """Stages above +6 should be clamped to +6."""
        assert get_acc_eva_multiplier(7) == get_acc_eva_multiplier(6)
        assert get_acc_eva_multiplier(100) == get_acc_eva_multiplier(6)

    def test_get_acc_eva_multiplier_clamps_low(self):
        """Stages below -6 should be clamped to -6."""
        assert get_acc_eva_multiplier(-7) == get_acc_eva_multiplier(-6)
        assert get_acc_eva_multiplier(-100) == get_acc_eva_multiplier(-6)


class TestMultiplierComparison:
    """Tests comparing stat multipliers with acc/eva multipliers."""

    def test_acc_eva_less_extreme_at_max(self):
        """Acc/Eva multipliers are less extreme than stat multipliers at +6."""
        stat_max = get_stage_multiplier(6)
        acc_max = get_acc_eva_multiplier(6)
        assert acc_max < stat_max  # 3.0 < 4.0

    def test_acc_eva_less_extreme_at_min(self):
        """Acc/Eva multipliers are less extreme than stat multipliers at -6."""
        stat_min = get_stage_multiplier(-6)
        acc_min = get_acc_eva_multiplier(-6)
        assert acc_min > stat_min  # 0.333 > 0.25

    def test_both_neutral_at_zero(self):
        """Both multiplier types should be 1.0 at stage 0."""
        assert get_stage_multiplier(0) == get_acc_eva_multiplier(0) == 1.0


class TestIndexRangesTuples:
    """Tests for index range tuples."""

    def test_stat_indices_length(self):
        """STAT_INDICES should have 6 entries."""
        assert len(STAT_INDICES) == 6

    def test_stage_indices_length(self):
        """STAGE_INDICES should have 5 entries (no HP stage)."""
        assert len(STAGE_INDICES) == 5

    def test_move_indices_length(self):
        """MOVE_INDICES should have 4 entries."""
        assert len(MOVE_INDICES) == 4

    def test_pp_indices_length(self):
        """PP_INDICES should have 4 entries."""
        assert len(PP_INDICES) == 4

    def test_iv_indices_length(self):
        """IV_INDICES should have 6 entries."""
        assert len(IV_INDICES) == 6

    def test_ev_indices_length(self):
        """EV_INDICES should have 6 entries."""
        assert len(EV_INDICES) == 6

    def test_indices_are_tuples(self):
        """All index ranges should be tuples (immutable)."""
        assert isinstance(STAT_INDICES, tuple)
        assert isinstance(STAGE_INDICES, tuple)
        assert isinstance(MOVE_INDICES, tuple)
        assert isinstance(PP_INDICES, tuple)
        assert isinstance(IV_INDICES, tuple)
        assert isinstance(EV_INDICES, tuple)
