"""Tests for Pokemon Showdown protocol implementation.

Tests cover:
- Protocol message parsing (SIM-PROTOCOL.md format)
- Protocol message emission
- Choice parsing and formatting
- Battle replay from protocol logs
"""
import pytest
from pathlib import Path

from parsers import (
    MessageType,
    ProtocolMessage,
    ProtocolParser,
    ProtocolEmitter,
    Choice,
    ChoiceParser,
    ReplayState,
    ProtocolReplayer,
)


# =============================================================================
# Protocol Parser Tests
# =============================================================================

class TestProtocolParser:
    """Tests for ProtocolParser."""

    @pytest.fixture
    def parser(self):
        return ProtocolParser()

    def test_parse_empty_line(self, parser):
        """Parse empty spacer line."""
        msg = parser.parse_line("|")
        assert msg.msg_type == MessageType.EMPTY

    def test_parse_player(self, parser):
        """Parse |player| message."""
        msg = parser.parse_line("|player|p1|Alice|60|1200")
        assert msg.msg_type == MessageType.PLAYER
        assert msg.args == ["p1", "Alice", "60", "1200"]

    def test_parse_teamsize(self, parser):
        """Parse |teamsize| message."""
        msg = parser.parse_line("|teamsize|p1|6")
        assert msg.msg_type == MessageType.TEAMSIZE
        assert msg.args == ["p1", "6"]

    def test_parse_gametype(self, parser):
        """Parse |gametype| message."""
        msg = parser.parse_line("|gametype|doubles")
        assert msg.msg_type == MessageType.GAMETYPE
        assert msg.args == ["doubles"]

    def test_parse_turn(self, parser):
        """Parse |turn| message."""
        msg = parser.parse_line("|turn|5")
        assert msg.msg_type == MessageType.TURN
        assert msg.args == ["5"]

    def test_parse_switch(self, parser):
        """Parse |switch| message."""
        msg = parser.parse_line("|switch|p1a: Pikachu|Pikachu, L50, M|100/100")
        assert msg.msg_type == MessageType.SWITCH
        assert msg.args == ["p1a: Pikachu", "Pikachu, L50, M", "100/100"]

    def test_parse_move(self, parser):
        """Parse |move| message."""
        msg = parser.parse_line("|move|p1a: Pikachu|Thunderbolt|p2a: Charizard")
        assert msg.msg_type == MessageType.MOVE
        assert msg.args == ["p1a: Pikachu", "Thunderbolt", "p2a: Charizard"]

    def test_parse_damage(self, parser):
        """Parse |-damage| message."""
        msg = parser.parse_line("|-damage|p2a: Charizard|75/100")
        assert msg.msg_type == MessageType.DAMAGE
        assert msg.args == ["p2a: Charizard", "75/100"]

    def test_parse_damage_with_source(self, parser):
        """Parse |-damage| with [from] tag."""
        msg = parser.parse_line("|-damage|p1a: Pikachu|90/100|[from] Stealth Rock")
        assert msg.msg_type == MessageType.DAMAGE
        assert msg.args == ["p1a: Pikachu", "90/100"]
        assert msg.kwargs["from"] == "Stealth Rock"

    def test_parse_damage_with_of(self, parser):
        """Parse |-damage| with [from] and [of] tags."""
        msg = parser.parse_line("|-damage|p1a: Pikachu|88/100|[from] Leech Seed|[of] p2a: Venusaur")
        assert msg.msg_type == MessageType.DAMAGE
        assert msg.kwargs["from"] == "Leech Seed"
        assert msg.kwargs["of"] == "p2a: Venusaur"

    def test_parse_boost(self, parser):
        """Parse |-boost| message."""
        msg = parser.parse_line("|-boost|p1a: Pikachu|spe|2")
        assert msg.msg_type == MessageType.BOOST
        assert msg.args == ["p1a: Pikachu", "spe", "2"]

    def test_parse_unboost(self, parser):
        """Parse |-unboost| message."""
        msg = parser.parse_line("|-unboost|p1a: Pikachu|atk|1")
        assert msg.msg_type == MessageType.UNBOOST
        assert msg.args == ["p1a: Pikachu", "atk", "1"]

    def test_parse_weather(self, parser):
        """Parse |-weather| message."""
        msg = parser.parse_line("|-weather|Sandstorm|[from] ability: Sand Stream|[of] p1a: Tyranitar")
        assert msg.msg_type == MessageType.WEATHER
        assert msg.args == ["Sandstorm"]
        assert msg.kwargs["from"] == "ability: Sand Stream"

    def test_parse_weather_upkeep(self, parser):
        """Parse |-weather| upkeep message."""
        msg = parser.parse_line("|-weather|Rain|[upkeep]")
        assert msg.msg_type == MessageType.WEATHER
        assert "upkeep" in msg.kwargs

    def test_parse_faint(self, parser):
        """Parse |faint| message."""
        msg = parser.parse_line("|faint|p2a: Charizard")
        assert msg.msg_type == MessageType.FAINT
        assert msg.args == ["p2a: Charizard"]

    def test_parse_win(self, parser):
        """Parse |win| message."""
        msg = parser.parse_line("|win|Alice")
        assert msg.msg_type == MessageType.WIN
        assert msg.args == ["Alice"]

    def test_parse_pokemon_id(self, parser):
        """Parse Pokemon ID strings."""
        player, slot, nickname = parser.parse_pokemon_id("p1a: Pikachu")
        assert player == "p1"
        assert slot == "a"
        assert nickname == "Pikachu"

    def test_parse_pokemon_id_no_nickname(self, parser):
        """Parse Pokemon ID without nickname."""
        player, slot, nickname = parser.parse_pokemon_id("p2b")
        assert player == "p2"
        assert slot == "b"
        assert nickname == ""

    def test_parse_details_full(self, parser):
        """Parse full details string."""
        details = parser.parse_details("Pikachu, L50, M, shiny, tera:Electric")
        assert details["species"] == "Pikachu"
        assert details["level"] == 50
        assert details["gender"] == "M"
        assert details["shiny"] is True
        assert details["tera_type"] == "Electric"

    def test_parse_details_minimal(self, parser):
        """Parse minimal details string."""
        details = parser.parse_details("Mewtwo")
        assert details["species"] == "Mewtwo"
        assert details["level"] == 100
        assert details["gender"] is None
        assert details["shiny"] is False

    def test_parse_hp_status_full(self, parser):
        """Parse HP and status."""
        current, max_hp, status = parser.parse_hp_status("75/100 psn")
        assert current == 75
        assert max_hp == 100
        assert status == "psn"

    def test_parse_hp_status_fainted(self, parser):
        """Parse fainted HP."""
        current, max_hp, status = parser.parse_hp_status("0 fnt")
        assert current == 0
        assert status == "fnt"

    def test_parse_hp_status_percent(self, parser):
        """Parse percentage HP."""
        current, max_hp, status = parser.parse_hp_status("50/100")
        assert current == 50
        assert max_hp == 100
        assert status is None

    def test_parse_hp_escaped_slash(self, parser):
        """Parse HP with escaped slash."""
        current, max_hp, status = parser.parse_hp_status("94\\/100")
        assert current == 94
        assert max_hp == 100


