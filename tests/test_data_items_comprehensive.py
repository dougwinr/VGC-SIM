"""Comprehensive tests for data/items.py based on item.md documentation.

Tests cover:
- Item flags (consumable, berry, choice, mega stone, etc.)
- Item categories
- Fling power values
- Item removability
- Type boosting items
- Item registry operations
"""
import pytest

from data.items import (
    ItemFlag,
    ItemData,
    ITEM_REGISTRY,
    ITEM_BY_NAME,
    get_item,
    get_item_id,
    register_item,
    is_choice_item,
    is_berry,
)
from data.types import Type


class TestItemFlagDefinitions:
    """Test ItemFlag bitflags are correctly defined."""

    def test_none_flag_is_zero(self):
        """NONE should be 0 for no flags."""
        assert ItemFlag.NONE == 0

    def test_consumable_flag_exists(self):
        """CONSUMABLE for single-use items."""
        assert ItemFlag.CONSUMABLE.value > 0

    def test_berry_flag_exists(self):
        """BERRY for berry items."""
        assert ItemFlag.BERRY.value > 0

    def test_gem_flag_exists(self):
        """GEM for type gems."""
        assert ItemFlag.GEM.value > 0

    def test_plate_flag_exists(self):
        """PLATE for Arceus plates."""
        assert ItemFlag.PLATE.value > 0

    def test_drive_flag_exists(self):
        """DRIVE for Genesect drives."""
        assert ItemFlag.DRIVE.value > 0

    def test_memory_flag_exists(self):
        """MEMORY for Silvally memories."""
        assert ItemFlag.MEMORY.value > 0

    def test_mega_stone_flag_exists(self):
        """MEGA_STONE for Mega Stones."""
        assert ItemFlag.MEGA_STONE.value > 0

    def test_z_crystal_flag_exists(self):
        """Z_CRYSTAL for Z-Crystals."""
        assert ItemFlag.Z_CRYSTAL.value > 0

    def test_choice_flag_exists(self):
        """CHOICE for Choice items."""
        assert ItemFlag.CHOICE.value > 0


class TestItemFlagCombinations:
    """Test combining item flags."""

    def test_flags_are_powers_of_two(self):
        """Each flag (except NONE) should be a power of 2."""
        for flag in ItemFlag:
            if flag != ItemFlag.NONE:
                assert flag.value & (flag.value - 1) == 0

    def test_flags_are_unique(self):
        """Each flag should have a unique value."""
        values = [f.value for f in ItemFlag]
        assert len(values) == len(set(values))

    def test_berry_is_consumable(self):
        """Berries should typically be consumable."""
        berry_flags = ItemFlag.CONSUMABLE | ItemFlag.BERRY
        assert berry_flags & ItemFlag.CONSUMABLE
        assert berry_flags & ItemFlag.BERRY

    def test_can_combine_multiple_flags(self):
        """Should be able to combine multiple flags."""
        combined = ItemFlag.CONSUMABLE | ItemFlag.BERRY | ItemFlag.GEM
        assert combined & ItemFlag.CONSUMABLE
        assert combined & ItemFlag.BERRY
        assert combined & ItemFlag.GEM


class TestItemDataStructure:
    """Test ItemData dataclass structure."""

    def test_create_basic_item(self):
        """Create a basic item with minimal fields."""
        item = ItemData(
            id=100,
            name="Test Item",
            description="A test item for unit tests.",
        )
        assert item.id == 100
        assert item.name == "Test Item"
        assert item.description == "A test item for unit tests."

    def test_item_has_fling_power(self):
        """Items should have a fling_power field."""
        item = ItemData(
            id=101,
            name="Heavy Item",
            description="Can be flung.",
            fling_power=80,
        )
        assert item.fling_power == 80

    def test_item_has_flags(self):
        """Items should have a flags field."""
        item = ItemData(
            id=102,
            name="Flagged Item",
            description="Has flags.",
            flags=ItemFlag.CONSUMABLE,
        )
        assert item.flags == ItemFlag.CONSUMABLE

    def test_item_has_type_boost(self):
        """Items can have type boost properties."""
        item = ItemData(
            id=103,
            name="Fire Booster",
            description="Boosts Fire moves.",
            type_boost=Type.FIRE,
            boost_amount=1.2,
        )
        assert item.type_boost == Type.FIRE
        assert item.boost_amount == 1.2

    def test_item_default_fling_power(self):
        """Default fling_power should be 0."""
        item = ItemData(
            id=104,
            name="Default Fling",
            description="Default fling power.",
        )
        assert item.fling_power == 0

    def test_item_default_flags(self):
        """Default flags should be NONE."""
        item = ItemData(
            id=105,
            name="Default Flags",
            description="Default flags.",
        )
        assert item.flags == ItemFlag.NONE

    def test_item_default_type_boost(self):
        """Default type_boost should be None."""
        item = ItemData(
            id=106,
            name="No Type Boost",
            description="No type boost.",
        )
        assert item.type_boost is None
        assert item.boost_amount == 1.0

    def test_item_is_frozen(self):
        """ItemData should be immutable."""
        item = ItemData(
            id=107,
            name="Frozen Item",
            description="Cannot be modified.",
        )
        with pytest.raises(Exception):
            item.name = "Modified"


