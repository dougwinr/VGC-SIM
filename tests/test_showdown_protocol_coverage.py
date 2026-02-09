"""Tests for showdown_protocol.py to improve coverage."""

import pytest
from parsers.showdown_protocol import (
    MessageType,
    ProtocolMessage,
    ProtocolParser,
    ProtocolEmitter,
    ChoiceParser,
    Choice,
    ProtocolReplayer,
)


class TestProtocolMessage:
    """Tests for ProtocolMessage."""

    def test_message_str_empty_type(self):
        """Test __str__ for EMPTY message type (lines 141-142)."""
        msg = ProtocolMessage(MessageType.EMPTY, raw="|")
        assert str(msg) == "|"

    def test_message_str_with_kwargs(self):
        """Test __str__ with kwargs (lines 144-147)."""
        msg = ProtocolMessage(
            MessageType.DAMAGE,
            args=["p1a: Pikachu", "50/100"],
            kwargs={"from": "item: Life Orb", "of": "p2a: Charizard"}
        )
        result = str(msg)
        assert "|-damage|" in result
        assert "p1a: Pikachu" in result
        assert "[from] item: Life Orb" in result
        assert "[of] p2a: Charizard" in result


class TestProtocolParser:
    """Tests for ProtocolParser edge cases."""

    def test_parse_line_not_starting_with_pipe(self):
        """Test parsing line that doesn't start with | (line 170)."""
        parser = ProtocolParser()
        result = parser.parse_line("This is raw text")
        assert result.msg_type == MessageType.UNKNOWN
        assert result.raw == "This is raw text"

    def test_parse_line_empty_parts(self):
        """Test parsing line with empty parts after split (line 174)."""
        parser = ProtocolParser()
        # A line that is just "|"
        result = parser.parse_line("|")
        # Should not crash
        assert result is not None

    def test_parse_line_unknown_message_type(self):
        """Test parsing unknown message type (lines 180-188)."""
        parser = ProtocolParser()
        # Unknown message type without - prefix
        result = parser.parse_line("|unknowntype|arg1|arg2")
        assert result.msg_type == MessageType.UNKNOWN

    def test_parse_line_unknown_minor_action(self):
        """Test parsing unknown minor action with - prefix (lines 182-186)."""
        parser = ProtocolParser()
        result = parser.parse_line("|-unknownminor|p1a: Pikachu")
        assert result.msg_type == MessageType.UNKNOWN

    def test_parse_details_empty_parts(self):
        """Test parse_details with no parts (line 258)."""
        parser = ProtocolParser()
        result = parser.parse_details("")
        assert result["species"] == ""
        assert result["level"] == 100

    def test_parse_details_invalid_level(self):
        """Test parse_details with invalid level (lines 266-267)."""
        parser = ProtocolParser()
        result = parser.parse_details("Pikachu, Linvalid")
        assert result["species"] == "Pikachu"
        assert result["level"] == 100  # Default unchanged

    def test_parse_hp_status_escaped_slash(self):
        """Test parse_hp_status with escaped slashes (line 288)."""
        parser = ProtocolParser()
        current, max_hp, status = parser.parse_hp_status("75\\/100 psn")
        assert current == 75
        assert max_hp == 100
        assert status == "psn"

    def test_parse_hp_status_invalid_values(self):
        """Test parse_hp_status with invalid values (lines 298-299)."""
        parser = ProtocolParser()
        current, max_hp, status = parser.parse_hp_status("abc/def")
        assert current == 100
        assert max_hp == 100

    def test_parse_hp_status_single_value_invalid(self):
        """Test parse_hp_status with invalid single value (lines 305-306)."""
        parser = ProtocolParser()
        current, max_hp, status = parser.parse_hp_status("invalid")
        assert current == 100
        assert max_hp == 100