class TestProtocolParserLog:
    """Test parsing full battle logs."""

    @pytest.fixture
    def parser(self):
        return ProtocolParser()

    def test_parse_simple_log(self, parser):
        """Parse a simple battle log."""
        log = """|player|p1|Alice|60|
|player|p2|Bob|113|
|gametype|doubles
|gen|9
|turn|1
|move|p1a: Pikachu|Thunderbolt|p2a: Charizard
|-damage|p2a: Charizard|50/100
|turn|2"""

        messages = parser.parse_log(log)

        assert len(messages) == 8
        assert messages[0].msg_type == MessageType.PLAYER
        assert messages[4].msg_type == MessageType.TURN
        assert messages[4].args == ["1"]
        assert messages[5].msg_type == MessageType.MOVE
        assert messages[6].msg_type == MessageType.DAMAGE


# =============================================================================
# Protocol Emitter Tests
# =============================================================================

class TestProtocolEmitter:
    """Tests for ProtocolEmitter."""

    @pytest.fixture
    def emitter(self):
        return ProtocolEmitter()

    def test_emit_player(self, emitter):
        """Emit |player| message."""
        emitter.player("p1", "Alice", "60", 1200)
        assert emitter.messages[-1] == "|player|p1|Alice|60|1200"

    def test_emit_switch(self, emitter):
        """Emit |switch| message."""
        emitter.switch("p1a: Pikachu", "Pikachu, L50, M", "100/100")
        assert emitter.messages[-1] == "|switch|p1a: Pikachu|Pikachu, L50, M|100/100"

    def test_emit_move(self, emitter):
        """Emit |move| message."""
        emitter.move("p1a: Pikachu", "Thunderbolt", "p2a: Charizard")
        assert emitter.messages[-1] == "|move|p1a: Pikachu|Thunderbolt|p2a: Charizard"

    def test_emit_move_spread(self, emitter):
        """Emit |move| with spread tag."""
        emitter.move("p1a: Garchomp", "Earthquake", "p2a: Pikachu", spread=True)
        assert "[spread]" in emitter.messages[-1]

    def test_emit_damage(self, emitter):
        """Emit |-damage| message."""
        emitter.damage("p2a: Charizard", "50/100")
        assert emitter.messages[-1] == "|-damage|p2a: Charizard|50/100"

    def test_emit_damage_with_source(self, emitter):
        """Emit |-damage| with source."""
        emitter.damage("p1a: Pikachu", "90/100", source="Stealth Rock")
        assert emitter.messages[-1] == "|-damage|p1a: Pikachu|90/100|[from] Stealth Rock"

    def test_emit_boost(self, emitter):
        """Emit |-boost| message."""
        emitter.boost("p1a: Pikachu", "spe", 2)
        assert emitter.messages[-1] == "|-boost|p1a: Pikachu|spe|2"

    def test_emit_weather(self, emitter):
        """Emit |-weather| message."""
        emitter.weather("Sandstorm", source="ability: Sand Stream")
        assert "|-weather|Sandstorm" in emitter.messages[-1]
        assert "[from] ability: Sand Stream" in emitter.messages[-1]

    def test_emit_weather_upkeep(self, emitter):
        """Emit |-weather| upkeep message."""
        emitter.weather("Rain", upkeep=True)
        assert emitter.messages[-1] == "|-weather|Rain|[upkeep]"

    def test_emit_faint(self, emitter):
        """Emit |faint| message."""
        emitter.faint("p2a: Charizard")
        assert emitter.messages[-1] == "|faint|p2a: Charizard"

    def test_emit_win(self, emitter):
        """Emit |win| message."""
        emitter.win("Alice")
        assert emitter.messages[-1] == "|win|Alice"

    def test_emit_turn(self, emitter):
        """Emit |turn| message."""
        emitter.turn(5)
        assert emitter.messages[-1] == "|turn|5"

    def test_emit_supereffective(self, emitter):
        """Emit |-supereffective| message."""
        emitter.supereffective("p2a: Charizard")
        assert emitter.messages[-1] == "|-supereffective|p2a: Charizard"

    def test_emit_sidestart(self, emitter):
        """Emit |-sidestart| message."""
        emitter.sidestart("p1: Alice", "move: Reflect")
        assert emitter.messages[-1] == "|-sidestart|p1: Alice|move: Reflect"

    def test_emit_full_battle(self, emitter):
        """Emit a full battle sequence."""
        emitter.player("p1", "Alice", "60", 1200)
        emitter.player("p2", "Bob", "113", 1100)
        emitter.gametype("doubles")
        emitter.gen(9)
        emitter.start()
        emitter.switch("p1a: Pikachu", "Pikachu, L50, M", "100/100")
        emitter.switch("p2a: Charizard", "Charizard, L50, M", "100/100")
        emitter.turn(1)
        emitter.move("p1a: Pikachu", "Thunderbolt", "p2a: Charizard")
        emitter.supereffective("p2a: Charizard")
        emitter.damage("p2a: Charizard", "0 fnt")
        emitter.faint("p2a: Charizard")
        emitter.win("Alice")

        output = emitter.get_output()
        assert "|player|p1|Alice" in output
        assert "|switch|p1a: Pikachu" in output
        assert "|move|p1a: Pikachu|Thunderbolt" in output
        assert "|win|Alice" in output