class TestItemRegistryBasics:
    """Test ITEM_REGISTRY basic functionality."""

    def test_registry_not_empty(self):
        """Registry should have registered items."""
        assert len(ITEM_REGISTRY) > 0

    def test_registry_has_no_item_placeholder(self):
        """ID 0 should be 'No Item' placeholder."""
        assert 0 in ITEM_REGISTRY
        assert ITEM_REGISTRY[0].name == "No Item"

    def test_registry_ids_are_unique(self):
        """All item IDs should be unique."""
        ids = list(ITEM_REGISTRY.keys())
        assert len(ids) == len(set(ids))

    def test_registry_items_have_required_fields(self):
        """All registered items should have required fields."""
        for item_id, item in ITEM_REGISTRY.items():
            assert isinstance(item.id, int)
            assert isinstance(item.name, str)
            assert isinstance(item.description, str)
            assert isinstance(item.fling_power, int)


class TestGetItemFunction:
    """Test get_item lookup function."""

    def test_get_existing_item(self):
        """Should return item for valid ID."""
        item = get_item(1)  # Choice Band
        assert item is not None
        assert item.id == 1

    def test_get_nonexistent_item(self):
        """Should return None for invalid ID."""
        item = get_item(99999)
        assert item is None

    def test_get_no_item_placeholder(self):
        """Should return No Item for ID 0."""
        item = get_item(0)
        assert item is not None
        assert item.name == "No Item"


class TestGetItemIdFunction:
    """Test get_item_id lookup by name."""

    def test_get_id_by_exact_name(self):
        """Should find item ID by exact name."""
        item_id = get_item_id("Choice Band")
        assert item_id == 1

    def test_get_id_case_insensitive(self):
        """Should be case-insensitive."""
        assert get_item_id("choice band") == get_item_id("CHOICE BAND")
        assert get_item_id("Leftovers") == get_item_id("leftovers")

    def test_get_id_ignores_spaces(self):
        """Should ignore spaces in name."""
        id_with_space = get_item_id("Choice Band")
        id_without_space = get_item_id("ChoiceBand")
        assert id_with_space == id_without_space

    def test_get_id_nonexistent_returns_none(self):
        """Should return None for unknown item."""
        assert get_item_id("NotARealItem") is None


class TestIsChoiceItemFunction:
    """Test is_choice_item helper function."""

    def test_choice_band_is_choice(self):
        """Choice Band should be identified as choice item."""
        assert is_choice_item(get_item_id("Choice Band"))

    def test_choice_specs_is_choice(self):
        """Choice Specs should be identified as choice item."""
        assert is_choice_item(get_item_id("Choice Specs"))

    def test_choice_scarf_is_choice(self):
        """Choice Scarf should be identified as choice item."""
        assert is_choice_item(get_item_id("Choice Scarf"))

    def test_leftovers_not_choice(self):
        """Leftovers should not be a choice item."""
        assert not is_choice_item(get_item_id("Leftovers"))

    def test_life_orb_not_choice(self):
        """Life Orb should not be a choice item."""
        assert not is_choice_item(get_item_id("Life Orb"))

    def test_invalid_id_returns_false(self):
        """Invalid ID should return False."""
        assert not is_choice_item(99999)


class TestIsBerryFunction:
    """Test is_berry helper function."""

    def test_sitrus_berry_is_berry(self):
        """Sitrus Berry should be identified as berry."""
        assert is_berry(get_item_id("Sitrus Berry"))

    def test_leftovers_not_berry(self):
        """Leftovers should not be a berry."""
        assert not is_berry(get_item_id("Leftovers"))

    def test_choice_band_not_berry(self):
        """Choice Band should not be a berry."""
        assert not is_berry(get_item_id("Choice Band"))

    def test_invalid_id_returns_false(self):
        """Invalid ID should return False."""
        assert not is_berry(99999)


