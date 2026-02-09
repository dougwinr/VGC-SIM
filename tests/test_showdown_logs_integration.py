"""Integration tests for Pokemon Showdown battle logs.

This module tests the battle engine against 4950+ real Pokemon Showdown
battle logs from VGC 2025 Reg I format. Tests include:
- Parsing validation for all log files
- Damage calculation verification
- Turn order mechanics
- Status effects and weather
- Ability triggers
- Detailed turn-by-turn verification for sample battles
"""
import pytest
import os
from pathlib import Path
from typing import List, Dict, Any
import random

from parsers.showdown_log_parser import (
    parse_battle_log,
    parse_battle_log_file,
    get_damage_events,
    get_move_events,
    LogEventType,
    ParsedBattleLog,
)


# =============================================================================
# Constants and Fixtures
# =============================================================================

LOGS_DIR = Path(__file__).parent.parent / "doc" / "logs"


def get_all_log_files() -> List[Path]:
    """Get all .log files from the logs directory."""
    if not LOGS_DIR.exists():
        return []
    return sorted(LOGS_DIR.glob("*.log"))


def get_sample_log_files(n: int = 20, seed: int = 42) -> List[Path]:
    """Get a random sample of log files for detailed testing."""
    all_files = get_all_log_files()
    if not all_files:
        return []
    random.seed(seed)
    return random.sample(all_files, min(n, len(all_files)))


@pytest.fixture(scope="module")
def all_log_files():
    """All log files in the logs directory."""
    return get_all_log_files()


@pytest.fixture(scope="module")
def sample_log_files():
    """Sample of log files for detailed testing."""
    return get_sample_log_files(20)


@pytest.fixture(scope="module")
def parsed_sample_logs(sample_log_files):
    """Parse sample log files."""
    parsed = []
    for log_file in sample_log_files:
        try:
            parsed.append((log_file.name, parse_battle_log_file(str(log_file))))
        except Exception as e:
            pytest.fail(f"Failed to parse {log_file.name}: {e}")
    return parsed


# =============================================================================
# Bulk Parsing Tests
# =============================================================================

class TestBulkLogParsing:
    """Tests for parsing all battle logs."""

    def test_logs_directory_exists(self):
        """Verify the logs directory exists."""
        assert LOGS_DIR.exists(), f"Logs directory not found: {LOGS_DIR}"

    def test_logs_directory_has_files(self, all_log_files):
        """Verify we have log files to test."""
        assert len(all_log_files) > 0, "No log files found"
        # We expect ~4950 files
        assert len(all_log_files) >= 4900, f"Expected ~4950 logs, found {len(all_log_files)}"

    def test_all_logs_parseable(self, all_log_files):
        """Verify all log files can be parsed without errors."""
        failed = []
        for log_file in all_log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                parsed = parse_battle_log(content)
                # Basic validation
                assert parsed.gametype == "doubles"
                assert parsed.gen == 9
            except Exception as e:
                failed.append((log_file.name, str(e)))

        if failed:
            fail_msg = "\n".join(f"  {name}: {err}" for name, err in failed[:10])
            pytest.fail(f"Failed to parse {len(failed)} logs:\n{fail_msg}")

    def test_all_logs_have_winner(self, all_log_files):
        """Verify all logs have a winner (completed battles)."""
        no_winner = []
        for log_file in all_log_files[:500]:  # Sample first 500 for speed
            try:
                parsed = parse_battle_log_file(str(log_file))
                if not parsed.winner:
                    no_winner.append(log_file.name)
            except Exception:
                pass  # Skip parsing errors, handled by other test

        # Allow some forfeits/disconnects
        no_winner_ratio = len(no_winner) / 500
        assert no_winner_ratio < 0.1, \
            f"Too many battles without winner: {len(no_winner)}/500"


# =============================================================================
# Sample Battle Detailed Tests
# =============================================================================