# =============================================================================
# Choice Parser Tests
# =============================================================================

class TestChoiceParser:
    """Tests for ChoiceParser."""

    @pytest.fixture
    def parser(self):
        return ChoiceParser()

    def test_parse_move_by_slot(self, parser):
        """Parse move choice by slot number."""
        choices = parser.parse_choice("move 1")
        assert len(choices) == 1
        assert choices[0].choice_type == "move"
        assert choices[0].move_slot == 1

    def test_parse_move_by_name(self, parser):
        """Parse move choice by name."""
        choices = parser.parse_choice("move Thunderbolt")
        assert choices[0].move_name == "Thunderbolt"

    def test_parse_move_with_target(self, parser):
        """Parse move choice with target."""
        choices = parser.parse_choice("move 1 +2")
        assert choices[0].target == 2

    def test_parse_move_with_negative_target(self, parser):
        """Parse move choice targeting ally."""
        choices = parser.parse_choice("move 1 -1")
        assert choices[0].target == -1

    def test_parse_move_mega(self, parser):
        """Parse mega evolution move."""
        choices = parser.parse_choice("move 1 mega")
        assert choices[0].mega is True

    def test_parse_move_zmove(self, parser):
        """Parse Z-move."""
        choices = parser.parse_choice("move 1 zmove")
        assert choices[0].zmove is True

    def test_parse_move_dynamax(self, parser):
        """Parse Dynamax move."""
        choices = parser.parse_choice("move 1 max")
        assert choices[0].dynamax is True

    def test_parse_switch_by_slot(self, parser):
        """Parse switch choice by slot."""
        choices = parser.parse_choice("switch 3")
        assert choices[0].choice_type == "switch"
        assert choices[0].switch_to == 3

    def test_parse_switch_by_name(self, parser):
        """Parse switch choice by name."""
        choices = parser.parse_choice("switch Pikachu")
        assert choices[0].switch_name == "Pikachu"

    def test_parse_pass(self, parser):
        """Parse pass choice."""
        choices = parser.parse_choice("pass")
        assert choices[0].choice_type == "pass"

    def test_parse_default(self, parser):
        """Parse default choice."""
        choices = parser.parse_choice("default")
        assert choices[0].choice_type == "default"

    def test_parse_doubles_choice(self, parser):
        """Parse doubles choice with comma separator."""
        choices = parser.parse_choice("move 1 +2, switch 3")
        assert len(choices) == 2
        assert choices[0].choice_type == "move"
        assert choices[0].target == 2
        assert choices[1].choice_type == "switch"
        assert choices[1].switch_to == 3

    def test_parse_doubles_with_pass(self, parser):
        """Parse doubles choice with pass."""
        choices = parser.parse_choice("move 1, pass")
        assert len(choices) == 2
        assert choices[1].choice_type == "pass"

    def test_format_move_choice(self, parser):
        """Format move choice back to string."""
        choices = [Choice("move", slot=0, move_slot=1, target=2)]
        formatted = parser.format_choice(choices)
        assert formatted == "move 1 +2"

    def test_format_switch_choice(self, parser):
        """Format switch choice back to string."""
        choices = [Choice("switch", slot=0, switch_to=3)]
        formatted = parser.format_choice(choices)
        assert formatted == "switch 3"

    def test_format_doubles_choice(self, parser):
        """Format doubles choice."""
        choices = [
            Choice("move", slot=0, move_slot=1, target=2),
            Choice("switch", slot=1, switch_to=3),
        ]
        formatted = parser.format_choice(choices)
        assert formatted == "move 1 +2, switch 3"