class TestItemByNameMapping:
    """Test ITEM_BY_NAME dictionary."""

    def test_mapping_not_empty(self):
        """Mapping should have entries."""
        assert len(ITEM_BY_NAME) > 0

    def test_mapping_points_to_valid_registry_entries(self):
        """All mappings should point to valid registry IDs."""
        for name, item_id in ITEM_BY_NAME.items():
            assert item_id in ITEM_REGISTRY


class TestRegisterItemFunction:
    """Test register_item dynamic registration."""

    def test_register_new_item(self):
        """Should register a new item."""
        new_item = ItemData(
            id=800,
            name="Test Registration Item",
            description="Testing registration function.",
            fling_power=30,
        )
        register_item(new_item)

        # Should be in registry
        assert 800 in ITEM_REGISTRY
        assert ITEM_REGISTRY[800].name == "Test Registration Item"

        # Should be accessible by name
        assert get_item_id("Test Registration Item") == 800

    def test_register_updates_existing(self):
        """Registering with existing ID should update."""
        updated = ItemData(
            id=800,
            name="Updated Registration Item",
            description="Updated description.",
            fling_power=50,
        )
        register_item(updated)
        assert ITEM_REGISTRY[800].name == "Updated Registration Item"


class TestChoiceItemProperties:
    """Test properties of Choice items."""

    def test_all_choice_items_have_choice_flag(self):
        """All Choice items should have CHOICE flag."""
        choice_names = ["Choice Band", "Choice Specs", "Choice Scarf"]
        for name in choice_names:
            item = get_item(get_item_id(name))
            assert item.flags & ItemFlag.CHOICE

    def test_choice_band_description_mentions_attack(self):
        """Choice Band should mention Attack boost."""
        choice_band = get_item(get_item_id("Choice Band"))
        assert "Attack" in choice_band.description or "Atk" in choice_band.description

    def test_choice_specs_description_mentions_spatk(self):
        """Choice Specs should mention Sp. Atk boost."""
        choice_specs = get_item(get_item_id("Choice Specs"))
        desc = choice_specs.description.lower()
        assert "sp" in desc or "special" in desc

    def test_choice_scarf_description_mentions_speed(self):
        """Choice Scarf should mention Speed boost."""
        choice_scarf = get_item(get_item_id("Choice Scarf"))
        assert "Speed" in choice_scarf.description


class TestConsumableItemProperties:
    """Test properties of consumable items."""

    def test_focus_sash_is_consumable(self):
        """Focus Sash should be consumable."""
        sash = get_item(get_item_id("Focus Sash"))
        assert sash.flags & ItemFlag.CONSUMABLE

    def test_sitrus_berry_is_consumable(self):
        """Sitrus Berry should be consumable."""
        sitrus = get_item(get_item_id("Sitrus Berry"))
        assert sitrus.flags & ItemFlag.CONSUMABLE

    def test_leftovers_not_consumable(self):
        """Leftovers should not be consumable."""
        leftovers = get_item(get_item_id("Leftovers"))
        assert not (leftovers.flags & ItemFlag.CONSUMABLE)

    def test_life_orb_not_consumable(self):
        """Life Orb should not be consumable."""
        life_orb = get_item(get_item_id("Life Orb"))
        assert not (life_orb.flags & ItemFlag.CONSUMABLE)


class TestBerryProperties:
    """Test properties of berry items."""

    def test_sitrus_berry_has_berry_flag(self):
        """Sitrus Berry should have BERRY flag."""
        sitrus = get_item(get_item_id("Sitrus Berry"))
        assert sitrus.flags & ItemFlag.BERRY

    def test_sitrus_berry_is_consumable_and_berry(self):
        """Sitrus Berry should be both consumable and a berry."""
        sitrus = get_item(get_item_id("Sitrus Berry"))
        assert sitrus.flags & ItemFlag.CONSUMABLE
        assert sitrus.flags & ItemFlag.BERRY


class TestFlingPower:
    """Test Fling power values for items."""

    def test_assault_vest_has_high_fling_power(self):
        """Assault Vest should have high Fling power (80)."""
        vest = get_item(get_item_id("Assault Vest"))
        assert vest.fling_power == 80

    def test_rocky_helmet_has_fling_power(self):
        """Rocky Helmet should have Fling power (60)."""
        helmet = get_item(get_item_id("Rocky Helmet"))
        assert helmet.fling_power == 60

    def test_life_orb_has_fling_power(self):
        """Life Orb should have Fling power (30)."""
        life_orb = get_item(get_item_id("Life Orb"))
        assert life_orb.fling_power == 30

    def test_choice_items_have_low_fling_power(self):
        """Choice items should have low Fling power (10)."""
        for name in ["Choice Band", "Choice Specs", "Choice Scarf"]:
            item = get_item(get_item_id(name))
            assert item.fling_power == 10

    def test_leftovers_has_fling_power(self):
        """Leftovers should have Fling power (10)."""
        leftovers = get_item(get_item_id("Leftovers"))
        assert leftovers.fling_power == 10


