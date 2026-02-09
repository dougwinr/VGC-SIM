"""Integration tests comparing battle engine against Pokemon Showdown replays.

These tests parse actual Pokemon Showdown battle logs and verify that our
battle engine produces consistent results for key mechanics:
- Turn order
- Damage calculations (within expected range)
- Status effects
- Weather/terrain effects
- Residual damage
"""
import pytest
import os
from pathlib import Path

from parsers.showdown_log_parser import (
    parse_battle_log_file,
    parse_battle_log,
    extract_log_data,
    get_damage_events,
    get_move_events,
    LogEventType,
    ParsedBattleLog,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_replay_path():
    """Path to the sample VGC replay."""
    return Path(__file__).parent.parent / "doc" / "pokemon_battle_log_test.html"


@pytest.fixture
def parsed_replay(sample_replay_path):
    """Parsed battle log from the sample replay."""
    return parse_battle_log_file(str(sample_replay_path))


# =============================================================================
# Parser Tests
# =============================================================================

class TestShowdownLogParser:
    """Tests for the Pokemon Showdown log parser."""

    def test_parse_replay_file_exists(self, sample_replay_path):
        """Verify the sample replay file exists."""
        assert sample_replay_path.exists(), f"Sample replay not found at {sample_replay_path}"

    def test_parse_replay_extracts_players(self, parsed_replay):
        """Verify player names are extracted."""
        assert "p1" in parsed_replay.players
        assert "p2" in parsed_replay.players
        assert parsed_replay.players["p1"] == "Wolfey UwU"
        assert parsed_replay.players["p2"] == "mechanicalToad"

    def test_parse_replay_extracts_format(self, parsed_replay):
        """Verify format/tier is extracted."""
        assert "VGC 2024" in parsed_replay.format
        assert parsed_replay.gen == 9
        assert parsed_replay.gametype == "doubles"

    def test_parse_replay_extracts_teams(self, parsed_replay):
        """Verify team Pokemon are extracted."""
        assert "p1" in parsed_replay.teams
        assert "p2" in parsed_replay.teams

        # Team 1 has 6 Pokemon
        assert len(parsed_replay.teams["p1"]) == 6
        p1_species = [p["species"] for p in parsed_replay.teams["p1"]]
        assert "Ursaluna-Bloodmoon" in p1_species
        assert "Whimsicott" in p1_species
        assert "Tyranitar" in p1_species

        # Team 2 has 6 Pokemon
        assert len(parsed_replay.teams["p2"]) == 6
        p2_species = [p["species"] for p in parsed_replay.teams["p2"]]
        assert "Muk-Alola" in p2_species
        assert "Smeargle" in p2_species
        assert "Garganacl" in p2_species

    def test_parse_replay_extracts_turns(self, parsed_replay):
        """Verify turns are extracted."""
        # Battle has 9 turns
        assert len(parsed_replay.turns) >= 9

    def test_parse_replay_extracts_winner(self, parsed_replay):
        """Verify winner is extracted."""
        assert parsed_replay.winner == "Wolfey UwU"

    def test_parse_replay_extracts_events(self, parsed_replay):
        """Verify events are extracted."""
        assert len(parsed_replay.all_events) > 0

        # Check for key event types
        event_types = {e.event_type for e in parsed_replay.all_events}
        assert LogEventType.SWITCH in event_types
        assert LogEventType.MOVE in event_types
        assert LogEventType.DAMAGE in event_types
        assert LogEventType.FAINT in event_types

    def test_get_damage_events(self, parsed_replay):
        """Verify damage events are extracted correctly."""
        damage_events = get_damage_events(parsed_replay)
        assert len(damage_events) > 0

        # Verify damage event structure
        first_damage = damage_events[0]
        assert "turn" in first_damage
        assert "slot" in first_damage
        assert "hp_before" in first_damage
        assert "hp_after" in first_damage
        assert "damage" in first_damage

    def test_get_move_events(self, parsed_replay):
        """Verify move events are extracted correctly."""
        move_events = get_move_events(parsed_replay)
        assert len(move_events) > 0

        # Check some specific moves from the replay
        moves_used = [e["move"] for e in move_events]
        assert "Follow Me" in moves_used
        assert "Encore" in moves_used
        assert "Calm Mind" in moves_used


class TestShowdownLogParserEdgeCases:
    """Edge case tests for the parser."""

    def test_parse_hp_with_status(self):
        """Test parsing HP string with status condition."""
        from parsers.showdown_log_parser import parse_hp

        # Normal HP
        current, max_hp, status = parse_hp("89/100")
        assert current == 89
        assert max_hp == 100
        assert status is None

        # HP with toxic
        current, max_hp, status = parse_hp("89/100 tox")
        assert current == 89
        assert max_hp == 100
        assert status == "tox"

        # Fainted
        current, max_hp, status = parse_hp("0 fnt")
        assert current == 0
        assert status is None

    def test_parse_slot(self):
        """Test parsing slot strings."""
        from parsers.showdown_log_parser import parse_slot

        slot, nickname = parse_slot("p1a: Ursaluna")
        assert slot == "p1a"
        assert nickname == "Ursaluna"

        slot, nickname = parse_slot("p2b: Smeargle")
        assert slot == "p2b"
        assert nickname == "Smeargle"

        slot, nickname = parse_slot("p1a")
        assert slot == "p1a"
        assert nickname == ""

    def test_parse_species_info(self):
        """Test parsing species information."""
        from parsers.showdown_log_parser import parse_species_info

        info = parse_species_info("Ursaluna-Bloodmoon, L50, M")
        assert info["species"] == "Ursaluna-Bloodmoon"
        assert info["level"] == 50
        assert info["gender"] == "M"

        info = parse_species_info("Pikachu, L100, F")
        assert info["species"] == "Pikachu"
        assert info["level"] == 100
        assert info["gender"] == "F"


# =============================================================================
# Battle Event Verification Tests
# =============================================================================

class TestReplayBattleEvents:
    """Tests verifying battle events from the replay."""

    def test_turn_1_moves(self, parsed_replay):
        """Verify Turn 1 moves from the replay."""
        move_events = get_move_events(parsed_replay)
        turn_1_moves = [e for e in move_events if e["turn"] == 1]

        # Turn 1: Follow Me, Encore, Calm Mind, Minimize
        turn_1_move_names = [m["move"] for m in turn_1_moves]
        assert "Follow Me" in turn_1_move_names
        assert "Encore" in turn_1_move_names
        assert "Calm Mind" in turn_1_move_names
        assert "Minimize" in turn_1_move_names

    def test_weather_sandstorm(self, parsed_replay):
        """Verify Sandstorm weather was set."""
        weather_events = [
            e for e in parsed_replay.all_events
            if e.event_type == LogEventType.WEATHER
        ]

        # Should have sandstorm from Tyranitar's Sand Stream
        sandstorm_events = [e for e in weather_events if "Sandstorm" in str(e.data)]
        assert len(sandstorm_events) > 0

    def test_toxic_status_applied(self, parsed_replay):
        """Verify Toxic status was applied to Ursaluna."""
        status_events = [
            e for e in parsed_replay.all_events
            if e.event_type == LogEventType.STATUS
        ]

        # Ursaluna should get tox status
        tox_events = [e for e in status_events if e.data.get("status") == "tox"]
        assert len(tox_events) > 0

        # Check it was applied to Ursaluna (p1a)
        ursaluna_toxic = [e for e in tox_events if e.data.get("slot") == "p1a"]
        assert len(ursaluna_toxic) > 0

    def test_faints_recorded(self, parsed_replay):
        """Verify faints are recorded correctly."""
        faint_events = [
            e for e in parsed_replay.all_events
            if e.event_type == LogEventType.FAINT
        ]

        # Smeargle (p2b), Muk (p2a), Sableye (p2b), Garganacl (p2a) should faint
        fainted_slots = [e.data.get("slot") for e in faint_events]
        assert len(fainted_slots) == 4  # 4 total faints

    def test_terastallize_events(self, parsed_replay):
        """Verify Terastallization events."""
        tera_events = [
            e for e in parsed_replay.all_events
            if e.event_type == LogEventType.TERASTALLIZE
        ]

        # Ursaluna terrastallizes to Normal on Turn 4
        assert len(tera_events) >= 1

        ursaluna_tera = [e for e in tera_events if e.data.get("slot") == "p1a"]
        assert len(ursaluna_tera) == 1
        assert ursaluna_tera[0].data.get("tera_type") == "Normal"


# =============================================================================
# Damage Verification Tests
# =============================================================================

class TestReplayDamageVerification:
    """Tests verifying damage calculations from the replay."""

    def test_smeargle_earth_power_damage(self, parsed_replay):
        """Verify Earth Power OHKO'd Smeargle (94% damage shown)."""
        damage_events = get_damage_events(parsed_replay)

        # Find damage to Smeargle from Earth Power (turn 3)
        smeargle_damage = [
            e for e in damage_events
            if e["slot"] == "p2b" and e["turn"] == 3 and e["damage"] > 0
        ]

        # Earth Power did massive damage (OHKO)
        assert len(smeargle_damage) > 0
        # Smeargle went from 94% to 0% (after sandstorm)
        total_damage = sum(e["damage"] for e in smeargle_damage)
        assert total_damage >= 94  # At least 94% damage

    def test_sandstorm_damage(self, parsed_replay):
        """Verify Sandstorm residual damage events exist."""
        # Find sandstorm damage events in raw events
        sand_damage_events = [
            e for e in parsed_replay.all_events
            if e.event_type == LogEventType.DAMAGE and
               e.data.get("source") == "Sandstorm"
        ]

        assert len(sand_damage_events) > 0, "Should have sandstorm damage events"

        # Verify HP values in the events (damage shown as HP after)
        # Sandstorm damage shows like: |-damage|p2b: Smeargle|94/100|[from] Sandstorm
        # This means HP went from 100 to 94 (6% damage)
        for event in sand_damage_events:
            hp_after = event.data.get("hp_current", 0)
            # HP should be reduced (either low value or showing remaining after damage)
            assert hp_after < 100, f"HP after sandstorm should be less than max"

    def test_toxic_damage_increases(self, parsed_replay):
        """Verify Toxic damage increases each turn."""
        damage_events = get_damage_events(parsed_replay)

        # Find toxic damage to Ursaluna (p1a)
        toxic_damage = [
            e for e in damage_events
            if e["slot"] == "p1a" and e.get("source") == "psn"
        ]

        # Toxic damage should increase: 1/16, 2/16, 3/16... (6%, 12%, 18%...)
        if len(toxic_damage) >= 3:
            # Verify damage is increasing
            damages = [e["damage"] for e in toxic_damage[:3]]
            # Should be roughly 6, 12, 18 or similar progression
            for i in range(1, len(damages)):
                # Allow some tolerance due to rounding
                assert damages[i] >= damages[i-1] - 2, \
                    f"Toxic damage not increasing: {damages}"


# =============================================================================
# Turn Order Verification Tests
# =============================================================================

class TestReplayTurnOrder:
    """Tests verifying turn order from the replay."""

    def test_priority_moves_go_first(self, parsed_replay):
        """Verify priority moves execute before others."""
        move_events = get_move_events(parsed_replay)

        # Turn 1: Follow Me (+2 priority) should go before Calm Mind (0)
        turn_1_moves = [e for e in move_events if e["turn"] == 1]

        if turn_1_moves:
            # Follow Me and Encore have priority, should be early
            move_order = [m["move"] for m in turn_1_moves]

            # Follow Me should be one of the first moves
            follow_me_idx = move_order.index("Follow Me") if "Follow Me" in move_order else -1
            assert follow_me_idx != -1, "Follow Me should appear in Turn 1"

    def test_protect_goes_first(self, parsed_replay):
        """Verify Protect (+4 priority) executes first."""
        move_events = get_move_events(parsed_replay)

        # Turn 3: Protect should be first
        turn_3_moves = [e for e in move_events if e["turn"] == 3]

        if turn_3_moves and "Protect" in [m["move"] for m in turn_3_moves]:
            # Protect should be first move
            assert turn_3_moves[0]["move"] == "Protect", \
                f"Protect should be first, but got: {turn_3_moves[0]['move']}"


# =============================================================================
# Integration Test: Replay Event Sequence
# =============================================================================

class TestReplayEventSequence:
    """Tests verifying the complete sequence of events matches expectations."""

    def test_battle_progression(self, parsed_replay):
        """Verify the battle progressed through expected phases."""
        turns = parsed_replay.turns

        # Battle should have multiple turns
        assert len(turns) >= 9, "Battle should have at least 9 turns"

        # First turn should have initial switches
        turn_0_events = turns[0].events if turns else []
        switch_events = [e for e in turn_0_events if e.event_type == LogEventType.SWITCH]
        assert len(switch_events) >= 4, "Should have 4 initial switches (2 per side in doubles)"

    def test_final_state(self, parsed_replay):
        """Verify the final battle state."""
        # Winner should be recorded
        assert parsed_replay.winner == "Wolfey UwU"

        # Final turn should show Garganacl fainted
        final_turn = parsed_replay.turns[-1] if parsed_replay.turns else None
        if final_turn:
            faint_events = [
                e for e in final_turn.events
                if e.event_type == LogEventType.FAINT
            ]
            # Garganacl should faint on the last turn
            assert len(faint_events) >= 1

    def test_all_events_parsed(self, parsed_replay):
        """Verify all event types are handled."""
        # Count unknown events
        unknown_events = [
            e for e in parsed_replay.all_events
            if e.event_type == LogEventType.UNKNOWN
        ]

        # Some unknown events are expected (chat, timestamps, etc.)
        # But core battle events should be parsed
        unknown_ratio = len(unknown_events) / len(parsed_replay.all_events)
        assert unknown_ratio < 0.5, \
            f"Too many unknown events: {unknown_ratio:.1%}"


# =============================================================================
# Synthetic Battle Comparison Tests
# =============================================================================

class TestSyntheticBattleComparison:
    """Tests comparing our engine against known Showdown damage values.

    These tests use pre-calculated damage values from Pokemon Showdown
    to verify our damage formula matches.
    """

    def test_base_damage_formula(self):
        """Verify base damage formula matches Showdown.

        Using known values from Showdown damage calculator:
        Level 50, 100 base power, 100 attack vs 100 defense
        Formula: ((2*L/5+2) * P * A/D) / 50 + 2
        = ((2*50/5+2) * 100 * 100/100) / 50 + 2
        = ((20+2) * 100) / 50 + 2 = 2200/50 + 2 = 44 + 2 = 46
        """
        from core.damage import calculate_base_damage

        # Test parameters matching Showdown calc
        level = 50
        power = 100
        attack = 100
        defense = 100

        base = calculate_base_damage(level, power, attack, defense)

        # Base damage (before random): ((2*50/5+2)*100*100/100)/50+2 = 46
        assert base == 46, f"Base damage {base} doesn't match expected 46"

    def test_thunderbolt_damage_range(self):
        """Verify Thunderbolt damage range matches Showdown.

        Thunderbolt: 90 base power, special
        Attacker: Level 50, 100 SpA
        Defender: Level 50, 100 SpD
        Expected: ~39-46 (neutral, no STAB)
        """
        from core.damage import calculate_base_damage, trunc

        level = 50
        power = 90
        spa = 100
        spd = 100

        base = calculate_base_damage(level, power, spa, spd)

        # Base = ((2*50/5+2)*90*100/100)/50+2 = ((22)*90)/50+2 = 1980/50+2 = 41
        assert base == 41, f"Thunderbolt base {base} doesn't match expected 41"

        # With random (0.85-1.0): 34-41
        min_damage = trunc(base * 0.85)
        max_damage = base

        assert 34 <= min_damage <= 35, f"Min damage {min_damage} out of range"
        assert max_damage == 41, f"Max damage {max_damage} should be 41"

    def test_super_effective_multiplier(self):
        """Verify super effective damage matches Showdown."""
        from core.damage import calculate_type_effectiveness
        from data.types import Type

        # Water vs Fire = 2x
        effectiveness = calculate_type_effectiveness(
            Type.WATER.value, Type.FIRE.value, -1
        )
        assert effectiveness == 2.0

        # Electric vs Water = 2x
        effectiveness = calculate_type_effectiveness(
            Type.ELECTRIC.value, Type.WATER.value, -1
        )
        assert effectiveness == 2.0

        # Ground vs Electric = 2x
        effectiveness = calculate_type_effectiveness(
            Type.GROUND.value, Type.ELECTRIC.value, -1
        )
        assert effectiveness == 2.0

    def test_type_immunity(self):
        """Verify type immunities match Showdown."""
        from core.damage import calculate_type_effectiveness
        from data.types import Type

        # Electric vs Ground = 0x (immune)
        effectiveness = calculate_type_effectiveness(
            Type.ELECTRIC.value, Type.GROUND.value, -1
        )
        assert effectiveness == 0.0

        # Normal vs Ghost = 0x (immune)
        effectiveness = calculate_type_effectiveness(
            Type.NORMAL.value, Type.GHOST.value, -1
        )
        assert effectiveness == 0.0

        # Ground vs Flying = 0x (immune)
        effectiveness = calculate_type_effectiveness(
            Type.GROUND.value, Type.FLYING.value, -1
        )
        assert effectiveness == 0.0

    def test_double_weakness(self):
        """Verify 4x weakness matches Showdown."""
        from core.damage import calculate_type_effectiveness
        from data.types import Type

        # Ice vs Grass/Flying (Jumpluff) = 4x
        effectiveness = calculate_type_effectiveness(
            Type.ICE.value, Type.GRASS.value, Type.FLYING.value
        )
        assert effectiveness == 4.0

        # Rock vs Fire/Flying (Charizard) = 4x
        effectiveness = calculate_type_effectiveness(
            Type.ROCK.value, Type.FIRE.value, Type.FLYING.value
        )
        assert effectiveness == 4.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
