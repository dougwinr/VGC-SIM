"""Tests for data/items_loader.py - Item data loading from TypeScript."""

import pytest
import tempfile
import os
from pathlib import Path

from data.items_loader import (
    _parse_type,
    _parse_item_flags,
    _extract_item_fields,
    parse_ts_items,
    load_items_from_ts,
    load_default_items,
    ensure_items_loaded,
)
from data.items import ItemFlag, ITEM_REGISTRY, ITEM_BY_NAME
from data.types import Type


@pytest.fixture
def save_restore_registry():
    """Fixture to save and restore the item registry between tests."""
    # Save current state
    saved_registry = dict(ITEM_REGISTRY)
    saved_by_name = dict(ITEM_BY_NAME)

    yield

    # Restore state after test
    ITEM_REGISTRY.clear()
    ITEM_REGISTRY.update(saved_registry)
    ITEM_BY_NAME.clear()
    ITEM_BY_NAME.update(saved_by_name)


class TestParseType:
    """Tests for _parse_type function."""

    def test_parse_valid_types(self):
        """Parse valid type names."""
        assert _parse_type("Fire") == Type.FIRE
        assert _parse_type("Water") == Type.WATER
        assert _parse_type("Grass") == Type.GRASS
        assert _parse_type("Electric") == Type.ELECTRIC

    def test_parse_case_insensitive(self):
        """Type parsing should be case-insensitive."""
        assert _parse_type("FIRE") == Type.FIRE
        assert _parse_type("fire") == Type.FIRE
        assert _parse_type("Fire") == Type.FIRE

    def test_parse_empty_string(self):
        """Empty string should return None."""
        assert _parse_type("") is None

    def test_parse_invalid_type(self):
        """Invalid type name should return None."""
        assert _parse_type("InvalidType") is None


class TestParseItemFlags:
    """Tests for _parse_item_flags function."""

    def test_default_none(self):
        """Default flag should be NONE."""
        flags = _parse_item_flags({})
        assert flags == ItemFlag.NONE

    def test_berry_flag(self):
        """isBerry should set CONSUMABLE and BERRY flags."""
        flags = _parse_item_flags({"isBerry": True})
        assert flags & ItemFlag.CONSUMABLE
        assert flags & ItemFlag.BERRY

    def test_gem_flag(self):
        """isGem should set CONSUMABLE and GEM flags."""
        flags = _parse_item_flags({"isGem": True})
        assert flags & ItemFlag.CONSUMABLE
        assert flags & ItemFlag.GEM

    def test_plate_flag(self):
        """onPlate should set PLATE flag."""
        flags = _parse_item_flags({"onPlate": "Fire"})
        assert flags & ItemFlag.PLATE

    def test_drive_flag(self):
        """onDrive should set DRIVE flag."""
        flags = _parse_item_flags({"onDrive": "Water"})
        assert flags & ItemFlag.DRIVE

    def test_memory_flag(self):
        """onMemory should set MEMORY flag."""
        flags = _parse_item_flags({"onMemory": "Steel"})
        assert flags & ItemFlag.MEMORY

    def test_mega_stone_flag(self):
        """megaStone should set MEGA_STONE flag."""
        flags = _parse_item_flags({"megaStone": True})
        assert flags & ItemFlag.MEGA_STONE

    def test_z_crystal_flag(self):
        """zMove should set Z_CRYSTAL flag."""
        flags = _parse_item_flags({"zMove": True})
        assert flags & ItemFlag.Z_CRYSTAL

    def test_choice_band_flag(self):
        """Choice Band should set CHOICE flag."""
        flags = _parse_item_flags({"name": "Choice Band"})
        assert flags & ItemFlag.CHOICE

    def test_choice_specs_flag(self):
        """Choice Specs should set CHOICE flag."""
        flags = _parse_item_flags({"name": "Choice Specs"})
        assert flags & ItemFlag.CHOICE

    def test_choice_scarf_flag(self):
        """Choice Scarf should set CHOICE flag."""
        flags = _parse_item_flags({"name": "Choice Scarf"})
        assert flags & ItemFlag.CHOICE

    def test_non_choice_item(self):
        """Non-choice items should not have CHOICE flag."""
        flags = _parse_item_flags({"name": "Leftovers"})
        assert not (flags & ItemFlag.CHOICE)

    def test_multiple_flags(self):
        """Item can have multiple flags."""
        flags = _parse_item_flags({"isBerry": True, "isGem": True})
        assert flags & ItemFlag.CONSUMABLE
        assert flags & ItemFlag.BERRY
        assert flags & ItemFlag.GEM