# =============================================================================
# Protocol Replayer Tests
# =============================================================================

class TestProtocolReplayer:
    """Tests for ProtocolReplayer."""

    @pytest.fixture
    def replayer(self):
        return ProtocolReplayer()

    def test_replay_simple_battle(self, replayer):
        """Replay a simple battle."""
        log = """|player|p1|Alice|60|
|player|p2|Bob|113|
|gametype|doubles
|gen|9
|switch|p1a: Pikachu|Pikachu, L50, M|100/100
|switch|p2a: Charizard|Charizard, L50, M|100/100
|turn|1
|move|p1a: Pikachu|Thunderbolt|p2a: Charizard
|-supereffective|p2a: Charizard
|-damage|p2a: Charizard|0 fnt
|faint|p2a: Charizard
|win|Alice"""

        state = replayer.replay(log)

        assert state.turn == 1
        assert state.winner == "Alice"
        assert state.pokemon_hp["p2a"] == (0, 100)

    def test_replay_tracks_hp(self, replayer):
        """Replay tracks HP changes."""
        log = """|switch|p1a: Pikachu|Pikachu, L50, M|100/100
|switch|p2a: Charizard|Charizard, L50, M|100/100
|turn|1
|-damage|p2a: Charizard|75/100
|turn|2
|-damage|p2a: Charizard|50/100"""

        state = replayer.replay(log)

        assert state.pokemon_hp["p2a"] == (50, 100)

    def test_replay_tracks_boosts(self, replayer):
        """Replay tracks stat boosts."""
        log = """|switch|p1a: Pikachu|Pikachu, L50, M|100/100
|turn|1
|-boost|p1a: Pikachu|spe|2
|turn|2
|-unboost|p1a: Pikachu|spe|1"""

        state = replayer.replay(log)

        assert state.pokemon_boosts["p1a"]["spe"] == 1

    def test_replay_tracks_weather(self, replayer):
        """Replay tracks weather."""
        log = """|switch|p1a: Tyranitar|Tyranitar, L50, M|100/100
|-weather|Sandstorm|[from] ability: Sand Stream
|turn|1
|-weather|Sandstorm|[upkeep]
|turn|2
|-weather|none"""

        state = replayer.replay(log)

        assert state.weather is None

    def test_replay_tracks_status(self, replayer):
        """Replay tracks status conditions."""
        log = """|switch|p1a: Pikachu|Pikachu, L50, M|100/100
|turn|1
|-status|p1a: Pikachu|par
|turn|2
|-curestatus|p1a: Pikachu|par"""

        state = replayer.replay(log)

        assert state.pokemon_status["p1a"] is None

    def test_replay_events_list(self, replayer):
        """Replay builds events list."""
        log = """|switch|p1a: Pikachu|Pikachu, L50, M|100/100
|turn|1
|move|p1a: Pikachu|Thunderbolt|p2a: Charizard
|-damage|p2a: Charizard|50/100"""

        replayer.replay(log)

        # Check events were recorded
        move_events = [e for e in replayer.events if e["type"] == "move"]
        assert len(move_events) == 1
        assert move_events[0]["move"] == "Thunderbolt"


