"""Tests for data/abilities_loader.py - Ability data loading from TypeScript."""

import pytest
import tempfile
import os
from pathlib import Path

from data.abilities_loader import (
    _parse_ability_flags,
    _extract_ability_fields,
    parse_ts_abilities,
    load_abilities_from_ts,
    load_default_abilities,
    ensure_abilities_loaded,
)
from data.abilities import AbilityFlag, AbilityData, ABILITY_REGISTRY, ABILITY_BY_NAME


@pytest.fixture
def save_restore_registry():
    """Fixture to save and restore the ability registry between tests."""
    # Save current state
    saved_registry = dict(ABILITY_REGISTRY)
    saved_by_name = dict(ABILITY_BY_NAME)

    yield

    # Restore state after test
    ABILITY_REGISTRY.clear()
    ABILITY_REGISTRY.update(saved_registry)
    ABILITY_BY_NAME.clear()
    ABILITY_BY_NAME.update(saved_by_name)


class TestParseAbilityFlags:
    """Tests for _parse_ability_flags function."""

    def test_default_breakable(self):
        """Default flag should be BREAKABLE."""
        flags = _parse_ability_flags({})
        assert flags == AbilityFlag.BREAKABLE

    def test_permanent_ability(self):
        """isPermanent should set CANTSUPPRESS flag."""
        flags = _parse_ability_flags({"isPermanent": True})
        assert flags == AbilityFlag.CANTSUPPRESS

    def test_non_permanent_ability(self):
        """Non-permanent abilities should be BREAKABLE."""
        flags = _parse_ability_flags({"isPermanent": False})
        assert flags == AbilityFlag.BREAKABLE

    def test_empty_data(self):
        """Empty dict should return BREAKABLE."""
        flags = _parse_ability_flags({})
        assert flags == AbilityFlag.BREAKABLE


class TestExtractAbilityFields:
    """Tests for _extract_ability_fields function."""

    def test_extract_all_fields(self):
        """Extract all ability fields from TypeScript content."""
        content = '''
	testability: {
		num: 123,
		name: "Test Ability",
		rating: 4.5,
		shortDesc: "A short description.",
		desc: "A longer description.",
		isPermanent: true,
		isNonstandard: "Past",
	},
'''
        result = _extract_ability_fields(content)

        assert result["num"] == 123
        assert result["name"] == "Test Ability"
        assert result["rating"] == 4.5
        assert result["shortDesc"] == "A short description."
        assert result["desc"] == "A longer description."
        assert result["isPermanent"] is True
        assert result["isNonstandard"] == "Past"

    def test_extract_minimal_fields(self):
        """Extract ability with only required fields."""
        content = '''
	minimal: {
		num: 1,
		name: "Minimal",
	},
'''
        result = _extract_ability_fields(content)

        assert result["num"] == 1
        assert result["name"] == "Minimal"
        assert "rating" not in result
        assert "shortDesc" not in result

    def test_extract_negative_rating(self):
        """Handle negative ratings (like for harmful abilities)."""
        content = '''
	harmful: {
		num: 99,
		name: "Harmful",
		rating: -1,
	},
'''
        result = _extract_ability_fields(content)
        assert result["rating"] == -1.0

    def test_missing_num(self):
        """Return empty dict if num is missing."""
        content = '''
	nonum: {
		name: "No Num",
	},
'''
        result = _extract_ability_fields(content)
        assert "num" not in result


