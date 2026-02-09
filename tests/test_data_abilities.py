"""Tests for data/abilities.py - Ability registry and data."""
import pytest

from data.abilities import (
    AbilityFlag,
    AbilityData,
    ABILITY_REGISTRY,
    ABILITY_BY_NAME,
    get_ability,
    get_ability_id,
    register_ability,
)


class TestAbilityFlag:
    """Tests for the AbilityFlag bitflags."""

    def test_none_flag_is_zero(self):
        """NONE flag should be 0."""
        assert AbilityFlag.NONE == 0

    def test_flags_are_powers_of_two(self):
        """Each flag (except NONE) should be a power of 2."""
        for flag in AbilityFlag:
            if flag != AbilityFlag.NONE:
                assert flag.value & (flag.value - 1) == 0

    def test_flags_are_unique(self):
        """Each flag should have a unique value."""
        values = [f.value for f in AbilityFlag]
        assert len(values) == len(set(values))

    def test_breakable_flag_exists(self):
        """BREAKABLE flag should exist for Mold Breaker interaction."""
        assert AbilityFlag.BREAKABLE.value > 0


class TestAbilityData:
    """Tests for the AbilityData dataclass."""

    def test_create_ability(self):
        """Should create an ability with all fields."""
        ability = AbilityData(
            id=100,
            name="Test Ability",
            description="A test ability.",
            rating=3.0,
            flags=AbilityFlag.BREAKABLE,
        )
        assert ability.id == 100
        assert ability.name == "Test Ability"
        assert ability.description == "A test ability."
        assert ability.rating == 3.0
        assert ability.flags == AbilityFlag.BREAKABLE

    def test_ability_defaults(self):
        """Should have sensible defaults."""
        ability = AbilityData(
            id=101,
            name="Default Test",
            description="Test defaults.",
        )
        assert ability.rating == 3.0
        assert ability.flags == AbilityFlag.BREAKABLE

    def test_ability_is_frozen(self):
        """AbilityData should be immutable."""
        ability = AbilityData(
            id=102,
            name="Frozen Test",
            description="Test immutability.",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            ability.name = "Changed"


class TestAbilityRegistry:
    """Tests for the ABILITY_REGISTRY."""

    def test_registry_not_empty(self):
        """Registry should have registered abilities."""
        assert len(ABILITY_REGISTRY) > 0

    def test_registry_has_common_abilities(self):
        """Registry should include common competitive abilities."""
        ability_names = [a.name.lower() for a in ABILITY_REGISTRY.values()]
        assert "intimidate" in ability_names
        assert "levitate" in ability_names

    def test_no_ability_placeholder_exists(self):
        """ID 0 should be reserved for 'No Ability'."""
        assert 0 in ABILITY_REGISTRY
        assert ABILITY_REGISTRY[0].name == "No Ability"

    def test_all_ids_unique(self):
        """All ability IDs should be unique."""
        ids = list(ABILITY_REGISTRY.keys())
        assert len(ids) == len(set(ids))


class TestGetAbility:
    """Tests for get_ability function."""

    def test_get_existing_ability(self):
        """Should return ability data for valid ID."""
        ability = get_ability(1)  # Intimidate
        assert ability is not None
        assert ability.name == "Intimidate"

    def test_get_nonexistent_ability(self):
        """Should return None for invalid ID."""
        ability = get_ability(99999)
        assert ability is None

    def test_get_no_ability(self):
        """Should return No Ability for ID 0."""
        ability = get_ability(0)
        assert ability is not None
        assert ability.name == "No Ability"


class TestGetAbilityId:
    """Tests for get_ability_id function."""

    def test_get_id_by_name(self):
        """Should return ID for valid ability name."""
        ability_id = get_ability_id("Intimidate")
        assert ability_id is not None
        assert ability_id == 1

    def test_get_id_case_insensitive(self):
        """Should be case-insensitive."""
        assert get_ability_id("intimidate") == get_ability_id("INTIMIDATE")
        assert get_ability_id("Levitate") == get_ability_id("levitate")

    def test_get_id_ignores_spaces(self):
        """Should ignore spaces in name."""
        # "Huge Power" should work with or without space
        id_with_space = get_ability_id("Huge Power")
        id_without_space = get_ability_id("HugePower")
        assert id_with_space == id_without_space

    def test_get_id_nonexistent(self):
        """Should return None for invalid ability name."""
        assert get_ability_id("NotARealAbility") is None


class TestAbilityByName:
    """Tests for ABILITY_BY_NAME mapping."""

    def test_mapping_not_empty(self):
        """Mapping should have entries."""
        assert len(ABILITY_BY_NAME) > 0

    def test_mapping_matches_registry(self):
        """Mapping should point to valid registry entries."""
        for name, ability_id in ABILITY_BY_NAME.items():
            assert ability_id in ABILITY_REGISTRY
            # Name should match (after normalization)
            registered_name = ABILITY_REGISTRY[ability_id].name.lower().replace(" ", "")
            assert name == registered_name


class TestRegisterAbility:
    """Tests for register_ability function."""

    def test_register_new_ability(self):
        """Should register a new ability."""
        new_ability = AbilityData(
            id=999,
            name="Custom Test Ability",
            description="For testing registration.",
            rating=1.0,
        )
        register_ability(new_ability)

        # Should be in registry
        assert 999 in ABILITY_REGISTRY
        assert ABILITY_REGISTRY[999].name == "Custom Test Ability"

        # Should be accessible by name
        assert get_ability_id("Custom Test Ability") == 999
        assert get_ability_id("customtestability") == 999

    def test_register_updates_existing(self):
        """Registering with existing ID should update entry."""
        updated = AbilityData(
            id=999,
            name="Updated Ability",
            description="Updated description.",
            rating=5.0,
        )
        register_ability(updated)
        assert ABILITY_REGISTRY[999].name == "Updated Ability"


class TestCommonAbilities:
    """Tests for specific common abilities."""

    def test_intimidate_properties(self):
        """Intimidate should have correct properties."""
        intimidate = get_ability(get_ability_id("Intimidate"))
        assert intimidate.name == "Intimidate"
        assert intimidate.flags & AbilityFlag.BREAKABLE
        assert intimidate.rating > 0

    def test_levitate_properties(self):
        """Levitate should be breakable."""
        levitate = get_ability(get_ability_id("Levitate"))
        assert levitate is not None
        assert levitate.flags & AbilityFlag.BREAKABLE

    def test_huge_power_not_breakable(self):
        """Huge Power should not be breakable by Mold Breaker."""
        huge_power = get_ability(get_ability_id("Huge Power"))
        assert huge_power is not None
        # Huge Power affects own stats, not breakable
        assert not (huge_power.flags & AbilityFlag.BREAKABLE)