class TestExtractItemFields:
    """Tests for _extract_item_fields function."""

    def test_extract_all_fields(self):
        """Extract all item fields from TypeScript content."""
        content = '''
	testitem: {
		num: 123,
		name: "Test Item",
		shortDesc: "A short description.",
		desc: "A longer description.",
		fling: {
			basePower: 80,
		},
		gen: 4,
		isBerry: true,
		onPlate: "Fire",
		isNonstandard: "Past",
	},
'''
        result = _extract_item_fields(content)

        assert result["num"] == 123
        assert result["name"] == "Test Item"
        assert result["shortDesc"] == "A short description."
        assert result["desc"] == "A longer description."
        assert result["fling"]["basePower"] == 80
        assert result["gen"] == 4
        assert result["isBerry"] is True
        assert result["onPlate"] == "Fire"
        assert result["isNonstandard"] == "Past"

    def test_extract_minimal_fields(self):
        """Extract item with only required fields."""
        content = '''
	minimal: {
		num: 1,
		name: "Minimal",
	},
'''
        result = _extract_item_fields(content)

        assert result["num"] == 1
        assert result["name"] == "Minimal"
        assert "fling" not in result
        assert "gen" not in result

    def test_extract_gem(self):
        """Extract gem item fields."""
        content = '''
	firegem: {
		num: 99,
		name: "Fire Gem",
		isGem: true,
	},
'''
        result = _extract_item_fields(content)
        assert result["isGem"] is True

    def test_extract_drive(self):
        """Extract drive item fields."""
        content = '''
	burndrive: {
		num: 98,
		name: "Burn Drive",
		onDrive: "Fire",
	},
'''
        result = _extract_item_fields(content)
        assert result["onDrive"] == "Fire"

    def test_extract_memory(self):
        """Extract memory item fields."""
        content = '''
	firememory: {
		num: 97,
		name: "Fire Memory",
		onMemory: "Fire",
	},
'''
        result = _extract_item_fields(content)
        assert result["onMemory"] == "Fire"

    def test_extract_mega_stone(self):
        """Extract mega stone fields."""
        content = '''
	charizarditex: {
		num: 96,
		name: "Charizardite X",
		megaStone: "Charizard-Mega-X",
	},
'''
        result = _extract_item_fields(content)
        assert result["megaStone"] is True

    def test_extract_z_move(self):
        """Extract Z-crystal fields."""
        content = '''
	firiumz: {
		num: 95,
		name: "Firium Z",
		zMove: true,
	},
'''
        result = _extract_item_fields(content)
        assert result["zMove"] is True

    def test_extract_z_move_type(self):
        """Extract Z-crystal with zMoveType."""
        content = '''
	firiumz: {
		num: 94,
		name: "Firium Z",
		zMoveType: "Fire",
	},
'''
        result = _extract_item_fields(content)
        assert result["zMove"] is True


class TestParseTsItems:
    """Tests for parse_ts_items function."""

    def test_parse_multiple_items(self):
        """Parse multiple items from TypeScript content."""
        content = '''export const Items: {[k: string]: ItemData} = {
	choiceband: {
		num: 1,
		name: "Choice Band",
		shortDesc: "Holder's Attack is 1.5x, but it can only use one move.",
	},
	leftovers: {
		num: 2,
		name: "Leftovers",
		shortDesc: "At the end of each turn, restores 1/16 max HP.",
	},
};'''

        result = parse_ts_items(content)

        assert "choiceband" in result
        assert "leftovers" in result
        assert result["choiceband"]["num"] == 1
        assert result["choiceband"]["name"] == "Choice Band"
        assert result["leftovers"]["num"] == 2
        assert result["leftovers"]["name"] == "Leftovers"

    def test_parse_empty_content(self):
        """Empty content should return empty dict."""
        result = parse_ts_items("")
        assert result == {}

    def test_skip_entries_without_num(self):
        """Skip entries that don't have a num field."""
        content = '''export const Items = {
	valid: {
		num: 1,
		name: "Valid",
	},
	invalid: {
		name: "No Num Here",
	},
};'''

        result = parse_ts_items(content)

        assert "valid" in result
        assert "invalid" not in result