class TestStatBoostingItems:
    """Test items that boost stats."""

    def test_assault_vest_description(self):
        """Assault Vest should mention Sp. Def boost."""
        vest = get_item(get_item_id("Assault Vest"))
        desc = vest.description.lower()
        assert "sp" in desc or "special" in desc

    def test_eviolite_description(self):
        """Eviolite should mention Defense and Sp. Def boost."""
        eviolite = get_item(get_item_id("Eviolite"))
        assert "Defense" in eviolite.description or "Def" in eviolite.description


class TestDamageModifyingItems:
    """Test items that modify damage."""

    def test_life_orb_description(self):
        """Life Orb should mention damage boost and HP loss."""
        life_orb = get_item(get_item_id("Life Orb"))
        desc = life_orb.description.lower()
        assert "damage" in desc or "1.3" in desc
        assert "hp" in desc

    def test_rocky_helmet_description(self):
        """Rocky Helmet should mention contact damage."""
        helmet = get_item(get_item_id("Rocky Helmet"))
        desc = helmet.description.lower()
        assert "contact" in desc


class TestHealingItems:
    """Test items that heal."""

    def test_leftovers_description(self):
        """Leftovers should mention HP healing."""
        leftovers = get_item(get_item_id("Leftovers"))
        desc = leftovers.description.lower()
        assert "heal" in desc or "hp" in desc

    def test_sitrus_berry_description(self):
        """Sitrus Berry should mention HP healing."""
        sitrus = get_item(get_item_id("Sitrus Berry"))
        desc = sitrus.description.lower()
        assert "heal" in desc or "hp" in desc


class TestSurvivalItems:
    """Test items that help survive attacks."""

    def test_focus_sash_description(self):
        """Focus Sash should mention surviving from full HP."""
        sash = get_item(get_item_id("Focus Sash"))
        desc = sash.description.lower()
        assert "full hp" in desc or "survives" in desc


class TestItemDescriptionQuality:
    """Test that item descriptions are meaningful."""

    def test_descriptions_not_empty(self):
        """All items should have non-empty descriptions."""
        for item in ITEM_REGISTRY.values():
            assert len(item.description) > 0

    def test_descriptions_are_sentences(self):
        """Descriptions should end with period."""
        for item in ITEM_REGISTRY.values():
            if len(item.description) > 10:
                assert item.description.endswith(".")


class TestItemNameConsistency:
    """Test item name formatting."""

    def test_names_not_empty(self):
        """All items should have non-empty names."""
        for item in ITEM_REGISTRY.values():
            assert len(item.name) > 0

    def test_names_are_title_case(self):
        """Item names should be in title case."""
        for item in ITEM_REGISTRY.values():
            words = item.name.split()
            for word in words:
                if word:
                    assert word[0].isupper() or word[0].isdigit()


class TestNoItemPlaceholder:
    """Test the No Item placeholder."""

    def test_no_item_has_id_zero(self):
        """No Item should have ID 0."""
        no_item = get_item(0)
        assert no_item.id == 0

    def test_no_item_has_no_flags(self):
        """No Item should have no flags."""
        no_item = get_item(0)
        assert no_item.flags == ItemFlag.NONE

    def test_no_item_has_zero_fling_power(self):
        """No Item should have 0 fling power."""
        no_item = get_item(0)
        assert no_item.fling_power == 0


class TestItemCategorization:
    """Test that items are properly categorized by flags."""

    def test_count_choice_items(self):
        """Should have at least 3 choice items."""
        choice_items = [
            item for item in ITEM_REGISTRY.values()
            if item.flags & ItemFlag.CHOICE
        ]
        assert len(choice_items) >= 3

    def test_count_consumable_items(self):
        """Should have some consumable items."""
        consumable_items = [
            item for item in ITEM_REGISTRY.values()
            if item.flags & ItemFlag.CONSUMABLE
        ]
        assert len(consumable_items) >= 1

    def test_count_berry_items(self):
        """Should have at least one berry."""
        berry_items = [
            item for item in ITEM_REGISTRY.values()
            if item.flags & ItemFlag.BERRY
        ]
        assert len(berry_items) >= 1