# =============================================================================
# Integration Test with Real Battle Log
# =============================================================================

class TestProtocolWithRealLog:
    """Test protocol parsing with real battle log."""

    LOG_FILE = "doc/logs/gen9vgc2025regi-2390379047.log"

    @pytest.fixture
    def log_content(self):
        path = Path(self.LOG_FILE)
        if path.exists():
            return path.read_text()
        return None

    def test_parse_real_log(self, log_content):
        """Parse real battle log file."""
        if log_content is None:
            pytest.skip("Log file not found")

        parser = ProtocolParser()
        messages = parser.parse_log(log_content)

        # Should have many messages
        assert len(messages) > 50

        # Check for expected message types
        msg_types = {m.msg_type for m in messages}
        assert MessageType.PLAYER in msg_types
        assert MessageType.SWITCH in msg_types
        assert MessageType.MOVE in msg_types
        assert MessageType.DAMAGE in msg_types
        assert MessageType.WIN in msg_types

    def test_replay_real_log(self, log_content):
        """Replay real battle log."""
        if log_content is None:
            pytest.skip("Log file not found")

        replayer = ProtocolReplayer()
        state = replayer.replay(log_content)

        # Should have a winner
        assert state.winner == "K1ngzzz"

        # Should have processed multiple turns
        assert state.turn >= 7

        # Should have tracked HP for active Pokemon
        assert len(state.pokemon_hp) > 0

    def test_extract_damage_from_real_log(self, log_content):
        """Extract damage events from real log."""
        if log_content is None:
            pytest.skip("Log file not found")

        replayer = ProtocolReplayer()
        replayer.replay(log_content)

        damage_events = [e for e in replayer.events if e["type"] == "damage"]

        # Should have multiple damage events
        assert len(damage_events) > 10

        # First damage should be Froslass OHKO
        first_ko = [e for e in damage_events if e["hp_after"] == 0]
        assert len(first_ko) >= 1

    def test_extract_moves_from_real_log(self, log_content):
        """Extract move events from real log."""
        if log_content is None:
            pytest.skip("Log file not found")

        replayer = ProtocolReplayer()
        replayer.replay(log_content)

        move_events = [e for e in replayer.events if e["type"] == "move"]

        # Should have many moves
        assert len(move_events) > 15

        # Should have specific moves from the battle
        move_names = [e["move"] for e in move_events]
        assert "Helping Hand" in move_names
        assert "Moongeist Beam" in move_names
        assert "Aurora Veil" in move_names


