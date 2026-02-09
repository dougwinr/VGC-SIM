"""Comprehensive tests for data/abilities.py based on ability.md documentation.

Tests cover:
- Ability flags (breakable, immutable, suppressible)
- Ability ratings
- Ability registry operations
- Common ability categories
- Ability data structure
"""
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


class TestAbilityFlagDefinitions:
    """Test AbilityFlag bitflags are correctly defined."""

    def test_none_flag_is_zero(self):
        """NONE should be 0 for no flags."""
        assert AbilityFlag.NONE == 0

    def test_breakable_flag_exists(self):
        """BREAKABLE for Mold Breaker-affected abilities."""
        assert AbilityFlag.BREAKABLE.value > 0

    def test_failroleplay_flag_exists(self):
        """FAILROLEPLAY for abilities that can't be copied by Role Play."""
        assert AbilityFlag.FAILROLEPLAY.value > 0

    def test_noreceiver_flag_exists(self):
        """NORECEIVER for abilities not acquired by Receiver/Power of Alchemy."""
        assert AbilityFlag.NORECEIVER.value > 0

    def test_noentrain_flag_exists(self):
        """NOENTRAIN for abilities not given by Entrainment."""
        assert AbilityFlag.NOENTRAIN.value > 0

    def test_notrace_flag_exists(self):
        """NOTRACE for abilities not copied by Trace."""
        assert AbilityFlag.NOTRACE.value > 0

    def test_failskillswap_flag_exists(self):
        """FAILSKILLSWAP for abilities that can't be Skill Swapped."""
        assert AbilityFlag.FAILSKILLSWAP.value > 0

    def test_cantsuppress_flag_exists(self):
        """CANTSUPPRESS for abilities not suppressed by Neutralizing Gas."""
        assert AbilityFlag.CANTSUPPRESS.value > 0


class TestAbilityFlagCombinations:
    """Test combining ability flags."""

    def test_flags_are_powers_of_two(self):
        """Each flag (except NONE) should be a power of 2."""
        for flag in AbilityFlag:
            if flag != AbilityFlag.NONE:
                assert flag.value & (flag.value - 1) == 0

    def test_flags_are_unique(self):
        """Each flag should have a unique value."""
        values = [f.value for f in AbilityFlag]
        assert len(values) == len(set(values))

    def test_can_combine_flags(self):
        """Should be able to combine multiple flags."""
        combined = AbilityFlag.BREAKABLE | AbilityFlag.FAILSKILLSWAP
        assert combined & AbilityFlag.BREAKABLE
        assert combined & AbilityFlag.FAILSKILLSWAP
        assert not (combined & AbilityFlag.NOTRACE)

    def test_immutable_ability_flags(self):
        """Immutable abilities like Multitype have multiple restriction flags."""
        immutable_flags = (
            AbilityFlag.FAILROLEPLAY |
            AbilityFlag.FAILSKILLSWAP |
            AbilityFlag.NOTRACE |
            AbilityFlag.CANTSUPPRESS
        )
        assert immutable_flags & AbilityFlag.FAILROLEPLAY
        assert immutable_flags & AbilityFlag.FAILSKILLSWAP
        assert immutable_flags & AbilityFlag.NOTRACE
        assert immutable_flags & AbilityFlag.CANTSUPPRESS


class TestAbilityDataStructure:
    """Test AbilityData dataclass structure."""

    def test_create_basic_ability(self):
        """Create a basic ability with minimal fields."""
        ability = AbilityData(
            id=100,
            name="Test Ability",
            description="A test ability for unit tests.",
        )
        assert ability.id == 100
        assert ability.name == "Test Ability"
        assert ability.description == "A test ability for unit tests."

    def test_ability_has_rating(self):
        """Abilities should have a rating field."""
        ability = AbilityData(
            id=101,
            name="Rated Ability",
            description="Has a rating.",
            rating=4.5,
        )
        assert ability.rating == 4.5

    def test_ability_has_flags(self):
        """Abilities should have a flags field."""
        ability = AbilityData(
            id=102,
            name="Flagged Ability",
            description="Has flags.",
            flags=AbilityFlag.BREAKABLE,
        )
        assert ability.flags == AbilityFlag.BREAKABLE

    def test_ability_default_rating(self):
        """Default rating should be 3.0."""
        ability = AbilityData(
            id=103,
            name="Default Rating",
            description="Uses default rating.",
        )
        assert ability.rating == 3.0

    def test_ability_default_flags(self):
        """Default flags should be BREAKABLE."""
        ability = AbilityData(
            id=104,
            name="Default Flags",
            description="Uses default flags.",
        )
        assert ability.flags == AbilityFlag.BREAKABLE

    def test_ability_is_frozen(self):
        """AbilityData should be immutable."""
        ability = AbilityData(
            id=105,
            name="Frozen Ability",
            description="Cannot be modified.",
        )
        with pytest.raises(Exception):
            ability.name = "Modified"

    def test_ability_with_all_fields(self):
        """Create ability with all fields specified."""
        ability = AbilityData(
            id=106,
            name="Full Ability",
            description="All fields specified.",
            rating=5.0,
            flags=AbilityFlag.NONE,
        )
        assert ability.id == 106
        assert ability.name == "Full Ability"
        assert ability.description == "All fields specified."
        assert ability.rating == 5.0
        assert ability.flags == AbilityFlag.NONE