class TestProtocolEmitter:
    """Tests for ProtocolEmitter to cover all emit methods."""

    def test_clear(self):
        """Test clear method (line 321)."""
        emitter = ProtocolEmitter()
        emitter.emit("test")
        emitter.clear()
        assert emitter.messages == []

    def test_teamsize(self):
        """Test teamsize method (line 338)."""
        emitter = ProtocolEmitter()
        emitter.teamsize("p1", 6)
        assert "|teamsize|p1|6" in emitter.messages

    def test_tier(self):
        """Test tier method (line 350)."""
        emitter = ProtocolEmitter()
        emitter.tier("[Gen 9] VGC 2025")
        assert "|tier|[Gen 9] VGC 2025" in emitter.messages

    def test_rule(self):
        """Test rule method (line 354)."""
        emitter = ProtocolEmitter()
        emitter.rule("Species Clause")
        assert "|rule|Species Clause" in emitter.messages

    def test_clearpoke(self):
        """Test clearpoke method (line 358)."""
        emitter = ProtocolEmitter()
        emitter.clearpoke()
        assert "|clearpoke" in emitter.messages

    def test_poke_with_item(self):
        """Test poke method with item (lines 362-363)."""
        emitter = ProtocolEmitter()
        emitter.poke("p1", "Pikachu, L50, M", has_item=True)
        assert "|poke|p1|Pikachu, L50, M|item" in emitter.messages

    def test_poke_without_item(self):
        """Test poke method without item."""
        emitter = ProtocolEmitter()
        emitter.poke("p1", "Pikachu, L50, M", has_item=False)
        assert "|poke|p1|Pikachu, L50, M|" in emitter.messages

    def test_teampreview_with_count(self):
        """Test teampreview with count (lines 367-368)."""
        emitter = ProtocolEmitter()
        emitter.teampreview(4)
        assert "|teampreview|4" in emitter.messages

    def test_teampreview_without_count(self):
        """Test teampreview without count (lines 369-370)."""
        emitter = ProtocolEmitter()
        emitter.teampreview()
        assert "|teampreview" in emitter.messages

    def test_spacer(self):
        """Test spacer method (line 379)."""
        emitter = ProtocolEmitter()
        emitter.spacer()
        assert "|" in emitter.messages

    def test_upkeep(self):
        """Test upkeep method (line 387)."""
        emitter = ProtocolEmitter()
        emitter.upkeep()
        assert "|upkeep" in emitter.messages

    def test_tie(self):
        """Test tie method (line 395)."""
        emitter = ProtocolEmitter()
        emitter.tie()
        assert "|tie" in emitter.messages

    def test_drag(self):
        """Test drag method (line 404)."""
        emitter = ProtocolEmitter()
        emitter.drag("p1a: Pikachu", "Pikachu, L50, M", "100/100")
        assert "|drag|p1a: Pikachu|Pikachu, L50, M|100/100" in emitter.messages

    def test_move_with_miss(self):
        """Test move with miss flag (line 413)."""
        emitter = ProtocolEmitter()
        emitter.move("p1a: Pikachu", "Thunder", "p2a: Charizard", miss=True)
        assert any("[miss]" in m for m in emitter.messages)

    def test_cant_with_move(self):
        """Test cant with move (lines 418-419)."""
        emitter = ProtocolEmitter()
        emitter.cant("p1a: Pikachu", "par", "Thunder")
        assert "|cant|p1a: Pikachu|par|Thunder" in emitter.messages

    def test_cant_without_move(self):
        """Test cant without move (lines 420-421)."""
        emitter = ProtocolEmitter()
        emitter.cant("p1a: Pikachu", "slp")
        assert "|cant|p1a: Pikachu|slp" in emitter.messages

    def test_damage_with_source_and_of(self):
        """Test damage with source and of_pokemon (lines 435)."""
        emitter = ProtocolEmitter()
        emitter.damage("p1a: Pikachu", "50/100", source="item: Life Orb", of_pokemon="p2a: Charizard")
        msg = emitter.messages[-1]
        assert "|-damage|" in msg
        assert "[from] item: Life Orb" in msg
        assert "[of] p2a: Charizard" in msg

    def test_heal_with_source_and_of(self):
        """Test heal with source and of_pokemon (lines 441-446)."""
        emitter = ProtocolEmitter()
        emitter.heal("p1a: Pikachu", "100/100", source="item: Leftovers", of_pokemon="p2a: Charizard")
        msg = emitter.messages[-1]
        assert "|-heal|" in msg
        assert "[from] item: Leftovers" in msg
        assert "[of] p2a: Charizard" in msg

    def test_status_with_source_and_of(self):
        """Test status with source and of_pokemon (lines 452-457)."""
        emitter = ProtocolEmitter()
        emitter.status("p1a: Pikachu", "brn", source="move: Will-O-Wisp", of_pokemon="p2a: Charizard")
        msg = emitter.messages[-1]
        assert "|-status|" in msg
        assert "[from] move: Will-O-Wisp" in msg
        assert "[of] p2a: Charizard" in msg

    def test_curestatus_with_source(self):
        """Test curestatus with source (lines 461-464)."""
        emitter = ProtocolEmitter()
        emitter.curestatus("p1a: Pikachu", "brn", source="ability: Natural Cure")
        msg = emitter.messages[-1]
        assert "|-curestatus|" in msg
        assert "[from] ability: Natural Cure" in msg

    def test_unboost(self):
        """Test unboost method (line 473)."""
        emitter = ProtocolEmitter()
        emitter.unboost("p1a: Pikachu", "atk", 1)
        assert "|-unboost|p1a: Pikachu|atk|1" in emitter.messages

    def test_clearboost(self):
        """Test clearboost method (line 477)."""
        emitter = ProtocolEmitter()
        emitter.clearboost("p1a: Pikachu")
        assert "|-clearboost|p1a: Pikachu" in emitter.messages

    def test_fieldstart_with_source_and_of(self):
        """Test fieldstart with source and of_pokemon (lines 491-496)."""
        emitter = ProtocolEmitter()
        emitter.fieldstart("move: Psychic Terrain", source="ability: Psychic Surge", of_pokemon="p1a: Indeedee")
        msg = emitter.messages[-1]
        assert "|-fieldstart|" in msg
        assert "[from] ability: Psychic Surge" in msg
        assert "[of] p1a: Indeedee" in msg

    def test_fieldend(self):
        """Test fieldend method (line 500)."""
        emitter = ProtocolEmitter()
        emitter.fieldend("Psychic Terrain")
        assert "|-fieldend|Psychic Terrain" in emitter.messages

    def test_sideend(self):
        """Test sideend method (line 508)."""
        emitter = ProtocolEmitter()
        emitter.sideend("p1", "Reflect")
        assert "|-sideend|p1|Reflect" in emitter.messages

    def test_resisted(self):
        """Test resisted method (line 517)."""
        emitter = ProtocolEmitter()
        emitter.resisted("p2a: Charizard")
        assert "|-resisted|p2a: Charizard" in emitter.messages

    def test_immune(self):
        """Test immune method (line 521)."""
        emitter = ProtocolEmitter()
        emitter.immune("p2a: Gengar")
        assert "|-immune|p2a: Gengar" in emitter.messages

    def test_crit(self):
        """Test crit method (line 525)."""
        emitter = ProtocolEmitter()
        emitter.crit("p2a: Charizard")
        assert "|-crit|p2a: Charizard" in emitter.messages

    def test_ability_with_source_and_of(self):
        """Test ability with source and of_pokemon (lines 531-536)."""
        emitter = ProtocolEmitter()
        emitter.ability("p1a: Pikachu", "Lightning Rod", source="move: Skill Swap", of_pokemon="p2a: Raichu")
        msg = emitter.messages[-1]
        assert "|-ability|" in msg
        assert "[from] move: Skill Swap" in msg
        assert "[of] p2a: Raichu" in msg

    def test_item_with_source(self):
        """Test item with source (lines 540-543)."""
        emitter = ProtocolEmitter()
        emitter.item("p1a: Pikachu", "Light Ball", source="move: Trick")
        msg = emitter.messages[-1]
        assert "|-item|" in msg
        assert "[from] move: Trick" in msg

    def test_enditem_with_source(self):
        """Test enditem with source (lines 547-550)."""
        emitter = ProtocolEmitter()
        emitter.enditem("p1a: Pikachu", "Focus Sash", source="eaten")
        msg = emitter.messages[-1]
        assert "|-enditem|" in msg
        assert "[from] eaten" in msg

    def test_start_volatile_with_source_and_of(self):
        """Test start_volatile with source and of_pokemon (lines 556-561)."""
        emitter = ProtocolEmitter()
        emitter.start_volatile("p1a: Pikachu", "confusion", source="move: Confuse Ray", of_pokemon="p2a: Gengar")
        msg = emitter.messages[-1]
        assert "|-start|" in msg
        assert "confusion" in msg
        assert "[from] move: Confuse Ray" in msg
        assert "[of] p2a: Gengar" in msg

    def test_end_volatile(self):
        """Test end_volatile method (line 565)."""
        emitter = ProtocolEmitter()
        emitter.end_volatile("p1a: Pikachu", "confusion")
        assert "|-end|p1a: Pikachu|confusion" in emitter.messages

    def test_activate(self):
        """Test activate method (line 570)."""
        emitter = ProtocolEmitter()
        emitter.activate("p1a: Pikachu", "Protect")
        assert "|-activate|p1a: Pikachu|Protect" in emitter.messages

    def test_singleturn_with_of(self):
        """Test singleturn with of_pokemon (lines 574-577)."""
        emitter = ProtocolEmitter()
        emitter.singleturn("p1a: Pikachu", "Protect", of_pokemon="p2a: Charizard")
        msg = emitter.messages[-1]
        assert "|-singleturn|" in msg
        assert "[of] p2a: Charizard" in msg

    def test_terastallize(self):
        """Test terastallize method (line 582)."""
        emitter = ProtocolEmitter()
        emitter.terastallize("p1a: Pikachu", "Electric")
        assert "|-terastallize|p1a: Pikachu|Electric" in emitter.messages

    def test_fail_with_action(self):
        """Test fail with action (lines 587-588)."""
        emitter = ProtocolEmitter()
        emitter.fail("p1a: Pikachu", "move: Thunder Wave")
        assert "|-fail|p1a: Pikachu|move: Thunder Wave" in emitter.messages

    def test_fail_without_action(self):
        """Test fail without action (lines 589-590)."""
        emitter = ProtocolEmitter()
        emitter.fail("p1a: Pikachu")
        assert "|-fail|p1a: Pikachu" in emitter.messages

    def test_miss_with_target(self):
        """Test miss with target (lines 594-595)."""
        emitter = ProtocolEmitter()
        emitter.miss("p1a: Pikachu", "p2a: Charizard")
        assert "|-miss|p1a: Pikachu|p2a: Charizard" in emitter.messages

    def test_miss_without_target(self):
        """Test miss without target (lines 596-597)."""
        emitter = ProtocolEmitter()
        emitter.miss("p1a: Pikachu")
        assert "|-miss|p1a: Pikachu" in emitter.messages

    def test_hitcount(self):
        """Test hitcount method (line 601)."""
        emitter = ProtocolEmitter()
        emitter.hitcount("p2a: Charizard", 3)
        assert "|-hitcount|p2a: Charizard|3" in emitter.messages


