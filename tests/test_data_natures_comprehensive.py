"""Comprehensive tests for data/natures.py based on nature.md documentation.

Tests cover:
- All 25 natures with correct stat effects
- All 5 neutral natures
- Stat modifier calculations (1.1x boost, 0.9x penalty)
- HP is never affected by nature
- Nature-to-stat mapping completeness
"""
import pytest

from data.natures import (
    Stat,
    Nature,
    NatureData,
    NATURE_DATA,
    NATURE_BY_NAME,
    get_nature_modifier,
    get_nature_modifiers,
)


class TestAllNaturesDefined:
    """Verify all 25 natures are defined correctly."""

    def test_exactly_25_natures(self):
        """There should be exactly 25 natures."""
        assert len(Nature) == 25

    def test_exactly_25_nature_data_entries(self):
        """NATURE_DATA should have 25 entries."""
        assert len(NATURE_DATA) == 25


class TestNeutralNatures:
    """Test the 5 neutral natures (no stat change)."""

    def test_hardy_is_neutral(self):
        """Hardy affects Atk/Atk - neutral."""
        assert NATURE_DATA[Nature.HARDY].is_neutral

    def test_docile_is_neutral(self):
        """Docile affects Def/Def - neutral."""
        assert NATURE_DATA[Nature.DOCILE].is_neutral

    def test_serious_is_neutral(self):
        """Serious affects Spe/Spe - neutral."""
        assert NATURE_DATA[Nature.SERIOUS].is_neutral

    def test_bashful_is_neutral(self):
        """Bashful affects SpA/SpA - neutral."""
        assert NATURE_DATA[Nature.BASHFUL].is_neutral

    def test_quirky_is_neutral(self):
        """Quirky affects SpD/SpD - neutral."""
        assert NATURE_DATA[Nature.QUIRKY].is_neutral

    def test_exactly_5_neutral_natures(self):
        """There should be exactly 5 neutral natures."""
        neutral_count = sum(1 for data in NATURE_DATA.values() if data.is_neutral)
        assert neutral_count == 5

    def test_neutral_natures_all_stats_1_0(self):
        """Neutral natures should return 1.0 for all stats."""
        neutral_natures = [Nature.HARDY, Nature.DOCILE, Nature.SERIOUS,
                          Nature.BASHFUL, Nature.QUIRKY]
        for nature in neutral_natures:
            for stat in Stat:
                assert get_nature_modifier(nature, stat) == 1.0


class TestAttackBoostingNatures:
    """Test natures that boost Attack."""

    def test_lonely_boosts_attack_lowers_defense(self):
        """Lonely: +Atk, -Def."""
        assert get_nature_modifier(Nature.LONELY, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.LONELY, Stat.DEF) == 0.9
        assert get_nature_modifier(Nature.LONELY, Stat.SPA) == 1.0
        assert get_nature_modifier(Nature.LONELY, Stat.SPD) == 1.0
        assert get_nature_modifier(Nature.LONELY, Stat.SPE) == 1.0

    def test_brave_boosts_attack_lowers_speed(self):
        """Brave: +Atk, -Spe."""
        assert get_nature_modifier(Nature.BRAVE, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.BRAVE, Stat.SPE) == 0.9

    def test_adamant_boosts_attack_lowers_spatk(self):
        """Adamant: +Atk, -SpA."""
        assert get_nature_modifier(Nature.ADAMANT, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPA) == 0.9

    def test_naughty_boosts_attack_lowers_spdef(self):
        """Naughty: +Atk, -SpD."""
        assert get_nature_modifier(Nature.NAUGHTY, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.NAUGHTY, Stat.SPD) == 0.9


