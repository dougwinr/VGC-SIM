"""Tests for data/items.py - Item registry and data."""
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


class TestItemFlag:
    """Tests for the ItemFlag bitflags."""

    def test_none_flag_is_zero(self):
        """NONE flag should be 0."""
        assert ItemFlag.NONE == 0

    def test_flags_are_powers_of_two(self):
        """Each flag (except NONE) should be a power of 2."""
        for flag in ItemFlag:
            if flag != ItemFlag.NONE:
                assert flag.value & (flag.value - 1) == 0

    def test_flags_are_unique(self):
        """Each flag should have a unique value."""
        values = [f.value for f in ItemFlag]
        assert len(values) == len(set(values))

    def test_common_flags_exist(self):
        """Common item flags should exist."""
        assert ItemFlag.CONSUMABLE.value > 0
        assert ItemFlag.BERRY.value > 0
        assert ItemFlag.CHOICE.value > 0


class TestItemData:
    """Tests for the ItemData dataclass."""

    def test_create_item(self):
        """Should create an item with all fields."""
        item = ItemData(
            id=100,
            name="Test Item",
            description="A test item.",
            fling_power=30,
            flags=ItemFlag.CONSUMABLE,
        )
        assert item.id == 100
        assert item.name == "Test Item"
        assert item.description == "A test item."
        assert item.fling_power == 30
        assert item.flags == ItemFlag.CONSUMABLE

    def test_item_defaults(self):
        """Should have sensible defaults."""
        item = ItemData(
            id=101,
            name="Default Test",
            description="Test defaults.",
        )
        assert item.fling_power == 0
        assert item.flags == ItemFlag.NONE
        assert item.type_boost is None
        assert item.boost_amount == 1.0

    def test_item_with_type_boost(self):
        """Should support type-boosting items."""
        item = ItemData(
            id=102,
            name="Fire Plate",
            description="Boosts Fire moves.",
            type_boost=Type.FIRE,
            boost_amount=1.2,
        )
        assert item.type_boost == Type.FIRE
        assert item.boost_amount == 1.2

    def test_item_is_frozen(self):
        """ItemData should be immutable."""
        item = ItemData(
            id=103,
            name="Frozen Test",
            description="Test immutability.",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            item.name = "Changed"


class TestItemRegistry:
    """Tests for the ITEM_REGISTRY."""

    def test_registry_not_empty(self):
        """Registry should have registered items."""
        assert len(ITEM_REGISTRY) > 0

    def test_registry_has_common_items(self):
        """Registry should include common competitive items."""
        item_names = [i.name.lower() for i in ITEM_REGISTRY.values()]
        assert "choice band" in item_names
        assert "leftovers" in item_names
        assert "life orb" in item_names

    def test_no_item_placeholder_exists(self):
        """ID 0 should be reserved for 'No Item'."""
        assert 0 in ITEM_REGISTRY
        assert ITEM_REGISTRY[0].name == "No Item"

    def test_all_ids_unique(self):
        """All item IDs should be unique."""
        ids = list(ITEM_REGISTRY.keys())
        assert len(ids) == len(set(ids))


class TestGetItem:
    """Tests for get_item function."""

    def test_get_existing_item(self):
        """Should return item data for valid ID."""
        item = get_item(1)  # Choice Band
        assert item is not None
        assert item.name == "Choice Band"

    def test_get_nonexistent_item(self):
        """Should return None for invalid ID."""
        item = get_item(99999)
        assert item is None

    def test_get_no_item(self):
        """Should return No Item for ID 0."""
        item = get_item(0)
        assert item is not None
        assert item.name == "No Item"


class TestGetItemId:
    """Tests for get_item_id function."""

    def test_get_id_by_name(self):
        """Should return ID for valid item name."""
        item_id = get_item_id("Choice Band")
        assert item_id is not None
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

    def test_get_id_nonexistent(self):
        """Should return None for invalid item name."""
        assert get_item_id("NotARealItem") is None


class TestIsChoiceItem:
    """Tests for is_choice_item function."""

    def test_choice_band_is_choice(self):
        """Choice Band should be a choice item."""
        choice_band_id = get_item_id("Choice Band")
        assert is_choice_item(choice_band_id)

    def test_choice_specs_is_choice(self):
        """Choice Specs should be a choice item."""
        choice_specs_id = get_item_id("Choice Specs")
        assert is_choice_item(choice_specs_id)

    def test_choice_scarf_is_choice(self):
        """Choice Scarf should be a choice item."""
        choice_scarf_id = get_item_id("Choice Scarf")
        assert is_choice_item(choice_scarf_id)

    def test_leftovers_not_choice(self):
        """Leftovers should not be a choice item."""
        leftovers_id = get_item_id("Leftovers")
        assert not is_choice_item(leftovers_id)

    def test_invalid_id_not_choice(self):
        """Invalid ID should return False."""
        assert not is_choice_item(99999)


class TestIsBerry:
    """Tests for is_berry function."""

    def test_sitrus_berry_is_berry(self):
        """Sitrus Berry should be a berry."""
        sitrus_id = get_item_id("Sitrus Berry")
        assert is_berry(sitrus_id)

    def test_leftovers_not_berry(self):
        """Leftovers should not be a berry."""
        leftovers_id = get_item_id("Leftovers")
        assert not is_berry(leftovers_id)

    def test_invalid_id_not_berry(self):
        """Invalid ID should return False."""
        assert not is_berry(99999)


class TestItemByName:
    """Tests for ITEM_BY_NAME mapping."""

    def test_mapping_not_empty(self):
        """Mapping should have entries."""
        assert len(ITEM_BY_NAME) > 0

    def test_mapping_matches_registry(self):
        """Mapping should point to valid registry entries."""
        for name, item_id in ITEM_BY_NAME.items():
            assert item_id in ITEM_REGISTRY


class TestRegisterItem:
    """Tests for register_item function."""

    def test_register_new_item(self):
        """Should register a new item."""
        new_item = ItemData(
            id=998,
            name="Custom Test Item",
            description="For testing registration.",
            fling_power=50,
        )
        register_item(new_item)

        # Should be in registry
        assert 998 in ITEM_REGISTRY
        assert ITEM_REGISTRY[998].name == "Custom Test Item"

        # Should be accessible by name
        assert get_item_id("Custom Test Item") == 998
        assert get_item_id("customtestitem") == 998

    def test_register_updates_existing(self):
        """Registering with existing ID should update entry."""
        updated = ItemData(
            id=998,
            name="Updated Item",
            description="Updated description.",
            fling_power=100,
        )
        register_item(updated)
        assert ITEM_REGISTRY[998].name == "Updated Item"


class TestCommonItems:
    """Tests for specific common items."""

    def test_choice_items_lock_move(self):
        """All choice items should have CHOICE flag."""
        for name in ["Choice Band", "Choice Specs", "Choice Scarf"]:
            item = get_item(get_item_id(name))
            assert item.flags & ItemFlag.CHOICE

    def test_focus_sash_is_consumable(self):
        """Focus Sash should be consumable."""
        sash = get_item(get_item_id("Focus Sash"))
        assert sash.flags & ItemFlag.CONSUMABLE

    def test_sitrus_berry_is_consumable_berry(self):
        """Sitrus Berry should be both consumable and a berry."""
        sitrus = get_item(get_item_id("Sitrus Berry"))
        assert sitrus.flags & ItemFlag.CONSUMABLE
        assert sitrus.flags & ItemFlag.BERRY

    def test_leftovers_not_consumable(self):
        """Leftovers should not be consumable."""
        leftovers = get_item(get_item_id("Leftovers"))
        assert not (leftovers.flags & ItemFlag.CONSUMABLE)