class TestChoiceParser:
    """Tests for ChoiceParser edge cases."""

    def test_parse_choice_empty_tokens(self):
        """Test parsing empty tokens returns pass (line 651)."""
        parser = ChoiceParser()
        result = parser.parse_choice("")
        assert len(result) == 1
        assert result[0].choice_type == "pass"

    def test_parse_choice_default(self):
        """Test parsing default choice (line 668)."""
        parser = ChoiceParser()
        result = parser.parse_choice("default")
        assert result[0].choice_type == "default"

    def test_parse_choice_unknown_action(self):
        """Test parsing unknown action type (line 668)."""
        parser = ChoiceParser()
        result = parser.parse_choice("unknown arg1 arg2")
        assert result[0].choice_type == "pass"

    def test_parse_move_choice_empty_tokens(self):
        """Test _parse_move_choice with empty tokens (line 675)."""
        parser = ChoiceParser()
        result = parser.parse_choice("move")
        assert result[0].choice_type == "move"

    def test_parse_move_choice_invalid_target(self):
        """Test move choice with invalid target (lines 701-702, 707-708)."""
        parser = ChoiceParser()
        # With + prefix but invalid number
        result = parser.parse_choice("move 1 +invalid")
        assert result[0].choice_type == "move"
        assert result[0].move_slot == 1

    def test_parse_move_choice_mega(self):
        """Test move choice with mega flag."""
        parser = ChoiceParser()
        result = parser.parse_choice("move 1 mega")
        assert result[0].choice_type == "move"
        assert result[0].mega is True

    def test_parse_move_choice_zmove(self):
        """Test move choice with zmove flag."""
        parser = ChoiceParser()
        result = parser.parse_choice("move 1 zmove")
        assert result[0].choice_type == "move"
        assert result[0].zmove is True

    def test_parse_move_choice_max(self):
        """Test move choice with max/dynamax flag."""
        parser = ChoiceParser()
        result = parser.parse_choice("move 1 max")
        assert result[0].choice_type == "move"
        assert result[0].dynamax is True

    def test_parse_move_choice_terastallize(self):
        """Test move choice with terastallize flag."""
        parser = ChoiceParser()
        result = parser.parse_choice("move 1 terastallize")
        assert result[0].choice_type == "move"
        assert result[0].terastallize is True

    def test_parse_switch_choice_empty_tokens(self):
        """Test _parse_switch_choice with empty tokens (line 719)."""
        parser = ChoiceParser()
        result = parser.parse_choice("switch")
        assert result[0].choice_type == "switch"

    def test_parse_switch_choice_with_name(self):
        """Test switch choice with pokemon name (line 726)."""
        parser = ChoiceParser()
        result = parser.parse_choice("switch Pikachu")
        assert result[0].choice_type == "switch"
        assert result[0].switch_name == "Pikachu"

    def test_format_choice_default(self):
        """Test format_choice for default type (line 738)."""
        parser = ChoiceParser()
        choices = [Choice("default", slot=0)]
        result = parser.format_choice(choices)
        assert result == "default"

    def test_format_choice_move_with_target(self):
        """Test format_choice for move with target (lines 741-743)."""
        parser = ChoiceParser()
        choices = [Choice("move", slot=0, move_slot=1, target=2)]
        result = parser.format_choice(choices)
        assert "move 1" in result
        assert "+2" in result

    def test_format_choice_move_with_negative_target(self):
        """Test format_choice for move with negative target (ally)."""
        parser = ChoiceParser()
        choices = [Choice("move", slot=0, move_slot=1, target=-1)]
        result = parser.format_choice(choices)
        assert "move 1" in result
        assert "-1" in result

    def test_format_choice_move_with_mega(self):
        """Test format_choice for move with mega (line 745)."""
        parser = ChoiceParser()
        choices = [Choice("move", slot=0, move_slot=1, mega=True)]
        result = parser.format_choice(choices)
        assert "mega" in result

    def test_format_choice_move_with_zmove(self):
        """Test format_choice for move with zmove (line 747)."""
        parser = ChoiceParser()
        choices = [Choice("move", slot=0, move_slot=1, zmove=True)]
        result = parser.format_choice(choices)
        assert "zmove" in result

    def test_format_choice_move_with_dynamax(self):
        """Test format_choice for move with dynamax (line 749)."""
        parser = ChoiceParser()
        choices = [Choice("move", slot=0, move_slot=1, dynamax=True)]
        result = parser.format_choice(choices)
        assert "max" in result

    def test_format_choice_move_with_terastallize(self):
        """Test format_choice for move with terastallize (line 751)."""
        parser = ChoiceParser()
        choices = [Choice("move", slot=0, move_slot=1, terastallize=True)]
        result = parser.format_choice(choices)
        assert "terastallize" in result

    def test_format_choice_switch_with_name(self):
        """Test format_choice for switch with name."""
        parser = ChoiceParser()
        choices = [Choice("switch", slot=0, switch_name="Pikachu")]
        result = parser.format_choice(choices)
        assert "switch Pikachu" in result