class TestDefenseBoostingNatures:
    """Test natures that boost Defense."""

    def test_bold_boosts_defense_lowers_attack(self):
        """Bold: +Def, -Atk."""
        assert get_nature_modifier(Nature.BOLD, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.BOLD, Stat.ATK) == 0.9

    def test_relaxed_boosts_defense_lowers_speed(self):
        """Relaxed: +Def, -Spe."""
        assert get_nature_modifier(Nature.RELAXED, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.RELAXED, Stat.SPE) == 0.9

    def test_impish_boosts_defense_lowers_spatk(self):
        """Impish: +Def, -SpA."""
        assert get_nature_modifier(Nature.IMPISH, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.IMPISH, Stat.SPA) == 0.9

    def test_lax_boosts_defense_lowers_spdef(self):
        """Lax: +Def, -SpD."""
        assert get_nature_modifier(Nature.LAX, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.LAX, Stat.SPD) == 0.9


class TestSpecialAttackBoostingNatures:
    """Test natures that boost Special Attack."""

    def test_modest_boosts_spatk_lowers_attack(self):
        """Modest: +SpA, -Atk."""
        assert get_nature_modifier(Nature.MODEST, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.MODEST, Stat.ATK) == 0.9

    def test_mild_boosts_spatk_lowers_defense(self):
        """Mild: +SpA, -Def."""
        assert get_nature_modifier(Nature.MILD, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.MILD, Stat.DEF) == 0.9

    def test_quiet_boosts_spatk_lowers_speed(self):
        """Quiet: +SpA, -Spe."""
        assert get_nature_modifier(Nature.QUIET, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.QUIET, Stat.SPE) == 0.9

    def test_rash_boosts_spatk_lowers_spdef(self):
        """Rash: +SpA, -SpD."""
        assert get_nature_modifier(Nature.RASH, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.RASH, Stat.SPD) == 0.9


class TestSpecialDefenseBoostingNatures:
    """Test natures that boost Special Defense."""

    def test_calm_boosts_spdef_lowers_attack(self):
        """Calm: +SpD, -Atk."""
        assert get_nature_modifier(Nature.CALM, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.CALM, Stat.ATK) == 0.9

    def test_gentle_boosts_spdef_lowers_defense(self):
        """Gentle: +SpD, -Def."""
        assert get_nature_modifier(Nature.GENTLE, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.GENTLE, Stat.DEF) == 0.9

    def test_sassy_boosts_spdef_lowers_speed(self):
        """Sassy: +SpD, -Spe."""
        assert get_nature_modifier(Nature.SASSY, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.SASSY, Stat.SPE) == 0.9

    def test_careful_boosts_spdef_lowers_spatk(self):
        """Careful: +SpD, -SpA."""
        assert get_nature_modifier(Nature.CAREFUL, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.CAREFUL, Stat.SPA) == 0.9


class TestSpeedBoostingNatures:
    """Test natures that boost Speed."""

    def test_timid_boosts_speed_lowers_attack(self):
        """Timid: +Spe, -Atk."""
        assert get_nature_modifier(Nature.TIMID, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.TIMID, Stat.ATK) == 0.9

    def test_hasty_boosts_speed_lowers_defense(self):
        """Hasty: +Spe, -Def."""
        assert get_nature_modifier(Nature.HASTY, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.HASTY, Stat.DEF) == 0.9

    def test_jolly_boosts_speed_lowers_spatk(self):
        """Jolly: +Spe, -SpA."""
        assert get_nature_modifier(Nature.JOLLY, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.JOLLY, Stat.SPA) == 0.9

    def test_naive_boosts_speed_lowers_spdef(self):
        """Naive: +Spe, -SpD."""
        assert get_nature_modifier(Nature.NAIVE, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.NAIVE, Stat.SPD) == 0.9


class TestHPNeverAffected:
    """Test that HP is never affected by any nature."""

    def test_hp_unaffected_by_all_natures(self):
        """HP should always have a 1.0 modifier regardless of nature."""
        for nature in Nature:
            modifier = get_nature_modifier(nature, Stat.HP)
            assert modifier == 1.0, f"{nature.name} should not modify HP"


class TestNatureModifierValues:
    """Test that modifier values are exactly correct."""

    def test_boost_is_exactly_1_1(self):
        """Boosted stats should be exactly 1.1x."""
        assert get_nature_modifier(Nature.ADAMANT, Stat.ATK) == 1.1

    def test_penalty_is_exactly_0_9(self):
        """Penalized stats should be exactly 0.9x."""
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPA) == 0.9

    def test_neutral_is_exactly_1_0(self):
        """Unaffected stats should be exactly 1.0x."""
        assert get_nature_modifier(Nature.ADAMANT, Stat.DEF) == 1.0
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPD) == 1.0
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPE) == 1.0