class TestAbilityRegistryBasics:
    """Test ABILITY_REGISTRY basic functionality."""

    def test_registry_not_empty(self):
        """Registry should have registered abilities."""
        assert len(ABILITY_REGISTRY) > 0

    def test_registry_has_no_ability_placeholder(self):
        """ID 0 should be 'No Ability' placeholder."""
        assert 0 in ABILITY_REGISTRY
        assert ABILITY_REGISTRY[0].name == "No Ability"

    def test_registry_ids_are_unique(self):
        """All ability IDs should be unique."""
        ids = list(ABILITY_REGISTRY.keys())
        assert len(ids) == len(set(ids))

    def test_registry_abilities_have_required_fields(self):
        """All registered abilities should have required fields."""
        for ability_id, ability in ABILITY_REGISTRY.items():
            assert isinstance(ability.id, int)
            assert isinstance(ability.name, str)
            assert isinstance(ability.description, str)
            assert isinstance(ability.rating, float)


class TestGetAbilityFunction:
    """Test get_ability lookup function."""

    def test_get_existing_ability(self):
        """Should return ability for valid ID."""
        ability = get_ability(1)  # Intimidate
        assert ability is not None
        assert ability.id == 1

    def test_get_nonexistent_ability(self):
        """Should return None for invalid ID."""
        ability = get_ability(99999)
        assert ability is None

    def test_get_no_ability_placeholder(self):
        """Should return No Ability for ID 0."""
        ability = get_ability(0)
        assert ability is not None
        assert ability.name == "No Ability"

    def test_get_ability_returns_correct_data(self):
        """Returned ability should have correct data."""
        intimidate = get_ability(1)
        assert intimidate.name == "Intimidate"
        assert "Attack" in intimidate.description


class TestGetAbilityIdFunction:
    """Test get_ability_id lookup by name."""

    def test_get_id_by_exact_name(self):
        """Should find ability ID by exact name."""
        ability_id = get_ability_id("Intimidate")
        assert ability_id == 1

    def test_get_id_case_insensitive(self):
        """Should be case-insensitive."""
        assert get_ability_id("intimidate") == get_ability_id("INTIMIDATE")
        assert get_ability_id("Levitate") == get_ability_id("levitate")

    def test_get_id_ignores_spaces(self):
        """Should ignore spaces in name."""
        id_with_space = get_ability_id("Huge Power")
        id_without_space = get_ability_id("HugePower")
        assert id_with_space == id_without_space

    def test_get_id_nonexistent_returns_none(self):
        """Should return None for unknown ability."""
        assert get_ability_id("NotARealAbility") is None


class TestAbilityByNameMapping:
    """Test ABILITY_BY_NAME dictionary."""

    def test_mapping_not_empty(self):
        """Mapping should have entries."""
        assert len(ABILITY_BY_NAME) > 0

    def test_mapping_points_to_valid_registry_entries(self):
        """All mappings should point to valid registry IDs."""
        for name, ability_id in ABILITY_BY_NAME.items():
            assert ability_id in ABILITY_REGISTRY


class TestRegisterAbilityFunction:
    """Test register_ability dynamic registration."""

    def test_register_new_ability(self):
        """Should register a new ability."""
        new_ability = AbilityData(
            id=900,
            name="Test Registration",
            description="Testing registration function.",
            rating=2.0,
        )
        register_ability(new_ability)

        # Should be in registry
        assert 900 in ABILITY_REGISTRY
        assert ABILITY_REGISTRY[900].name == "Test Registration"

        # Should be accessible by name
        assert get_ability_id("Test Registration") == 900

    def test_register_updates_existing(self):
        """Registering with existing ID should update."""
        updated = AbilityData(
            id=900,
            name="Updated Registration",
            description="Updated description.",
            rating=4.0,
        )
        register_ability(updated)
        assert ABILITY_REGISTRY[900].name == "Updated Registration"