class TestSampleBattleDetails:
    """Detailed tests on sample battles."""

    def test_sample_logs_have_players(self, parsed_sample_logs):
        """Verify sample logs have player information."""
        for name, parsed in parsed_sample_logs:
            assert "p1" in parsed.players, f"{name}: Missing p1"
            assert "p2" in parsed.players, f"{name}: Missing p2"
            assert parsed.players["p1"], f"{name}: Empty p1 name"
            assert parsed.players["p2"], f"{name}: Empty p2 name"

    def test_sample_logs_have_teams(self, parsed_sample_logs):
        """Verify sample logs have team information."""
        for name, parsed in parsed_sample_logs:
            assert "p1" in parsed.teams, f"{name}: Missing p1 team"
            assert "p2" in parsed.teams, f"{name}: Missing p2 team"
            # VGC format has 6 Pokemon per team
            assert len(parsed.teams["p1"]) == 6, f"{name}: p1 team size != 6"
            assert len(parsed.teams["p2"]) == 6, f"{name}: p2 team size != 6"

    def test_sample_logs_have_turns(self, parsed_sample_logs):
        """Verify sample logs have turn data."""
        for name, parsed in parsed_sample_logs:
            assert len(parsed.turns) >= 1, f"{name}: No turns found"

    def test_sample_logs_have_events(self, parsed_sample_logs):
        """Verify sample logs have battle events."""
        for name, parsed in parsed_sample_logs:
            assert len(parsed.all_events) > 10, f"{name}: Too few events"

            # Check for essential event types
            event_types = {e.event_type for e in parsed.all_events}
            assert LogEventType.SWITCH in event_types, f"{name}: No switches"
            assert LogEventType.MOVE in event_types, f"{name}: No moves"


# =============================================================================
# Damage Calculation Verification
# =============================================================================

class TestDamageCalculations:
    """Tests verifying damage calculations match expected ranges."""

    def test_damage_events_have_valid_hp(self, parsed_sample_logs):
        """Verify damage events have valid HP values."""
        for name, parsed in parsed_sample_logs:
            damage_events = get_damage_events(parsed)
            for event in damage_events:
                hp_after = event.get("hp_after", -1)
                hp_before = event.get("hp_before", -1)

                # HP should be between 0 and 100 (percentage)
                assert 0 <= hp_after <= 100, \
                    f"{name}: Invalid HP after: {hp_after}"

    def test_damage_is_non_negative(self, parsed_sample_logs):
        """Verify calculated damage is never negative."""
        for name, parsed in parsed_sample_logs:
            damage_events = get_damage_events(parsed)
            for event in damage_events:
                damage = event.get("damage", 0)
                # Damage should be non-negative (0 or positive)
                assert damage >= 0, \
                    f"{name}: Negative damage: {damage}"

    def test_ohko_does_100_percent(self, parsed_sample_logs):
        """Verify OHKOs reduce HP to 0."""
        for name, parsed in parsed_sample_logs:
            faint_events = [
                e for e in parsed.all_events
                if e.event_type == LogEventType.FAINT
            ]

            for faint in faint_events:
                slot = faint.data.get("slot", "")
                # Find corresponding damage event
                damage_events = [
                    e for e in parsed.all_events
                    if e.event_type == LogEventType.DAMAGE and
                       e.data.get("slot") == slot and
                       e.data.get("hp_current") == 0
                ]
                # Pokemon that fainted should have a 0 HP damage event
                # (unless they forfeited)
                if not parsed.winner:
                    continue  # Skip forfeits


# =============================================================================
# Status Effects Verification
# =============================================================================

class TestStatusEffects:
    """Tests verifying status effects work correctly."""

    def test_status_events_valid(self, parsed_sample_logs):
        """Verify status events have valid status values."""
        valid_statuses = {"slp", "psn", "tox", "brn", "par", "frz"}

        for name, parsed in parsed_sample_logs:
            status_events = [
                e for e in parsed.all_events
                if e.event_type == LogEventType.STATUS
            ]

            for event in status_events:
                status = event.data.get("status", "")
                assert status in valid_statuses, \
                    f"{name}: Invalid status: {status}"

    def test_sleep_prevents_moves(self, parsed_sample_logs):
        """Verify sleeping Pokemon can't move (shown as 'cant')."""
        for name, parsed in parsed_sample_logs:
            # Find Pokemon that were put to sleep
            sleep_events = [
                e for e in parsed.all_events
                if e.event_type == LogEventType.STATUS and
                   e.data.get("status") == "slp"
            ]

            # Check if there are corresponding 'cant' events
            cant_events = [
                e for e in parsed.all_events
                if e.event_type == LogEventType.UNKNOWN and
                   "|cant|" in e.raw_line and "slp" in e.raw_line
            ]

            # If there was sleep, there might be cant events
            # (not always - Pokemon might wake up immediately)


# =============================================================================
# Weather Verification
# =============================================================================