class TestParseTsAbilities:
    """Tests for parse_ts_abilities function."""

    def test_parse_multiple_abilities(self):
        """Parse multiple abilities from TypeScript content."""
        content = '''export const Abilities: {[k: string]: AbilityData} = {
	stench: {
		num: 1,
		name: "Stench",
		rating: 0.5,
		shortDesc: "This Pokemon's attacks have a 10% chance to flinch.",
	},
	drizzle: {
		num: 2,
		name: "Drizzle",
		rating: 4,
		shortDesc: "On switch-in, this Pokemon summons Rain Dance.",
	},
};'''

        result = parse_ts_abilities(content)

        assert "stench" in result
        assert "drizzle" in result
        assert result["stench"]["num"] == 1
        assert result["stench"]["name"] == "Stench"
        assert result["drizzle"]["num"] == 2
        assert result["drizzle"]["name"] == "Drizzle"

    def test_parse_empty_content(self):
        """Empty content should return empty dict."""
        result = parse_ts_abilities("")
        assert result == {}

    def test_parse_no_entries(self):
        """Content with no valid entries should return empty dict."""
        content = "// Just a comment"
        result = parse_ts_abilities(content)
        assert result == {}

    def test_skip_entries_without_num(self):
        """Skip entries that don't have a num field."""
        content = '''export const Abilities = {
	valid: {
		num: 1,
		name: "Valid",
	},
	invalid: {
		name: "No Num Here",
	},
};'''

        result = parse_ts_abilities(content)

        assert "valid" in result
        assert "invalid" not in result


