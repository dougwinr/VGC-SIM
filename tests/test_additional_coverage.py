"""Additional tests for coverage of remaining edge cases."""

import pytest
from unittest.mock import patch, MagicMock
import random

# Tests for data/species_loader.py edge cases
class TestSpeciesLoaderEdgeCases:
    """Test species_loader.py edge cases."""

    def test_infer_generation_invalid_gen_tag(self):
        """Test _infer_generation with invalid Gen tag (lines 168-169)."""
        from data.species_loader import _infer_generation

        # A tag like "Geninvalid" should be handled
        result = _infer_generation(0, ["Geninvalid", "SomeOtherTag"])
        # Should fall through to dex-based generation
        assert result == 0  # dex_num <= 0 returns 0

    def test_infer_generation_gen_tag_with_valid_suffix(self):
        """Test _infer_generation with valid Gen tag."""
        from data.species_loader import _infer_generation

        result = _infer_generation(0, ["Gen5", "SomeTag"])
        assert result == 5

    def test_infer_generation_by_dex_ranges(self):
        """Test _infer_generation inferring from dex number."""
        from data.species_loader import _infer_generation

        # Test various ranges
        assert _infer_generation(1, []) == 1    # Gen 1
        assert _infer_generation(152, []) == 2  # Gen 2
        assert _infer_generation(252, []) == 3  # Gen 3
        assert _infer_generation(387, []) == 4  # Gen 4
        assert _infer_generation(494, []) == 5  # Gen 5
        assert _infer_generation(650, []) == 6  # Gen 6
        assert _infer_generation(722, []) == 7  # Gen 7
        assert _infer_generation(810, []) == 8  # Gen 8
        assert _infer_generation(1000, []) == 9  # Gen 9

    def test_parse_tags_non_list(self):
        """Test _parse_tags with non-list value."""
        from data.species_loader import _parse_tags

        # Test with dict that has tags as non-list
        result = _parse_tags({"tags": "not_a_list"})
        assert result == ()

    def test_parse_tags_with_list(self):
        """Test _parse_tags with valid list."""
        from data.species_loader import _parse_tags

        result = _parse_tags({"tags": ["Tag1", "Tag2"]})
        assert result == ("Tag1", "Tag2")


# Tests for parsers/showdown_log_parser.py remaining line
class TestShowdownLogParserRemainingEdgeCases:
    """Test remaining edge case in showdown_log_parser."""

    def test_parse_event_line_truly_empty_parts(self):
        """Test parse_event_line with edge case that causes empty parts (line 170)."""
        from parsers.showdown_log_parser import parse_event_line, LogEventType

        # Test with a line that is just a pipe followed by nothing
        # This test simply verifies the parser doesn't crash
        result = parse_event_line("|")
        # Result should be a BattleLogEvent with UNKNOWN type
        assert result is not None
        assert result.event_type == LogEventType.UNKNOWN


# Tests for tournament/runner.py edge cases
class TestTournamentRunnerEdgeCases:
    """Test tournament runner edge cases."""

    def test_action_to_choice_with_target(self):
        """Test _action_to_choice with different targets."""
        from tournament.runner import _action_to_choice
        from agents import Action, ActionKind

        # Create an action targeting opponent (different side)
        action = Action.move(
            slot=0,
            move_slot=1,
            target_side=1,
            target_slot=0,
        )

        # When target_side != player_side (1 != 0), target should be positive
        choice = _action_to_choice(action, player_side=0)
        assert choice.target == 1  # target_slot + 1 = 0 + 1 = 1

    def test_action_to_choice_ally_target(self):
        """Test _action_to_choice with ally target (same side)."""
        from tournament.runner import _action_to_choice
        from agents import Action, ActionKind

        # Create an action targeting ally (same side as player)
        action = Action.move(
            slot=0,
            move_slot=1,
            target_side=0,  # Same as player_side
            target_slot=1,
        )

        # When target_side == player_side, target should be negative
        choice = _action_to_choice(action, player_side=0)
        assert choice.target == -2  # -(target_slot + 1) = -(1 + 1) = -2

    def test_action_to_choice_switch(self):
        """Test _action_to_choice for switch action."""
        from tournament.runner import _action_to_choice
        from agents import Action

        # Create a switch action
        action = Action.switch(
            slot=0,
            switch_to=2,  # Switching to team slot 2
        )

        choice = _action_to_choice(action, player_side=0)
        assert choice.choice_type == "switch"

    def test_action_to_choice_pass(self):
        """Test _action_to_choice for pass action."""
        from tournament.runner import _action_to_choice
        from agents import Action

        # Create a pass action
        action = Action.pass_action(slot=0)

        choice = _action_to_choice(action, player_side=0)
        assert choice.choice_type == "pass"