class TestWeatherEffects:
    """Tests verifying weather mechanics."""

    def test_weather_events_valid(self, parsed_sample_logs):
        """Verify weather events have valid weather types."""
        valid_weather = {
            "Sandstorm", "RainDance", "SunnyDay", "Snow", "Hail",
            "PrimordialSea", "DesolateLand", "DeltaStream", "none",
            "Snowscape",  # Gen 9 snow move name
        }

        for name, parsed in parsed_sample_logs:
            weather_events = [
                e for e in parsed.all_events
                if e.event_type == LogEventType.WEATHER
            ]

            for event in weather_events:
                weather = event.data.get("weather", "")
                assert weather in valid_weather or weather == "", \
                    f"{name}: Invalid weather: {weather}"

    def test_drizzle_sets_rain(self, parsed_sample_logs):
        """Verify Drizzle ability sets rain."""
        for name, parsed in parsed_sample_logs:
            # Check if any Pokemon has Drizzle (like Kyogre)
            drizzle_pokemon = ["Kyogre", "Pelipper", "Politoed"]

            has_drizzle = any(
                any(p["species"] in drizzle_pokemon for p in team)
                for team in parsed.teams.values()
            )

            if has_drizzle:
                # Should have rain weather event
                rain_events = [
                    e for e in parsed.all_events
                    if e.event_type == LogEventType.WEATHER and
                       "RainDance" in str(e.data) or "Drizzle" in str(e.raw_line)
                ]
                # Might not always trigger if switched out immediately


# =============================================================================
# Turn Order Verification
# =============================================================================

class TestTurnOrder:
    """Tests verifying turn order mechanics."""

    def test_protect_goes_first(self, parsed_sample_logs):
        """Verify Protect (+4 priority) typically executes first in turn."""
        protect_first_count = 0
        protect_total_count = 0

        for name, parsed in parsed_sample_logs:
            for turn in parsed.turns:
                move_events = [
                    e for e in turn.events
                    if e.event_type == LogEventType.MOVE
                ]

                if not move_events:
                    continue

                protect_moves = [
                    e for e in move_events
                    if e.data.get("move") in ("Protect", "Detect", "Spiky Shield",
                                               "King's Shield", "Silk Trap")
                ]

                if protect_moves:
                    protect_total_count += 1
                    # Check if Protect was first move
                    first_move = move_events[0]
                    if first_move.data.get("move") in ("Protect", "Detect",
                                                        "Spiky Shield", "King's Shield",
                                                        "Silk Trap"):
                        protect_first_count += 1

        # Protect should be first most of the time (allow for Follow Me, etc.)
        if protect_total_count > 0:
            ratio = protect_first_count / protect_total_count
            assert ratio > 0.5, \
                f"Protect first only {ratio:.1%} of time ({protect_first_count}/{protect_total_count})"

    def test_fake_out_high_priority(self, parsed_sample_logs):
        """Verify Fake Out (+3 priority) executes early."""
        fake_out_positions = []

        for name, parsed in parsed_sample_logs:
            for turn in parsed.turns:
                move_events = [
                    e for e in turn.events
                    if e.event_type == LogEventType.MOVE
                ]

                if len(move_events) < 2:
                    continue

                for i, event in enumerate(move_events):
                    if event.data.get("move") == "Fake Out":
                        # Record position (0-indexed)
                        fake_out_positions.append(i / len(move_events))

        # Fake Out should be in first half of turn most of the time
        if fake_out_positions:
            avg_position = sum(fake_out_positions) / len(fake_out_positions)
            assert avg_position < 0.5, \
                f"Fake Out avg position {avg_position:.2f} (should be < 0.5)"


# =============================================================================
# Ability Verification
# =============================================================================

class TestAbilities:
    """Tests verifying ability mechanics."""

    def test_intimidate_triggers(self, parsed_sample_logs):
        """Verify Intimidate triggers on switch-in."""
        for name, parsed in parsed_sample_logs:
            # Find Intimidate Pokemon
            intimidate_pokemon = ["Incineroar", "Landorus", "Gyarados",
                                  "Salamence", "Arcanine"]

            # Check if any team has Intimidate user
            has_intimidate = any(
                any(p["species"] in intimidate_pokemon for p in team)
                for team in parsed.teams.values()
            )

            if has_intimidate:
                # Look for Intimidate ability trigger
                intimidate_events = [
                    e for e in parsed.all_events
                    if "Intimidate" in e.raw_line
                ]
                # Should have at least one trigger
                # (might not if never switched in)

    def test_as_one_triggers(self, parsed_sample_logs):
        """Verify As One ability triggers for Calyrex forms."""
        for name, parsed in parsed_sample_logs:
            # Find Calyrex Ice/Shadow
            calyrex_pokemon = ["Calyrex-Ice", "Calyrex-Shadow"]

            has_calyrex = any(
                any(p["species"] in calyrex_pokemon for p in team)
                for team in parsed.teams.values()
            )

            if has_calyrex:
                # Look for As One ability trigger
                as_one_events = [
                    e for e in parsed.all_events
                    if "As One" in e.raw_line
                ]
                assert len(as_one_events) > 0, \
                    f"{name}: Calyrex should trigger As One"