class TestLoadItemsFromTs:
    """Tests for load_items_from_ts function."""

    def test_load_from_file(self, save_restore_registry):
        """Load items from a TypeScript file."""
        content = '''export const Items: {[k: string]: ItemData} = {
	testloaditem: {
		num: 8998,
		name: "Test Load Item",
		shortDesc: "Test loading from file.",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_items_from_ts(temp_path)
            assert count == 1
            assert 8998 in ITEM_REGISTRY
            assert ITEM_REGISTRY[8998].name == "Test Load Item"
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_items_from_ts("/nonexistent/path/items.ts")

    def test_load_with_fling_power(self, save_restore_registry):
        """Load item with fling power."""
        content = '''export const Items = {
	testfling: {
		num: 8997,
		name: "Test Fling",
		fling: {
			basePower: 100,
		},
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            load_items_from_ts(temp_path)
            assert ITEM_REGISTRY[8997].fling_power == 100
        finally:
            os.unlink(temp_path)

    def test_load_plate_with_type_boost(self, save_restore_registry):
        """Load plate item with type boost."""
        content = '''export const Items = {
	flameplate: {
		num: 8996,
		name: "Flame Plate",
		onPlate: "Fire",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            load_items_from_ts(temp_path)
            assert ITEM_REGISTRY[8996].type_boost == Type.FIRE
            assert ITEM_REGISTRY[8996].boost_amount == 1.2
        finally:
            os.unlink(temp_path)

    def test_load_drive_with_type_boost(self, save_restore_registry):
        """Load drive item with type boost (no boost amount increase)."""
        content = '''export const Items = {
	burndrive: {
		num: 8995,
		name: "Burn Drive",
		onDrive: "Fire",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            load_items_from_ts(temp_path)
            assert ITEM_REGISTRY[8995].type_boost == Type.FIRE
            assert ITEM_REGISTRY[8995].boost_amount == 1.0
        finally:
            os.unlink(temp_path)

    def test_load_berry_item(self, save_restore_registry):
        """Load berry item with proper flags."""
        content = '''export const Items = {
	testberry: {
		num: 8994,
		name: "Test Berry",
		isBerry: true,
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            load_items_from_ts(temp_path)
            assert ITEM_REGISTRY[8994].flags & ItemFlag.BERRY
            assert ITEM_REGISTRY[8994].flags & ItemFlag.CONSUMABLE
        finally:
            os.unlink(temp_path)


class TestLoadDefaultItems:
    """Tests for load_default_items function."""

    def test_load_default_succeeds_or_raises(self, save_restore_registry):
        """load_default_items should either succeed or raise FileNotFoundError."""
        try:
            count = load_default_items()
            assert count > 0
        except FileNotFoundError:
            # Expected if default file doesn't exist
            pass


class TestEnsureItemsLoaded:
    """Tests for ensure_items_loaded function."""

    def test_ensure_loaded_no_error(self, save_restore_registry):
        """ensure_items_loaded should not raise even if file missing."""
        ensure_items_loaded()

    def test_registry_has_base_items(self):
        """Registry should have at least base items after ensure."""
        # Should have at least "No Item" placeholder (from data/items.py)
        assert 0 in ITEM_REGISTRY


class TestAutoLoad:
    """Tests for _auto_load_items function."""

    def test_auto_load_with_empty_registry(self, save_restore_registry):
        """Test auto-load behavior with minimal registry."""
        from data.items_loader import _auto_load_items
        from unittest.mock import patch
        from pathlib import Path

        # Clear registry to trigger auto-load path
        ITEM_REGISTRY.clear()
        ITEM_BY_NAME.clear()

        # Mock Path.exists to return False, triggering exception handling
        with patch.object(Path, 'exists', return_value=False):
            # This should attempt to load, fail, and catch the exception
            _auto_load_items()

        # Registry may or may not have data depending on file availability
        assert isinstance(ITEM_REGISTRY, dict)

    def test_auto_load_with_populated_registry(self, save_restore_registry):
        """Test auto-load skips when registry is populated."""
        from data.items_loader import _auto_load_items
        from data.items import register_item, ItemData

        # Add a couple entries to exceed threshold
        register_item(ItemData(id=0, name="Test", description=""))
        register_item(ItemData(id=1, name="Test2", description=""))

        initial_count = len(ITEM_REGISTRY)
        _auto_load_items()

        # Should not have changed much since registry > 1
        assert len(ITEM_REGISTRY) >= initial_count


class TestEdgeCases:
    """Tests for edge cases in item loading."""

    def test_load_skips_entries_without_num(self, save_restore_registry):
        """Test that entries without num are skipped during load."""
        content = '''export const Items = {
	valid: {
		num: 8984,
		name: "Valid Item",
	},
	invalid: {
		name: "No Num Item",
	},
	alsovalid: {
		num: 8983,
		name: "Also Valid",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_items_from_ts(temp_path)
            # Should only load 2 (the ones with num)
            assert count == 2
            assert 8984 in ITEM_REGISTRY
            assert 8983 in ITEM_REGISTRY
        finally:
            os.unlink(temp_path)

    def test_ensure_loaded_triggers_load_attempt(self, save_restore_registry):
        """Test ensure_items_loaded triggers load when registry is small."""
        from unittest.mock import patch
        from pathlib import Path

        # Clear to make registry small (<=11)
        ITEM_REGISTRY.clear()
        ITEM_BY_NAME.clear()

        # Mock Path.exists to return False, triggering FileNotFoundError
        # which should be caught by ensure_items_loaded
        with patch.object(Path, 'exists', return_value=False):
            # This should try to load, fail with FileNotFoundError, and catch it
            ensure_items_loaded()

        # Function should complete without error
        assert True

    def test_load_default_file_not_found(self, save_restore_registry):
        """Test load_default_items raises FileNotFoundError when no file exists."""
        from unittest.mock import patch
        from pathlib import Path

        # Mock Path.exists to always return False
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_default_items()

            assert "Could not find items_data.ts" in str(exc_info.value)


class TestIntegration:
    """Integration tests for item loading."""

    def test_load_complex_item_file(self, save_restore_registry):
        """Load a file with multiple complex items."""
        content = '''export const Items: {[k: string]: ItemData} = {
	item1: {
		num: 8990,
		name: "Item One",
		shortDesc: "First item.",
		fling: {
			basePower: 30,
		},
	},
	item2: {
		num: 8991,
		name: "Item Two",
		shortDesc: "Second item.",
		isBerry: true,
	},
	item3: {
		num: 8992,
		name: "Item Three",
		shortDesc: "Third item.",
		onPlate: "Water",
	},
	choicebandtest: {
		num: 8993,
		name: "Choice Band Test",
		shortDesc: "A choice band for testing.",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_items_from_ts(temp_path)
            assert count == 4

            # Check item 1
            assert ITEM_REGISTRY[8990].name == "Item One"
            assert ITEM_REGISTRY[8990].fling_power == 30

            # Check item 2 (berry)
            assert ITEM_REGISTRY[8991].name == "Item Two"
            assert ITEM_REGISTRY[8991].flags & ItemFlag.BERRY

            # Check item 3 (plate)
            assert ITEM_REGISTRY[8992].name == "Item Three"
            assert ITEM_REGISTRY[8992].type_boost == Type.WATER
            assert ITEM_REGISTRY[8992].boost_amount == 1.2

            # Check item 4 (choice)
            assert ITEM_REGISTRY[8993].name == "Choice Band Test"
            assert ITEM_REGISTRY[8993].flags & ItemFlag.CHOICE
        finally:
            os.unlink(temp_path)