# Tests for parsers/showdown_protocol.py remaining lines
class TestShowdownProtocolRemainingEdgeCases:
    """Test remaining edge cases in showdown_protocol."""

    def test_parse_line_only_pipe(self):
        """Test parsing line that is just | (line 174)."""
        from parsers.showdown_protocol import ProtocolParser, MessageType

        parser = ProtocolParser()
        # This should not crash and return something sensible
        result = parser.parse_line("|")
        assert result is not None

    def test_parse_details_empty(self):
        """Test parse_details with empty string (line 258)."""
        from parsers.showdown_protocol import ProtocolParser

        parser = ProtocolParser()
        result = parser.parse_details("")
        # Should return defaults
        assert result["level"] == 100

    def test_move_choice_numeric_target_no_sign(self):
        """Test move choice with numeric target without sign (lines 705-708)."""
        from parsers.showdown_protocol import ChoiceParser

        parser = ChoiceParser()
        result = parser.parse_choice("move 1 2")  # Target 2 without + sign
        assert result[0].target == 2

    def test_format_choice_move_with_name(self):
        """Test format_choice for move with name instead of slot (line 736)."""
        from parsers.showdown_protocol import ChoiceParser, Choice

        parser = ChoiceParser()
        choices = [Choice("move", slot=0, move_name="Thunderbolt")]
        result = parser.format_choice(choices)
        assert "move Thunderbolt" in result

    def test_replayer_handle_move(self):
        """Test ProtocolReplayer _handle_move."""
        from parsers.showdown_protocol import ProtocolReplayer

        replayer = ProtocolReplayer()
        state = replayer.replay("|move|p1a: Pikachu|Thunderbolt|p2a: Charizard")
        assert any(e.get("type") == "move" for e in replayer.events)

    def test_replayer_handle_switch(self):
        """Test ProtocolReplayer _handle_switch."""
        from parsers.showdown_protocol import ProtocolReplayer

        replayer = ProtocolReplayer()
        state = replayer.replay("|switch|p1a: Pikachu|Pikachu, L50, M|100/100")
        # Check switch was tracked
        assert "p1a" in state.pokemon_hp or len(replayer.events) > 0

    def test_replayer_handle_damage(self):
        """Test ProtocolReplayer _handle_damage."""
        from parsers.showdown_protocol import ProtocolReplayer

        replayer = ProtocolReplayer()
        # First switch to add pokemon, then damage
        state = replayer.replay("|switch|p1a: Pikachu|Pikachu, L50, M|100/100\n|-damage|p1a: Pikachu|50/100")
        assert state.pokemon_hp.get("p1a") == (50, 100)

    def test_replayer_handle_heal(self):
        """Test ProtocolReplayer _handle_heal."""
        from parsers.showdown_protocol import ProtocolReplayer

        replayer = ProtocolReplayer()
        state = replayer.replay("|switch|p1a: Pikachu|Pikachu, L50, M|50/100\n|-heal|p1a: Pikachu|75/100")
        assert state.pokemon_hp.get("p1a") == (75, 100)

    def test_replayer_handle_faint(self):
        """Test ProtocolReplayer _handle_faint."""
        from parsers.showdown_protocol import ProtocolReplayer

        replayer = ProtocolReplayer()
        state = replayer.replay("|switch|p1a: Pikachu|Pikachu, L50, M|100/100\n|faint|p1a: Pikachu")
        # Faint events are tracked in the events list
        assert any(e.get("type") == "faint" for e in replayer.events)

    def test_replayer_handle_status(self):
        """Test ProtocolReplayer _handle_status."""
        from parsers.showdown_protocol import ProtocolReplayer

        replayer = ProtocolReplayer()
        state = replayer.replay("|-status|p1a: Pikachu|par")
        assert state.pokemon_status.get("p1a") == "par"

    def test_replayer_handle_curestatus(self):
        """Test ProtocolReplayer _handle_curestatus."""
        from parsers.showdown_protocol import ProtocolReplayer

        replayer = ProtocolReplayer()
        state = replayer.replay("|-status|p1a: Pikachu|par\n|-curestatus|p1a: Pikachu|par")
        assert state.pokemon_status.get("p1a") is None


# Tests for data/moves_loader.py remaining lines
class TestMovesLoaderRemainingEdgeCases:
    """Test remaining edge cases in moves_loader."""

    def test_parse_ts_move_with_correct_format(self):
        """Test parsing move with correct TypeScript format."""
        from data.moves_loader import parse_ts_moves

        # Use actual TypeScript format with tabs
        ts_content = 'export const Moves: {[id: string]: MoveData} = {\n\ttackle: {\n\t\tnum: 33,\n\t\taccuracy: 100,\n\t\tbasePower: 40,\n\t\tcategory: "Physical",\n\t\tname: "Tackle",\n\t\ttype: "Normal",\n\t\ttarget: "normal",\n\t},\n};'
        result = parse_ts_moves(ts_content)
        assert "tackle" in result

    def test_parse_ts_move_status(self):
        """Test parsing status move with no base power."""
        from data.moves_loader import parse_ts_moves

        # Use actual TypeScript format
        ts_content = 'export const Moves = {\n\tsplash: {\n\t\tnum: 150,\n\t\taccuracy: true,\n\t\tbasePower: 0,\n\t\tcategory: "Status",\n\t\tname: "Splash",\n\t\ttype: "Normal",\n\t\ttarget: "self",\n\t},\n};'
        result = parse_ts_moves(ts_content)
        assert "splash" in result
        assert result["splash"]["basePower"] == 0


# Tests for core/battle.py remaining lines
class TestBattleRemainingEdgeCases:
    """Test remaining edge cases in battle.py."""

    def test_battle_runs_without_crash(self):
        """Test battle runs without crashing."""
        from tests.test_battle_coverage import setup_doubles_battle
        from core.battle import BattleEngine, Choice

        state, engine = setup_doubles_battle(seed=42)

        # Run a few turns
        for _ in range(3):
            if engine.check_victory() is not None:
                break
            choices = {
                0: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
                1: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
            }
            engine.step(choices)

        # Should complete without error
        assert True