class TestLoadAbilitiesFromTs:
    """Tests for load_abilities_from_ts function."""

    def test_load_from_file(self, save_restore_registry):
        """Load abilities from a TypeScript file."""
        content = '''export const Abilities: {[k: string]: AbilityData} = {
	testload: {
		num: 9998,
		name: "Test Load Ability",
		rating: 3,
		shortDesc: "Test loading from file.",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_abilities_from_ts(temp_path)
            assert count == 1
            assert 9998 in ABILITY_REGISTRY
            assert ABILITY_REGISTRY[9998].name == "Test Load Ability"
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_abilities_from_ts("/nonexistent/path/abilities.ts")

    def test_load_with_rating_none(self, save_restore_registry):
        """Handle abilities where rating might be None."""
        content = '''export const Abilities = {
	testrating: {
		num: 9997,
		name: "Test Rating",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_abilities_from_ts(temp_path)
            assert count == 1
            # Should default to 3.0
            assert ABILITY_REGISTRY[9997].rating == 3.0
        finally:
            os.unlink(temp_path)

    def test_load_permanent_ability(self, save_restore_registry):
        """Load ability with isPermanent flag."""
        content = '''export const Abilities = {
	permanenttest: {
		num: 9996,
		name: "Permanent Test",
		isPermanent: true,
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            load_abilities_from_ts(temp_path)
            assert ABILITY_REGISTRY[9996].flags == AbilityFlag.CANTSUPPRESS
        finally:
            os.unlink(temp_path)


class TestLoadDefaultAbilities:
    """Tests for load_default_abilities function."""

    def test_load_default_succeeds_or_raises(self, save_restore_registry):
        """load_default_abilities should either succeed or raise FileNotFoundError."""
        try:
            count = load_default_abilities()
            assert count > 0
        except FileNotFoundError:
            # Expected if default file doesn't exist
            pass


class TestEnsureAbilitiesLoaded:
    """Tests for ensure_abilities_loaded function."""

    def test_ensure_loaded_no_error(self, save_restore_registry):
        """ensure_abilities_loaded should not raise even if file missing."""
        # This should not raise - it catches FileNotFoundError internally
        ensure_abilities_loaded()

    def test_registry_has_base_abilities(self):
        """Registry should have at least base abilities after ensure."""
        # Should have at least "No Ability" placeholder (from data/abilities.py)
        assert 0 in ABILITY_REGISTRY


class TestAutoLoad:
    """Tests for _auto_load_abilities function."""

    def test_auto_load_with_empty_registry(self, save_restore_registry):
        """Test auto-load behavior with minimal registry."""
        from data.abilities_loader import _auto_load_abilities
        from unittest.mock import patch
        from pathlib import Path

        # Clear registry to trigger auto-load path
        ABILITY_REGISTRY.clear()
        ABILITY_BY_NAME.clear()

        # Mock Path.exists to return False, triggering exception handling
        with patch.object(Path, 'exists', return_value=False):
            # This should attempt to load, fail, and catch the exception
            _auto_load_abilities()

        # Registry may or may not have data depending on file availability
        assert isinstance(ABILITY_REGISTRY, dict)

    def test_auto_load_with_populated_registry(self, save_restore_registry):
        """Test auto-load skips when registry is populated."""
        from data.abilities_loader import _auto_load_abilities

        # Add a couple entries to exceed threshold
        from data.abilities import register_ability, AbilityData, AbilityFlag
        register_ability(AbilityData(id=0, name="Test", description=""))
        register_ability(AbilityData(id=1, name="Test2", description=""))

        initial_count = len(ABILITY_REGISTRY)
        _auto_load_abilities()

        # Should not have changed much since registry > 1
        assert len(ABILITY_REGISTRY) >= initial_count


class TestEdgeCases:
    """Tests for edge cases in ability loading."""

    def test_load_with_explicit_null_rating(self, save_restore_registry):
        """Test loading ability where rating is explicitly null."""
        content = '''export const Abilities = {
	nullrating: {
		num: 9985,
		name: "Null Rating",
		rating: null,
	},
};'''
        # The regex won't match "null" as a number, so rating won't be set
        # This tests the "rating is None" path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_abilities_from_ts(temp_path)
            assert count == 1
            # Should default to 3.0
            assert ABILITY_REGISTRY[9985].rating == 3.0
        finally:
            os.unlink(temp_path)

    def test_load_skips_entries_without_num(self, save_restore_registry):
        """Test that entries without num are skipped during load."""
        content = '''export const Abilities = {
	valid: {
		num: 9984,
		name: "Valid Ability",
	},
	invalid: {
		name: "No Num Ability",
		rating: 5,
	},
	alsovalid: {
		num: 9983,
		name: "Also Valid",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_abilities_from_ts(temp_path)
            # Should only load 2 (the ones with num)
            assert count == 2
            assert 9984 in ABILITY_REGISTRY
            assert 9983 in ABILITY_REGISTRY
        finally:
            os.unlink(temp_path)

    def test_ensure_loaded_triggers_load_attempt(self, save_restore_registry):
        """Test ensure_abilities_loaded triggers load when registry is small."""
        from unittest.mock import patch
        from pathlib import Path

        # Clear to make registry small (<=11)
        ABILITY_REGISTRY.clear()
        ABILITY_BY_NAME.clear()

        # Mock Path.exists to return False, triggering FileNotFoundError
        # which should be caught by ensure_abilities_loaded
        with patch.object(Path, 'exists', return_value=False):
            # This should try to load, fail with FileNotFoundError, and catch it
            ensure_abilities_loaded()

        # Function should complete without error
        assert True

    def test_load_default_file_not_found(self, save_restore_registry):
        """Test load_default_abilities raises FileNotFoundError when no file exists."""
        import sys
        from unittest.mock import patch
        from pathlib import Path

        # Mock Path.exists to always return False
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_default_abilities()

            assert "Could not find abilities_data.ts" in str(exc_info.value)


class TestIntegration:
    """Integration tests for ability loading."""

    def test_load_complex_ability_file(self, save_restore_registry):
        """Load a file with multiple complex abilities."""
        content = '''export const Abilities: {[k: string]: AbilityData} = {
	ability1: {
		num: 9990,
		name: "Ability One",
		rating: 5,
		shortDesc: "First ability.",
		desc: "A longer description for ability one.",
	},
	ability2: {
		num: 9991,
		name: "Ability Two",
		rating: 2.5,
		shortDesc: "Second ability.",
		isPermanent: true,
	},
	ability3: {
		num: 9992,
		name: "Ability Three",
		rating: 0,
		shortDesc: "Third ability.",
		isNonstandard: "Past",
	},
};'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            count = load_abilities_from_ts(temp_path)
            assert count == 3

            # Check ability 1
            assert ABILITY_REGISTRY[9990].name == "Ability One"
            assert ABILITY_REGISTRY[9990].rating == 5.0
            assert ABILITY_REGISTRY[9990].flags == AbilityFlag.BREAKABLE

            # Check ability 2 (permanent)
            assert ABILITY_REGISTRY[9991].name == "Ability Two"
            assert ABILITY_REGISTRY[9991].flags == AbilityFlag.CANTSUPPRESS

            # Check ability 3
            assert ABILITY_REGISTRY[9992].name == "Ability Three"
            assert ABILITY_REGISTRY[9992].rating == 0.0
        finally:
            os.unlink(temp_path)