class TestGetNatureModifiers:
    """Test get_nature_modifiers function returning all stat modifiers."""

    def test_returns_all_six_stats(self):
        """Should return modifiers for all 6 stats."""
        modifiers = get_nature_modifiers(Nature.ADAMANT)
        assert len(modifiers) == 6
        assert Stat.HP in modifiers
        assert Stat.ATK in modifiers
        assert Stat.DEF in modifiers
        assert Stat.SPA in modifiers
        assert Stat.SPD in modifiers
        assert Stat.SPE in modifiers

    def test_adamant_complete_modifiers(self):
        """Adamant should have correct modifiers for all stats."""
        modifiers = get_nature_modifiers(Nature.ADAMANT)
        assert modifiers[Stat.HP] == 1.0
        assert modifiers[Stat.ATK] == 1.1
        assert modifiers[Stat.DEF] == 1.0
        assert modifiers[Stat.SPA] == 0.9
        assert modifiers[Stat.SPD] == 1.0
        assert modifiers[Stat.SPE] == 1.0

    def test_timid_complete_modifiers(self):
        """Timid should have correct modifiers for all stats."""
        modifiers = get_nature_modifiers(Nature.TIMID)
        assert modifiers[Stat.HP] == 1.0
        assert modifiers[Stat.ATK] == 0.9
        assert modifiers[Stat.DEF] == 1.0
        assert modifiers[Stat.SPA] == 1.0
        assert modifiers[Stat.SPD] == 1.0
        assert modifiers[Stat.SPE] == 1.1


class TestNatureDataStructure:
    """Test NatureData dataclass properties."""

    def test_nature_data_has_name(self):
        """Each NatureData should have a name string."""
        for nature, data in NATURE_DATA.items():
            assert isinstance(data.name, str)
            assert len(data.name) > 0

    def test_nature_data_has_boosted_stat(self):
        """Each NatureData should have a boosted stat."""
        for nature, data in NATURE_DATA.items():
            assert data.boosted is None or isinstance(data.boosted, Stat)

    def test_nature_data_has_hindered_stat(self):
        """Each NatureData should have a hindered stat."""
        for nature, data in NATURE_DATA.items():
            assert data.hindered is None or isinstance(data.hindered, Stat)

    def test_nature_data_is_frozen(self):
        """NatureData should be immutable."""
        data = NATURE_DATA[Nature.ADAMANT]
        with pytest.raises(Exception):
            data.name = "Modified"


class TestNatureByNameLookup:
    """Test NATURE_BY_NAME dictionary for string lookups."""

    def test_all_natures_accessible_by_lowercase_name(self):
        """All natures should be accessible by lowercase name."""
        expected_names = [
            "hardy", "lonely", "brave", "adamant", "naughty",
            "bold", "docile", "relaxed", "impish", "lax",
            "timid", "hasty", "serious", "jolly", "naive",
            "modest", "mild", "quiet", "bashful", "rash",
            "calm", "gentle", "sassy", "careful", "quirky"
        ]
        for name in expected_names:
            assert name in NATURE_BY_NAME, f"Missing nature: {name}"

    def test_lookup_returns_correct_nature(self):
        """Looking up by name should return the correct Nature enum."""
        assert NATURE_BY_NAME["adamant"] == Nature.ADAMANT
        assert NATURE_BY_NAME["jolly"] == Nature.JOLLY
        assert NATURE_BY_NAME["modest"] == Nature.MODEST
        assert NATURE_BY_NAME["timid"] == Nature.TIMID