# =============================================================================
# Round-trip Tests
# =============================================================================

class TestProtocolRoundTrip:
    """Test that emitted protocol can be parsed back."""

    def test_roundtrip_switch(self):
        """Round-trip switch message."""
        emitter = ProtocolEmitter()
        emitter.switch("p1a: Pikachu", "Pikachu, L50, M", "100/100")

        parser = ProtocolParser()
        msg = parser.parse_line(emitter.messages[0])

        assert msg.msg_type == MessageType.SWITCH
        assert msg.args[0] == "p1a: Pikachu"

    def test_roundtrip_damage(self):
        """Round-trip damage message."""
        emitter = ProtocolEmitter()
        emitter.damage("p2a: Charizard", "75/100", source="Thunderbolt")

        parser = ProtocolParser()
        msg = parser.parse_line(emitter.messages[0])

        assert msg.msg_type == MessageType.DAMAGE
        assert msg.kwargs["from"] == "Thunderbolt"

    def test_roundtrip_weather(self):
        """Round-trip weather message."""
        emitter = ProtocolEmitter()
        emitter.weather("Sandstorm", source="ability: Sand Stream")

        parser = ProtocolParser()
        msg = parser.parse_line(emitter.messages[0])

        assert msg.msg_type == MessageType.WEATHER
        assert msg.args[0] == "Sandstorm"
        assert "Sand Stream" in msg.kwargs.get("from", "")

    def test_roundtrip_full_battle(self):
        """Round-trip full battle."""
        emitter = ProtocolEmitter()
        emitter.player("p1", "Alice", "60")
        emitter.player("p2", "Bob", "113")
        emitter.gametype("doubles")
        emitter.gen(9)
        emitter.switch("p1a: Pikachu", "Pikachu, L50, M", "100/100")
        emitter.switch("p2a: Charizard", "Charizard, L50, M", "100/100")
        emitter.turn(1)
        emitter.move("p1a: Pikachu", "Thunderbolt", "p2a: Charizard")
        emitter.damage("p2a: Charizard", "0 fnt")
        emitter.faint("p2a: Charizard")
        emitter.win("Alice")

        # Parse back
        parser = ProtocolParser()
        messages = parser.parse_log(emitter.get_output())

        # Replay
        replayer = ProtocolReplayer()
        for msg in messages:
            replayer._process_message(msg)

        assert replayer.state.winner == "Alice"
        assert replayer.state.pokemon_hp["p2a"] == (0, 100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