class TestProtocolReplayer:
    """Tests for ProtocolReplayer to cover various handlers."""

    def test_handle_tie(self):
        """Test _handle_tie method (lines 1091-1092)."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|tie")
        assert state.winner == "tie"
        assert any(e.get("type") == "tie" for e in replayer.events)

    def test_handle_win(self):
        """Test _handle_win method."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|win|Player1")
        assert state.winner == "Player1"

    def test_handle_weather_none(self):
        """Test weather set to none."""
        replayer = ProtocolReplayer()
        # First set weather, then set to none
        state = replayer.replay("|-weather|Rain\n|-weather|none")
        assert state.weather is None

    def test_handle_fieldstart_terrain(self):
        """Test fieldstart with terrain."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|-fieldstart|move: Psychic Terrain")
        assert state.terrain == "psychic"

    def test_handle_fieldend_terrain(self):
        """Test fieldend clearing terrain."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|-fieldstart|move: Psychic Terrain\n|-fieldend|Psychic Terrain")
        assert state.terrain is None

    def test_handle_sidestart(self):
        """Test sidestart adding condition."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|-sidestart|p1: Player1|Reflect")
        assert "Reflect" in state.side_conditions.get("p1", [])

    def test_handle_sideend(self):
        """Test sideend removing condition."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|-sidestart|p1: Player1|Reflect\n|-sideend|p1: Player1|Reflect")
        assert "Reflect" not in state.side_conditions.get("p1", [])

    def test_handle_boost(self):
        """Test boost handler."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|-boost|p1a: Pikachu|atk|2")
        assert state.pokemon_boosts.get("p1a", {}).get("atk") == 2

    def test_handle_unboost(self):
        """Test unboost handler."""
        replayer = ProtocolReplayer()
        state = replayer.replay("|-boost|p1a: Pikachu|atk|2\n|-unboost|p1a: Pikachu|atk|1")
        assert state.pokemon_boosts["p1a"]["atk"] == 1