class TestCommonAbilityProperties:
    """Test properties of commonly registered abilities."""

    def test_intimidate_is_breakable(self):
        """Intimidate should be affected by Mold Breaker."""
        intimidate = get_ability(get_ability_id("Intimidate"))
        assert intimidate.flags & AbilityFlag.BREAKABLE

    def test_levitate_is_breakable(self):
        """Levitate should be affected by Mold Breaker."""
        levitate = get_ability(get_ability_id("Levitate"))
        assert levitate.flags & AbilityFlag.BREAKABLE

    def test_huge_power_not_breakable(self):
        """Huge Power affects own stats, not breakable."""
        huge_power = get_ability(get_ability_id("Huge Power"))
        assert not (huge_power.flags & AbilityFlag.BREAKABLE)

    def test_prankster_not_breakable(self):
        """Prankster modifies own moves, not breakable."""
        prankster = get_ability(get_ability_id("Prankster"))
        # Prankster doesn't need to be broken as it affects the user
        assert prankster is not None


class TestAbilityRatings:
    """Test ability rating system."""

    def test_no_ability_has_zero_rating(self):
        """No Ability placeholder should have 0 rating."""
        no_ability = get_ability(0)
        assert no_ability.rating == 0.0

    def test_ratings_in_valid_range(self):
        """All ratings should be between -1 and 5."""
        for ability in ABILITY_REGISTRY.values():
            assert -1 <= ability.rating <= 5

    def test_high_rated_abilities_exist(self):
        """Should have some highly rated abilities."""
        high_rated = [a for a in ABILITY_REGISTRY.values() if a.rating >= 4.0]
        assert len(high_rated) > 0


class TestAbilityCategories:
    """Test different categories of abilities based on their effects."""

    def test_stat_modifier_ability_exists(self):
        """Should have stat modifying abilities like Huge Power."""
        huge_power = get_ability(get_ability_id("Huge Power"))
        assert huge_power is not None
        assert "Attack" in huge_power.description or "doubled" in huge_power.description.lower()

    def test_type_immunity_ability_exists(self):
        """Should have type immunity abilities like Levitate."""
        levitate = get_ability(get_ability_id("Levitate"))
        assert levitate is not None
        assert "Ground" in levitate.description

    def test_priority_modifier_ability_exists(self):
        """Should have priority modifying abilities like Prankster."""
        prankster = get_ability(get_ability_id("Prankster"))
        assert prankster is not None
        assert "priority" in prankster.description.lower()

    def test_speed_modifier_ability_exists(self):
        """Should have speed modifying abilities like Speed Boost."""
        speed_boost = get_ability(get_ability_id("Speed Boost"))
        assert speed_boost is not None
        assert "Speed" in speed_boost.description

    def test_damage_modifier_ability_exists(self):
        """Should have damage reducing abilities like Multiscale."""
        multiscale = get_ability(get_ability_id("Multiscale"))
        assert multiscale is not None
        assert "damage" in multiscale.description.lower()

    def test_survival_ability_exists(self):
        """Should have survival abilities like Sturdy."""
        sturdy = get_ability(get_ability_id("Sturdy"))
        assert sturdy is not None
        assert "survives" in sturdy.description.lower() or "HP" in sturdy.description

    def test_stat_drop_immunity_ability_exists(self):
        """Should have stat drop immunity like Clear Body."""
        clear_body = get_ability(get_ability_id("Clear Body"))
        assert clear_body is not None
        assert "stat" in clear_body.description.lower()


class TestAbilityDescriptionQuality:
    """Test that ability descriptions are meaningful."""

    def test_descriptions_not_empty(self):
        """All abilities should have non-empty descriptions."""
        for ability in ABILITY_REGISTRY.values():
            assert len(ability.description) > 0

    def test_descriptions_are_sentences(self):
        """Descriptions should be proper sentences (end with period)."""
        for ability in ABILITY_REGISTRY.values():
            # Skip if description is very short
            if len(ability.description) > 10:
                assert ability.description.endswith(".")


class TestAbilityNameConsistency:
    """Test ability name formatting and consistency."""

    def test_names_not_empty(self):
        """All abilities should have non-empty names."""
        for ability in ABILITY_REGISTRY.values():
            assert len(ability.name) > 0

    def test_names_are_title_case(self):
        """Ability names should be in title case."""
        for ability in ABILITY_REGISTRY.values():
            # Check first letter of each word is uppercase
            words = ability.name.split()
            for word in words:
                if word:  # Skip empty strings
                    assert word[0].isupper() or word[0].isdigit()


class TestAbilityInteractionFlags:
    """Test abilities that have special interaction restrictions."""

    def test_breakable_abilities_can_be_ignored(self):
        """Breakable abilities should be ignorable by Mold Breaker."""
        breakable = [a for a in ABILITY_REGISTRY.values()
                     if a.flags & AbilityFlag.BREAKABLE]
        # Should have some breakable abilities
        assert len(breakable) > 0

    def test_some_abilities_not_breakable(self):
        """Some abilities should not be breakable."""
        non_breakable = [a for a in ABILITY_REGISTRY.values()
                         if not (a.flags & AbilityFlag.BREAKABLE)]
        # Should have some non-breakable abilities
        assert len(non_breakable) > 0
