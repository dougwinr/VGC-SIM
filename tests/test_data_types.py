"""Tests for data/types.py - Type chart and effectiveness calculations."""
import pytest

from data.types import (
    Type,
    TYPE_CHART,
    TYPE_BY_NAME,
    EFFECTIVENESS_MULTIPLIER,
    get_type_effectiveness,
    get_dual_type_effectiveness,
)


class TestTypeEnum:
    """Tests for the Type enum."""

    def test_type_count(self):
        """Should have exactly 19 types (including Stellar)."""
        assert len(Type) == 19

    def test_type_values_are_sequential(self):
        """Type IDs should be sequential integers starting from 0."""
        type_values = sorted([t.value for t in Type])
        expected = list(range(19))
        assert type_values == expected

    def test_common_types_exist(self):
        """Common types should be defined."""
        assert Type.FIRE.value >= 0
        assert Type.WATER.value >= 0
        assert Type.GRASS.value >= 0
        assert Type.ELECTRIC.value >= 0
        assert Type.DRAGON.value >= 0
        assert Type.FAIRY.value >= 0


class TestTypeChart:
    """Tests for the TYPE_CHART data structure."""

    def test_all_types_have_entries(self):
        """Every type should have a defense chart entry."""
        for t in Type:
            assert t in TYPE_CHART, f"Missing TYPE_CHART entry for {t.name}"

    def test_all_matchups_defined(self):
        """Each type should have all attacking type matchups defined."""
        for defending_type in Type:
            for attacking_type in Type:
                assert attacking_type in TYPE_CHART[defending_type], \
                    f"Missing matchup: {attacking_type.name} vs {defending_type.name}"

    def test_effectiveness_values_valid(self):
        """All effectiveness values should be 0, 1, 2, or 3."""
        valid_values = {0, 1, 2, 3}
        for defending_type in Type:
            for attacking_type, effectiveness in TYPE_CHART[defending_type].items():
                assert effectiveness in valid_values, \
                    f"Invalid effectiveness {effectiveness} for {attacking_type.name} vs {defending_type.name}"


class TestTypeEffectiveness:
    """Tests for type effectiveness calculations."""

    def test_super_effective_matchups(self):
        """Super effective attacks should return 2.0x multiplier."""
        # Fire is super effective against Grass
        assert get_type_effectiveness(Type.FIRE, Type.GRASS) == 2.0
        # Water is super effective against Fire
        assert get_type_effectiveness(Type.WATER, Type.FIRE) == 2.0
        # Electric is super effective against Water
        assert get_type_effectiveness(Type.ELECTRIC, Type.WATER) == 2.0
        # Ground is super effective against Electric
        assert get_type_effectiveness(Type.GROUND, Type.ELECTRIC) == 2.0

    def test_not_very_effective_matchups(self):
        """Not very effective attacks should return 0.5x multiplier."""
        # Fire is not very effective against Water
        assert get_type_effectiveness(Type.FIRE, Type.WATER) == 0.5
        # Grass is not very effective against Fire
        assert get_type_effectiveness(Type.GRASS, Type.FIRE) == 0.5
        # Electric is not very effective against Grass
        assert get_type_effectiveness(Type.ELECTRIC, Type.GRASS) == 0.5

    def test_immune_matchups(self):
        """Immune matchups should return 0.0x multiplier."""
        # Normal doesn't affect Ghost
        assert get_type_effectiveness(Type.NORMAL, Type.GHOST) == 0.0
        # Ghost doesn't affect Normal
        assert get_type_effectiveness(Type.GHOST, Type.NORMAL) == 0.0
        # Ground doesn't affect Flying
        assert get_type_effectiveness(Type.GROUND, Type.FLYING) == 0.0
        # Electric doesn't affect Ground
        assert get_type_effectiveness(Type.ELECTRIC, Type.GROUND) == 0.0
        # Psychic doesn't affect Dark
        assert get_type_effectiveness(Type.PSYCHIC, Type.DARK) == 0.0
        # Dragon doesn't affect Fairy
        assert get_type_effectiveness(Type.DRAGON, Type.FAIRY) == 0.0
        # Poison doesn't affect Steel
        assert get_type_effectiveness(Type.POISON, Type.STEEL) == 0.0

    def test_neutral_matchups(self):
        """Neutral matchups should return 1.0x multiplier."""
        # Fire vs Electric is neutral
        assert get_type_effectiveness(Type.FIRE, Type.ELECTRIC) == 1.0
        # Normal vs Normal is neutral
        assert get_type_effectiveness(Type.NORMAL, Type.NORMAL) == 1.0


class TestDualTypeEffectiveness:
    """Tests for dual-type effectiveness calculations."""

    def test_double_super_effective(self):
        """4x effectiveness against dual types weak to same attack."""
        # Fighting vs Steel/Rock = 2x * 2x = 4x
        assert get_dual_type_effectiveness(Type.FIGHTING, Type.STEEL, Type.ROCK) == 4.0
        # Ground vs Fire/Electric = 2x * 2x = 4x
        assert get_dual_type_effectiveness(Type.GROUND, Type.FIRE, Type.ELECTRIC) == 4.0

    def test_double_resist(self):
        """0.25x effectiveness against dual types resisting same attack."""
        # Fire vs Water/Dragon = 0.5x * 0.5x = 0.25x
        assert get_dual_type_effectiveness(Type.FIRE, Type.WATER, Type.DRAGON) == 0.25

    def test_immunity_overrides_weakness(self):
        """Immunity should result in 0x regardless of other type."""
        # Ground vs Flying/Water = 0x (Flying immune)
        assert get_dual_type_effectiveness(Type.GROUND, Type.FLYING, Type.WATER) == 0.0
        # Normal vs Ghost/Psychic = 0x (Ghost immune)
        assert get_dual_type_effectiveness(Type.NORMAL, Type.GHOST, Type.PSYCHIC) == 0.0

    def test_single_type_handling(self):
        """None as second type should work like single-typed Pokemon."""
        assert get_dual_type_effectiveness(Type.FIRE, Type.GRASS, None) == 2.0
        assert get_dual_type_effectiveness(Type.WATER, Type.FIRE, None) == 2.0

    def test_same_type_twice(self):
        """Same type for both should work like single-typed."""
        assert get_dual_type_effectiveness(Type.FIRE, Type.GRASS, Type.GRASS) == 2.0


class TestTypeByName:
    """Tests for string-to-Type mapping."""

    def test_all_types_have_names(self):
        """Every type should have a name mapping."""
        assert len(TYPE_BY_NAME) == 19

    def test_lookup_by_lowercase_name(self):
        """Should look up types by lowercase name."""
        assert TYPE_BY_NAME["fire"] == Type.FIRE
        assert TYPE_BY_NAME["water"] == Type.WATER
        assert TYPE_BY_NAME["grass"] == Type.GRASS

    def test_stellar_type_exists(self):
        """Stellar type (Gen 9) should be accessible."""
        assert TYPE_BY_NAME["stellar"] == Type.STELLAR
