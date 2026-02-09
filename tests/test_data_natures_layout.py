"""Additional comprehensive tests for data/natures.py module.

Tests cover:
- All 25 natures and their stat effects
- Nature modifier function edge cases
- NATURE_BY_NAME lookup
- NatureData dataclass
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


class TestStatEnum:
    """Tests for the Stat enum."""

    def test_stat_count(self):
        """Should have exactly 6 stats."""
        assert len(Stat) == 6

    def test_stat_values_are_sequential(self):
        """Stat IDs should be sequential integers starting from 0."""
        stat_values = sorted([s.value for s in Stat])
        expected = list(range(6))
        assert stat_values == expected

    def test_stat_ordering(self):
        """Stats should be in standard order."""
        assert Stat.HP.value == 0
        assert Stat.ATK.value == 1
        assert Stat.DEF.value == 2
        assert Stat.SPA.value == 3
        assert Stat.SPD.value == 4
        assert Stat.SPE.value == 5


class TestNatureEnum:
    """Tests for the Nature enum."""

    def test_nature_count(self):
        """Should have exactly 25 natures."""
        assert len(Nature) == 25

    def test_nature_values_are_sequential(self):
        """Nature IDs should be sequential integers starting from 0."""
        nature_values = sorted([n.value for n in Nature])
        expected = list(range(25))
        assert nature_values == expected

    def test_neutral_natures_ids(self):
        """Neutral natures should have IDs 0-4."""
        neutral = [Nature.HARDY, Nature.DOCILE, Nature.SERIOUS,
                   Nature.BASHFUL, Nature.QUIRKY]
        for nature in neutral:
            assert nature.value in range(5)

    def test_attack_boosting_natures(self):
        """Attack boosting natures should be 5-8."""
        atk_boost = [Nature.LONELY, Nature.BRAVE, Nature.ADAMANT, Nature.NAUGHTY]
        for nature in atk_boost:
            assert nature.value in range(5, 9)

    def test_defense_boosting_natures(self):
        """Defense boosting natures should be 9-12."""
        def_boost = [Nature.BOLD, Nature.RELAXED, Nature.IMPISH, Nature.LAX]
        for nature in def_boost:
            assert nature.value in range(9, 13)

    def test_spa_boosting_natures(self):
        """Special Attack boosting natures should be 13-16."""
        spa_boost = [Nature.MODEST, Nature.MILD, Nature.QUIET, Nature.RASH]
        for nature in spa_boost:
            assert nature.value in range(13, 17)

    def test_spd_boosting_natures(self):
        """Special Defense boosting natures should be 17-20."""
        spd_boost = [Nature.CALM, Nature.GENTLE, Nature.SASSY, Nature.CAREFUL]
        for nature in spd_boost:
            assert nature.value in range(17, 21)

    def test_speed_boosting_natures(self):
        """Speed boosting natures should be 21-24."""
        spe_boost = [Nature.TIMID, Nature.HASTY, Nature.JOLLY, Nature.NAIVE]
        for nature in spe_boost:
            assert nature.value in range(21, 25)


class TestNatureData:
    """Tests for NatureData dataclass."""

    def test_all_natures_have_data(self):
        """Every Nature should have corresponding NatureData."""
        for nature in Nature:
            assert nature in NATURE_DATA, f"Missing NATURE_DATA for {nature.name}"

    def test_nature_data_fields(self):
        """NatureData should have name, boosted, and hindered fields."""
        adamant = NATURE_DATA[Nature.ADAMANT]
        assert hasattr(adamant, 'name')
        assert hasattr(adamant, 'boosted')
        assert hasattr(adamant, 'hindered')

    def test_neutral_nature_is_neutral(self):
        """Neutral natures should have is_neutral = True."""
        neutral = [Nature.HARDY, Nature.DOCILE, Nature.SERIOUS,
                   Nature.BASHFUL, Nature.QUIRKY]
        for nature in neutral:
            assert NATURE_DATA[nature].is_neutral

    def test_non_neutral_nature_is_not_neutral(self):
        """Non-neutral natures should have is_neutral = False."""
        non_neutral = [Nature.ADAMANT, Nature.JOLLY, Nature.MODEST,
                       Nature.BOLD, Nature.CALM]
        for nature in non_neutral:
            assert not NATURE_DATA[nature].is_neutral

    def test_adamant_nature_data(self):
        """Adamant nature should boost ATK and hinder SPA."""
        adamant = NATURE_DATA[Nature.ADAMANT]
        assert adamant.name == "Adamant"
        assert adamant.boosted == Stat.ATK
        assert adamant.hindered == Stat.SPA

    def test_jolly_nature_data(self):
        """Jolly nature should boost SPE and hinder SPA."""
        jolly = NATURE_DATA[Nature.JOLLY]
        assert jolly.name == "Jolly"
        assert jolly.boosted == Stat.SPE
        assert jolly.hindered == Stat.SPA

    def test_modest_nature_data(self):
        """Modest nature should boost SPA and hinder ATK."""
        modest = NATURE_DATA[Nature.MODEST]
        assert modest.name == "Modest"
        assert modest.boosted == Stat.SPA
        assert modest.hindered == Stat.ATK

    def test_bold_nature_data(self):
        """Bold nature should boost DEF and hinder ATK."""
        bold = NATURE_DATA[Nature.BOLD]
        assert bold.name == "Bold"
        assert bold.boosted == Stat.DEF
        assert bold.hindered == Stat.ATK

    def test_timid_nature_data(self):
        """Timid nature should boost SPE and hinder ATK."""
        timid = NATURE_DATA[Nature.TIMID]
        assert timid.name == "Timid"
        assert timid.boosted == Stat.SPE
        assert timid.hindered == Stat.ATK


class TestNatureByName:
    """Tests for NATURE_BY_NAME lookup dictionary."""

    def test_all_natures_in_lookup(self):
        """All nature names should be in NATURE_BY_NAME."""
        assert len(NATURE_BY_NAME) == 25

    def test_lowercase_lookup(self):
        """Lookups should be lowercase."""
        assert "adamant" in NATURE_BY_NAME
        assert "jolly" in NATURE_BY_NAME
        assert "modest" in NATURE_BY_NAME
        assert "hardy" in NATURE_BY_NAME

    def test_lookup_returns_correct_nature(self):
        """Lookups should return correct Nature enum values."""
        assert NATURE_BY_NAME["adamant"] == Nature.ADAMANT
        assert NATURE_BY_NAME["jolly"] == Nature.JOLLY
        assert NATURE_BY_NAME["modest"] == Nature.MODEST
        assert NATURE_BY_NAME["hardy"] == Nature.HARDY


class TestGetNatureModifier:
    """Tests for get_nature_modifier function."""

    def test_hp_never_modified(self):
        """HP should never be modified by any nature."""
        for nature in Nature:
            assert get_nature_modifier(nature, Stat.HP) == 1.0

    def test_neutral_nature_no_effect(self):
        """Neutral natures should give 1.0 for all stats."""
        neutral = [Nature.HARDY, Nature.DOCILE, Nature.SERIOUS,
                   Nature.BASHFUL, Nature.QUIRKY]
        for nature in neutral:
            for stat in Stat:
                assert get_nature_modifier(nature, stat) == 1.0

    def test_adamant_boosts_attack(self):
        """Adamant should give 1.1 for ATK."""
        assert get_nature_modifier(Nature.ADAMANT, Stat.ATK) == 1.1

    def test_adamant_hinders_spa(self):
        """Adamant should give 0.9 for SPA."""
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPA) == 0.9

    def test_adamant_neutral_for_others(self):
        """Adamant should give 1.0 for DEF, SPD, SPE."""
        assert get_nature_modifier(Nature.ADAMANT, Stat.DEF) == 1.0
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPD) == 1.0
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPE) == 1.0

    def test_all_boosting_natures_give_11(self):
        """All non-neutral natures should give 1.1 for boosted stat."""
        boosting = {
            Nature.LONELY: Stat.ATK, Nature.BRAVE: Stat.ATK,
            Nature.ADAMANT: Stat.ATK, Nature.NAUGHTY: Stat.ATK,
            Nature.BOLD: Stat.DEF, Nature.RELAXED: Stat.DEF,
            Nature.IMPISH: Stat.DEF, Nature.LAX: Stat.DEF,
            Nature.MODEST: Stat.SPA, Nature.MILD: Stat.SPA,
            Nature.QUIET: Stat.SPA, Nature.RASH: Stat.SPA,
            Nature.CALM: Stat.SPD, Nature.GENTLE: Stat.SPD,
            Nature.SASSY: Stat.SPD, Nature.CAREFUL: Stat.SPD,
            Nature.TIMID: Stat.SPE, Nature.HASTY: Stat.SPE,
            Nature.JOLLY: Stat.SPE, Nature.NAIVE: Stat.SPE,
        }
        for nature, boosted_stat in boosting.items():
            assert get_nature_modifier(nature, boosted_stat) == 1.1, \
                f"{nature.name} should boost {boosted_stat.name}"

    def test_all_hindering_natures_give_09(self):
        """All non-neutral natures should give 0.9 for hindered stat."""
        hindering = {
            Nature.LONELY: Stat.DEF, Nature.BOLD: Stat.ATK,
            Nature.MODEST: Stat.ATK, Nature.CALM: Stat.ATK,
            Nature.TIMID: Stat.ATK,
            Nature.HASTY: Stat.DEF, Nature.MILD: Stat.DEF,
            Nature.GENTLE: Stat.DEF,
            Nature.ADAMANT: Stat.SPA, Nature.IMPISH: Stat.SPA,
            Nature.CAREFUL: Stat.SPA, Nature.JOLLY: Stat.SPA,
            Nature.NAUGHTY: Stat.SPD, Nature.LAX: Stat.SPD,
            Nature.RASH: Stat.SPD, Nature.NAIVE: Stat.SPD,
            Nature.BRAVE: Stat.SPE, Nature.RELAXED: Stat.SPE,
            Nature.QUIET: Stat.SPE, Nature.SASSY: Stat.SPE,
        }
        for nature, hindered_stat in hindering.items():
            assert get_nature_modifier(nature, hindered_stat) == 0.9, \
                f"{nature.name} should hinder {hindered_stat.name}"


class TestGetNatureModifiers:
    """Tests for get_nature_modifiers function."""

    def test_returns_dict_with_all_stats(self):
        """Should return a dict with all 6 stats."""
        result = get_nature_modifiers(Nature.ADAMANT)
        assert len(result) == 6
        for stat in Stat:
            assert stat in result

    def test_adamant_modifiers(self):
        """Adamant should have correct modifiers for all stats."""
        result = get_nature_modifiers(Nature.ADAMANT)
        assert result[Stat.HP] == 1.0
        assert result[Stat.ATK] == 1.1
        assert result[Stat.DEF] == 1.0
        assert result[Stat.SPA] == 0.9
        assert result[Stat.SPD] == 1.0
        assert result[Stat.SPE] == 1.0

    def test_hardy_all_neutral(self):
        """Hardy (neutral) should have 1.0 for all stats."""
        result = get_nature_modifiers(Nature.HARDY)
        for stat in Stat:
            assert result[stat] == 1.0

    def test_timid_modifiers(self):
        """Timid should have correct modifiers for all stats."""
        result = get_nature_modifiers(Nature.TIMID)
        assert result[Stat.HP] == 1.0
        assert result[Stat.ATK] == 0.9
        assert result[Stat.DEF] == 1.0
        assert result[Stat.SPA] == 1.0
        assert result[Stat.SPD] == 1.0
        assert result[Stat.SPE] == 1.1


class TestNatureStatInteractions:
    """Tests for all 25 nature × stat interactions."""

    def test_lonely_nature(self):
        """Lonely: +ATK, -DEF."""
        assert get_nature_modifier(Nature.LONELY, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.LONELY, Stat.DEF) == 0.9

    def test_brave_nature(self):
        """Brave: +ATK, -SPE."""
        assert get_nature_modifier(Nature.BRAVE, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.BRAVE, Stat.SPE) == 0.9

    def test_naughty_nature(self):
        """Naughty: +ATK, -SPD."""
        assert get_nature_modifier(Nature.NAUGHTY, Stat.ATK) == 1.1
        assert get_nature_modifier(Nature.NAUGHTY, Stat.SPD) == 0.9

    def test_relaxed_nature(self):
        """Relaxed: +DEF, -SPE."""
        assert get_nature_modifier(Nature.RELAXED, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.RELAXED, Stat.SPE) == 0.9

    def test_impish_nature(self):
        """Impish: +DEF, -SPA."""
        assert get_nature_modifier(Nature.IMPISH, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.IMPISH, Stat.SPA) == 0.9

    def test_lax_nature(self):
        """Lax: +DEF, -SPD."""
        assert get_nature_modifier(Nature.LAX, Stat.DEF) == 1.1
        assert get_nature_modifier(Nature.LAX, Stat.SPD) == 0.9

    def test_mild_nature(self):
        """Mild: +SPA, -DEF."""
        assert get_nature_modifier(Nature.MILD, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.MILD, Stat.DEF) == 0.9

    def test_quiet_nature(self):
        """Quiet: +SPA, -SPE."""
        assert get_nature_modifier(Nature.QUIET, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.QUIET, Stat.SPE) == 0.9

    def test_rash_nature(self):
        """Rash: +SPA, -SPD."""
        assert get_nature_modifier(Nature.RASH, Stat.SPA) == 1.1
        assert get_nature_modifier(Nature.RASH, Stat.SPD) == 0.9

    def test_gentle_nature(self):
        """Gentle: +SPD, -DEF."""
        assert get_nature_modifier(Nature.GENTLE, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.GENTLE, Stat.DEF) == 0.9

    def test_sassy_nature(self):
        """Sassy: +SPD, -SPE."""
        assert get_nature_modifier(Nature.SASSY, Stat.SPD) == 1.1
        assert get_nature_modifier(Nature.SASSY, Stat.SPE) == 0.9

    def test_hasty_nature(self):
        """Hasty: +SPE, -DEF."""
        assert get_nature_modifier(Nature.HASTY, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.HASTY, Stat.DEF) == 0.9

    def test_naive_nature(self):
        """Naive: +SPE, -SPD."""
        assert get_nature_modifier(Nature.NAIVE, Stat.SPE) == 1.1
        assert get_nature_modifier(Nature.NAIVE, Stat.SPD) == 0.9