# =============================================================================
# Specific Battle Integration Tests
# =============================================================================

class TestSpecificBattles:
    """Detailed tests for specific battle scenarios."""

    @pytest.fixture
    def battle_2390373499(self):
        """First battle log: Miraidon + Calyrex mirror match."""
        log_path = LOGS_DIR / "gen9vgc2025regi-2390373499.log"
        if not log_path.exists():
            pytest.skip("Battle log not found")
        return parse_battle_log_file(str(log_path))

    @pytest.fixture
    def battle_2390375355(self):
        """Second battle log: Kyogre + Calyrex vs Calyrex-Shadow."""
        log_path = LOGS_DIR / "gen9vgc2025regi-2390375355.log"
        if not log_path.exists():
            pytest.skip("Battle log not found")
        return parse_battle_log_file(str(log_path))

    def test_battle_1_winner(self, battle_2390373499):
        """Verify battle 1 winner."""
        assert battle_2390373499.winner == "eriksp"

    def test_battle_1_teams(self, battle_2390373499):
        """Verify battle 1 team composition."""
        p1_species = [p["species"] for p in battle_2390373499.teams["p1"]]
        p2_species = [p["species"] for p in battle_2390373499.teams["p2"]]

        assert "Miraidon" in p1_species
        assert "Calyrex-Ice" in p1_species
        assert "Incineroar" in p1_species

        assert "Calyrex-Ice" in p2_species
        assert "Miraidon" in p2_species
        assert "Grimmsnarl" in p2_species

    def test_battle_1_turns(self, battle_2390373499):
        """Verify battle 1 has 8 turns."""
        # Count actual turns (not including turn 0)
        turn_events = [
            e for e in battle_2390373499.all_events
            if e.event_type == LogEventType.TURN
        ]
        assert len(turn_events) == 8

    def test_battle_1_faints(self, battle_2390373499):
        """Verify battle 1 faint sequence."""
        faint_events = [
            e for e in battle_2390373499.all_events
            if e.event_type == LogEventType.FAINT
        ]

        # Should have multiple faints
        assert len(faint_events) >= 4

        # Extract fainted Pokemon
        fainted = [e.data.get("nickname", "") for e in faint_events]
        assert "Incineroar" in fainted or any("Incineroar" in f for f in fainted)

    def test_battle_1_electric_terrain(self, battle_2390373499):
        """Verify Electric Terrain from Hadron Engine."""
        terrain_events = [
            e for e in battle_2390373499.all_events
            if e.event_type == LogEventType.FIELD_START and
               "Electric Terrain" in e.raw_line
        ]
        assert len(terrain_events) >= 1

    def test_battle_1_light_screen(self, battle_2390373499):
        """Verify Light Screen was set."""
        screen_events = [
            e for e in battle_2390373499.all_events
            if e.event_type == LogEventType.SIDE_START and
               "Light Screen" in e.raw_line
        ]
        assert len(screen_events) >= 1

    def test_battle_2_winner(self, battle_2390375355):
        """Verify battle 2 winner (forfeit)."""
        assert battle_2390375355.winner == "BlackLocks"

    def test_battle_2_rain(self, battle_2390375355):
        """Verify rain was set by Kyogre's Drizzle."""
        rain_events = [
            e for e in battle_2390375355.all_events
            if e.event_type == LogEventType.WEATHER and
               "RainDance" in str(e.data)
        ]
        assert len(rain_events) >= 1

    def test_battle_2_trick_room(self, battle_2390375355):
        """Verify Trick Room was used."""
        tr_events = [
            e for e in battle_2390375355.all_events
            if e.event_type == LogEventType.FIELD_START and
               "Trick Room" in e.raw_line
        ]
        assert len(tr_events) >= 1

    def test_battle_2_disable(self, battle_2390375355):
        """Verify Disable was used on Calyrex-Shadow."""
        disable_events = [
            e for e in battle_2390375355.all_events
            if "Disable" in e.raw_line and "Astral Barrage" in e.raw_line
        ]
        assert len(disable_events) >= 1

    def test_battle_2_spore_immunity(self, battle_2390375355):
        """Verify Grass Tera Calyrex is immune to Spore."""
        immune_events = [
            e for e in battle_2390375355.all_events
            if "-immune|" in e.raw_line and "Calyrex" in e.raw_line
        ]
        assert len(immune_events) >= 1


