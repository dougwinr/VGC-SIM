"""Tests for data/natures.py - Nature enum and stat modifiers."""
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

    def test_stat_values(self):
        """Stats should have expected values."""
        assert Stat.HP == 0
        assert Stat.ATK == 1
        assert Stat.DEF == 2
        assert Stat.SPA == 3
        assert Stat.SPD == 4
        assert Stat.SPE == 5


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

    def test_common_natures_exist(self):
        """Common competitive natures should be defined."""
        assert Nature.ADAMANT.value >= 0
        assert Nature.JOLLY.value >= 0
        assert Nature.MODEST.value >= 0
        assert Nature.TIMID.value >= 0
        assert Nature.BOLD.value >= 0
        assert Nature.CALM.value >= 0


class TestNatureData:
    """Tests for the NATURE_DATA registry."""

    def test_all_natures_have_data(self):
        """Every nature should have associated data."""
        for nature in Nature:
            assert nature in NATURE_DATA, f"Missing data for {nature.name}"

    def test_nature_data_has_required_fields(self):
        """Each NatureData should have name, boosted, and hindered stats."""
        for nature, data in NATURE_DATA.items():
            assert isinstance(data.name, str), f"{nature.name} missing name"
            assert isinstance(data.boosted, Stat), f"{nature.name} missing boosted"
            assert isinstance(data.hindered, Stat), f"{nature.name} missing hindered"

    def test_neutral_natures_identified(self):
        """Neutral natures should have same boosted and hindered stat."""
        neutral_natures = [Nature.HARDY, Nature.DOCILE, Nature.SERIOUS,
                          Nature.BASHFUL, Nature.QUIRKY]
        for nature in neutral_natures:
            data = NATURE_DATA[nature]
            assert data.is_neutral, f"{nature.name} should be neutral"
            assert data.boosted == data.hindered

    def test_exactly_five_neutral_natures(self):
        """Should have exactly 5 neutral natures."""
        neutral_count = sum(1 for data in NATURE_DATA.values() if data.is_neutral)
        assert neutral_count == 5


class TestNatureModifier:
    """Tests for get_nature_modifier function."""

    def test_hp_never_modified(self):
        """HP should never be modified by any nature."""
        for nature in Nature:
            assert get_nature_modifier(nature, Stat.HP) == 1.0, \
                f"{nature.name} should not modify HP"

    def test_boosted_stat_returns_1_1(self):
        """Boosted stat should return 1.1x modifier."""
        # Adamant boosts Attack
        assert get_nature_modifier(Nature.ADAMANT, Stat.ATK) == 1.1
        # Modest boosts Special Attack
        assert get_nature_modifier(Nature.MODEST, Stat.SPA) == 1.1
        # Jolly boosts Speed
        assert get_nature_modifier(Nature.JOLLY, Stat.SPE) == 1.1
        # Bold boosts Defense
        assert get_nature_modifier(Nature.BOLD, Stat.DEF) == 1.1

    def test_hindered_stat_returns_0_9(self):
        """Hindered stat should return 0.9x modifier."""
        # Adamant hinders Special Attack
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPA) == 0.9
        # Modest hinders Attack
        assert get_nature_modifier(Nature.MODEST, Stat.ATK) == 0.9
        # Jolly hinders Special Attack
        assert get_nature_modifier(Nature.JOLLY, Stat.SPA) == 0.9
        # Timid hinders Attack
        assert get_nature_modifier(Nature.TIMID, Stat.ATK) == 0.9

    def test_neutral_stats_return_1_0(self):
        """Unaffected stats should return 1.0x modifier."""
        # Adamant doesn't affect Defense, SpD, or Speed
        assert get_nature_modifier(Nature.ADAMANT, Stat.DEF) == 1.0
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPD) == 1.0
        assert get_nature_modifier(Nature.ADAMANT, Stat.SPE) == 1.0

    def test_neutral_nature_all_stats_1_0(self):
        """Neutral natures should return 1.0 for all stats."""
        for stat in Stat:
            assert get_nature_modifier(Nature.HARDY, stat) == 1.0
            assert get_nature_modifier(Nature.SERIOUS, stat) == 1.0


class TestNatureModifiers:
    """Tests for get_nature_modifiers function."""

    def test_returns_all_stats(self):
        """Should return modifier for every stat."""
        modifiers = get_nature_modifiers(Nature.ADAMANT)
        assert len(modifiers) == 6
        for stat in Stat:
            assert stat in modifiers

    def test_adamant_modifiers(self):
        """Adamant should boost Atk, hinder SpA."""
        modifiers = get_nature_modifiers(Nature.ADAMANT)
        assert modifiers[Stat.HP] == 1.0
        assert modifiers[Stat.ATK] == 1.1
        assert modifiers[Stat.DEF] == 1.0
        assert modifiers[Stat.SPA] == 0.9
        assert modifiers[Stat.SPD] == 1.0
        assert modifiers[Stat.SPE] == 1.0

    def test_neutral_nature_all_1_0(self):
        """Neutral nature should have all 1.0 modifiers."""
        modifiers = get_nature_modifiers(Nature.HARDY)
        for stat, modifier in modifiers.items():
            assert modifier == 1.0, f"Hardy should not modify {stat.name}"


class TestNatureByName:
    """Tests for string-to-Nature mapping."""

    def test_all_natures_have_names(self):
        """Every nature should be accessible by name."""
        assert len(NATURE_BY_NAME) == 25

    def test_lookup_by_lowercase_name(self):
        """Should look up natures by lowercase name."""
        assert NATURE_BY_NAME["adamant"] == Nature.ADAMANT
        assert NATURE_BY_NAME["jolly"] == Nature.JOLLY
        assert NATURE_BY_NAME["modest"] == Nature.MODEST
        assert NATURE_BY_NAME["timid"] == Nature.TIMID

    def test_all_competitive_natures_accessible(self):
        """Common competitive natures should be accessible."""
        competitive = ["adamant", "jolly", "modest", "timid", "bold",
                       "calm", "impish", "careful", "brave", "quiet"]
        for name in competitive:
            assert name in NATURE_BY_NAME, f"Missing nature: {name}"