class TestCompetitiveNaturePairs:
    """Test common competitive nature pairs and their effects."""

    def test_physical_attacker_natures(self):
        """Common physical attacker natures."""
        # Adamant: +Atk, -SpA (for pure physical)
        assert get_nature_modifier(Nature.ADAMANT, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPA) == 0.9

        # Jolly: +Spe, -SpA (for fast physical)
        assert get_nature_modifier(Nature.JOLLY, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.JOLLY, Stat.SPA) == 0.9

    def test_special_attacker_natures(self):
        """Common special attacker natures."""
        # Modest: +SpA, -Atk (for pure special)
        assert get_nature_modifier(Nature.MODEST, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.MODEST, Stat.ATK) == 0.9

        # Timid: +Spe, -Atk (for fast special)
        assert get_nature_modifier(Nature.TIMID, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.TIMID, Stat.ATK) == 0.9

    def test_trick_room_natures(self):
        """Natures that lower Speed for Trick Room teams."""
        # Brave: +Atk, -Spe (physical in Trick Room)
        assert get_nature_modifier(Nature.BRAVE, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.BRAVE, Stat.SPE) == 0.9

        # Quiet: +SpA, -Spe (special in Trick Room)
        assert get_nature_modifier(Nature.QUIET, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.QUIET, Stat.SPE) == 0.9

        # Relaxed: +Def, -Spe (defensive in Trick Room)
        assert get_nature_modifier(Nature.RELAXED, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.RELAXED, Stat.SPE) == 0.9

        # Sassy: +SpD, -Spe (special defensive in Trick Room)
        assert get_nature_modifier(Nature.SASSY, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.SASSY, Stat.SPE) == 0.9

    def test_defensive_natures(self):
        """Common defensive natures."""
        # Bold: +Def, -Atk (physical wall)
        assert get_nature_modifier(Nature.BOLD, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.BOLD, Stat.ATK) == 0.9

        # Calm: +SpD, -Atk (special wall)
        assert get_nature_modifier(Nature.CALM, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.CALM, Stat.ATK) == 0.9

        # Impish: +Def, -SpA (physical wall that may use Knock Off)
        assert get_nature_modifier(Nature.IMPISH, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.IMPISH, Stat.SPA) == 0.9

        # Careful: +SpD, -SpA (special wall that uses physical moves)
        assert get_nature_modifier(Nature.CAREFUL, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.CAREFUL, Stat.SPA) == 0.9


class TestNatureStatCoverage:
    """Test that all non-HP stats can be boosted and hindered."""

    def test_all_stats_can_be_boosted(self):
        """Each non-HP stat should be boostable by at least one nature."""
        boostable_stats = {Stat.ATK, Stat.DEF, Stat.SPA, Stat.SPD, Stat.SPE}
        boosted_stats = set()
        for data in NATURE_DATA.values():
            if data.boosted and not data.is_neutral:
                boosted_stats.add(data.boosted)
        assert boostable_stats == boosted_stats

    def test_all_stats_can_be_hindered(self):
        """Each non-HP stat should be hinderable by at least one nature."""
        hinderable_stats = {Stat.ATK, Stat.DEF, Stat.SPA, Stat.SPD, Stat.SPE}
        hindered_stats = set()
        for data in NATURE_DATA.values():
            if data.hindered and not data.is_neutral:
                hindered_stats.add(data.hindered)
        assert hinderable_stats == hindered_stats


class TestNatureMatrixCompleteness:
    """Test that all 20 non-neutral nature combinations exist."""

    def test_20_non_neutral_natures(self):
        """There should be exactly 20 non-neutral natures (5x4 combinations)."""
        non_neutral = [n for n in Nature if not NATURE_DATA[n].is_neutral]
        assert len(non_neutral) == 20

    def test_each_boost_has_4_hindered_options(self):
        """Each boosted stat should have 4 different hindered stat options."""
        for boost_stat in [Stat.ATK, Stat.DEF, Stat.SPA, Stat.SPD, Stat.SPE]:
            hindered_for_boost = []
            for nature, data in NATURE_DATA.items():
                if data.boosted == boost_stat and not data.is_neutral:
                    hindered_for_boost.append(data.hindered)
            # Should have 4 different hindered stats (all except the boosted one)
            assert len(hindered_for_boost) == 4
            assert boost_stat not in hindered_for_boost