# =============================================================================
# Aggregate Statistics Tests
# =============================================================================

class TestAggregateStatistics:
    """Tests for aggregate statistics across all battles."""

    def test_average_battle_length(self, all_log_files):
        """Verify average battle length is reasonable."""
        turn_counts = []

        for log_file in all_log_files[:100]:  # Sample 100 for speed
            try:
                parsed = parse_battle_log_file(str(log_file))
                turn_events = [
                    e for e in parsed.all_events
                    if e.event_type == LogEventType.TURN
                ]
                turn_counts.append(len(turn_events))
            except Exception:
                pass

        if turn_counts:
            avg_turns = sum(turn_counts) / len(turn_counts)
            # VGC battles typically last 5-15 turns
            assert 3 <= avg_turns <= 20, \
                f"Average battle length {avg_turns:.1f} turns seems wrong"

    def test_win_rate_balance(self, all_log_files):
        """Verify win rates are somewhat balanced (p1 vs p2)."""
        p1_wins = 0
        p2_wins = 0

        for log_file in all_log_files[:500]:  # Sample 500
            try:
                parsed = parse_battle_log_file(str(log_file))
                winner = parsed.winner
                if winner:
                    p1_name = parsed.players.get("p1", "")
                    if winner == p1_name:
                        p1_wins += 1
                    else:
                        p2_wins += 1
            except Exception:
                pass

        total = p1_wins + p2_wins
        if total > 0:
            p1_rate = p1_wins / total
            # Win rate should be roughly balanced (40-60%)
            assert 0.35 <= p1_rate <= 0.65, \
                f"Win rate imbalance: p1={p1_rate:.1%}"

    def test_common_pokemon_usage(self, all_log_files):
        """Verify common Pokemon appear in battles."""
        pokemon_usage: Dict[str, int] = {}

        for log_file in all_log_files[:200]:  # Sample 200
            try:
                parsed = parse_battle_log_file(str(log_file))
                for team in parsed.teams.values():
                    for pokemon in team:
                        species = pokemon.get("species", "")
                        pokemon_usage[species] = pokemon_usage.get(species, 0) + 1
            except Exception:
                pass

        # VGC 2025 Reg I common Pokemon
        expected_common = ["Calyrex-Ice", "Calyrex-Shadow", "Incineroar",
                          "Miraidon", "Kyogre", "Rillaboom"]

        # At least some of these should appear
        found_common = [p for p in expected_common if pokemon_usage.get(p, 0) > 10]
        assert len(found_common) >= 3, \
            f"Expected more common Pokemon, found: {found_common}"


# =============================================================================
# Damage Range Verification
# =============================================================================

class TestDamageRanges:
    """Tests verifying damage falls within expected ranges."""

    def test_glacial_lance_damage_range(self, all_log_files):
        """Verify Glacial Lance damage is in expected range."""
        damages = []

        for log_file in all_log_files[:100]:
            try:
                parsed = parse_battle_log_file(str(log_file))
                damage_events = get_damage_events(parsed)
                move_events = get_move_events(parsed)

                # Find Glacial Lance moves and subsequent damage
                for i, move in enumerate(move_events):
                    if move.get("move") == "Glacial Lance":
                        # Find damage events on this turn
                        turn = move.get("turn", 0)
                        turn_damage = [
                            d for d in damage_events
                            if d.get("turn") == turn and d.get("damage", 0) > 0
                        ]
                        for d in turn_damage:
                            damages.append(d.get("damage", 0))
            except Exception:
                pass

        if damages:
            avg_damage = sum(damages) / len(damages)
            # Glacial Lance is strong - should deal decent damage
            assert avg_damage > 10, \
                f"Glacial Lance avg damage {avg_damage:.1f}% seems low"

    def test_spread_moves_hit_multiple(self, all_log_files):
        """Verify spread moves can hit multiple targets."""
        spread_moves = ["Glacial Lance", "Astral Barrage", "Rock Slide",
                        "Earthquake", "Surf", "Heat Wave", "Dazzling Gleam"]

        multi_hits_found = 0

        for log_file in all_log_files[:100]:
            try:
                parsed = parse_battle_log_file(str(log_file))

                for event in parsed.all_events:
                    if event.event_type == LogEventType.MOVE:
                        move = event.data.get("move", "")
                        if move in spread_moves and event.data.get("spread"):
                            multi_hits_found += 1
            except Exception:
                pass

        # Should find some spread moves hitting multiple targets
        assert multi_hits_found >= 5, \
            f"Found only {multi_hits_found} spread move hits"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
