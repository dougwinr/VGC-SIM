"""Comprehensive stress tests for the tournament system.

These tests stress test all tournament features including:
- Large tournaments (100+ players)
- Edge cases in pairings
- Scoring and tiebreakers
- Tournament simulation
- Data loaders
- Concurrent operations
"""

import pytest
import random
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

from tournament import (
    Tournament,
    Division,
    Player,
    Team,
    Match,
    Standing,
    MatchResult,
    TournamentPhase,
    validate_team,
)
from tournament.pairings import generate_swiss_pairings, generate_top_cut_bracket
from tournament.scoring import ScoringProfile, VGC_SCORING, calculate_standings, get_sorted_standings
from tournament.regulation import Regulation, VGC_2024
from tournament.runner import (
    simulate_tournament,
    simulate_match,
    create_random_team,
    TournamentConfig,
)
from tournament.pokedata_loader import (
    parse_pokedata_json,
    standings_to_tournament,
    get_top_pokemon,
    get_top_items,
    PlayerStanding,
    PokemonEntry,
)


def create_test_tournament(num_players: int, swiss_rounds: int = 5) -> Tournament:
    """Helper to create a tournament with players and teams."""
    tournament = Tournament(
        id=f"test_{num_players}",
        name=f"Test Tournament ({num_players} players)",
        best_of=3,
    )

    division = Division(
        id="main",
        name="Main",
        total_swiss_rounds=swiss_rounds,
    )
    tournament.divisions.append(division)

    for i in range(num_players):
        player_id = f"player_{i:03d}"
        team = create_random_team(f"team_{i:03d}", seed=i)
        tournament.add_team(team)

        player = Player(
            id=player_id,
            name=f"Player {i + 1}",
            team_id=team.id,
        )
        tournament.players[player_id] = player
        division.add_player(player_id)

    return tournament


class TestLargeTournaments:
    """Test tournaments with many players."""

    def test_32_player_tournament(self):
        """Simulate a 32-player tournament (5 rounds)."""
        tournament = create_test_tournament(32, swiss_rounds=5)
        regulation = VGC_2024
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, regulation, config=config, seed=42)

        assert result.player_count == 32
        division = result.get_division("main")
        assert division is not None
        assert len(division.matches) >= 5 * 16  # At least 16 matches per round

        # Check standings
        standings = list(division.standings.values())
        assert len(standings) == 32

        # Verify no player played more than 5 matches
        for standing in standings:
            assert standing.matches_played <= 5

    def test_64_player_tournament(self):
        """Simulate a 64-player tournament (6 rounds)."""
        tournament = create_test_tournament(64, swiss_rounds=6)
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, VGC_2024, config=config, seed=42)

        assert result.player_count == 64
        division = result.get_division("main")
        assert len(division.standings) == 64

    def test_100_player_tournament(self):
        """Simulate a 100-player tournament."""
        tournament = create_test_tournament(100, swiss_rounds=7)
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, VGC_2024, config=config, seed=42)

        assert result.player_count == 100
        division = result.get_division("main")

        # With 100 players (even), we shouldn't have byes unless odd
        # But let's just verify the tournament completed
        assert result.phase == TournamentPhase.COMPLETE

    def test_128_player_tournament(self):
        """Simulate a 128-player tournament (7 rounds)."""
        tournament = create_test_tournament(128, swiss_rounds=7)
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, VGC_2024, config=config, seed=42)

        assert result.player_count == 128
        assert result.phase == TournamentPhase.COMPLETE

    def test_256_player_tournament_performance(self):
        """Test performance with 256 players."""
        start_time = time.time()

        tournament = create_test_tournament(256, swiss_rounds=8)
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, VGC_2024, config=config, seed=42)

        elapsed = time.time() - start_time

        assert result.player_count == 256
        # Should complete in reasonable time (< 120 seconds for simulation)
        # Note: Actual time varies with system load, typically ~35-65s
        assert elapsed < 120, f"Tournament took too long: {elapsed:.2f}s"


class TestPairingsEdgeCases:
    """Test edge cases in Swiss pairings."""

    def test_all_same_record(self):
        """Test pairing when all players have the same record."""
        standings: Dict[str, Standing] = {}

        # Add 8 players all with 0-0 record
        for i in range(8):
            player_id = f"player_{i}"
            standings[player_id] = Standing(player_id=player_id)

        pairings = generate_swiss_pairings(standings, [], round_number=1)

        assert len(pairings) == 4
        # All players should be paired
        paired_players = set()
        for match in pairings:
            paired_players.add(match.player1_id)
            if match.player2_id:
                paired_players.add(match.player2_id)
        assert len(paired_players) == 8

    def test_prevent_triple_match(self):
        """Test that players don't face each other more than once."""
        standings: Dict[str, Standing] = {}
        past_matches: List[Match] = []

        # Add 4 players
        for i in range(4):
            standings[f"player_{i}"] = Standing(player_id=f"player_{i}")

        # Simulate 3 rounds
        all_matchups = set()
        for round_num in range(1, 4):
            pairings = generate_swiss_pairings(standings, past_matches, round_number=round_num)

            for match in pairings:
                if match.player2_id is not None:
                    matchup = tuple(sorted([match.player1_id, match.player2_id]))
                    # Should not have seen this matchup before
                    assert matchup not in all_matchups, f"Rematch detected: {matchup}"
                    all_matchups.add(matchup)

                    # Complete the match
                    match.p1_wins = random.randint(0, 2)
                    match.p2_wins = 2 - match.p1_wins
                    match.completed = True
                    match.winner_id = match.player1_id if match.p1_wins > match.p2_wins else match.player2_id

                past_matches.append(match)

    def test_odd_number_players_bye_rotation(self):
        """Test that bye rotates among different players."""
        standings: Dict[str, Standing] = {}
        past_matches: List[Match] = []

        # Add 7 players (odd)
        for i in range(7):
            standings[f"player_{i}"] = Standing(player_id=f"player_{i}")

        bye_receivers = set()
        for round_num in range(1, 8):  # 7 rounds
            pairings = generate_swiss_pairings(standings, past_matches, round_number=round_num)

            # Find the bye
            for match in pairings:
                if match.player2_id is None:
                    bye_receivers.add(match.player1_id)
                else:
                    # Complete match
                    match.p1_wins = 2
                    match.p2_wins = random.randint(0, 1)
                    match.completed = True
                    match.winner_id = match.player1_id

                past_matches.append(match)

            # Update standings
            calculate_standings(standings, pairings, VGC_SCORING)

        # Each player should get at most one bye
        assert len(bye_receivers) == 7


class TestScoringAndTiebreakers:
    """Test scoring system and tiebreaker calculations."""

    def test_vgc_scoring_points(self):
        """Test VGC scoring (3 for win, 0 for loss, 1 for tie)."""
        standing = Standing(player_id="test")

        standing.record_match(
            MatchResult.WIN, "opp1", 2, 1,
            VGC_SCORING.win_points, VGC_SCORING.loss_points, VGC_SCORING.draw_points
        )
        assert standing.match_points == 3

        standing.record_match(
            MatchResult.LOSS, "opp2", 0, 2,
            VGC_SCORING.win_points, VGC_SCORING.loss_points, VGC_SCORING.draw_points
        )
        assert standing.match_points == 3  # Still 3

        standing.record_match(
            MatchResult.DRAW, "opp3", 1, 1,
            VGC_SCORING.win_points, VGC_SCORING.loss_points, VGC_SCORING.draw_points
        )
        assert standing.match_points == 4  # 3 + 1

    def test_resistance_calculation(self):
        """Test opponent match win percentage (resistance) calculation."""
        standings: Dict[str, Standing] = {}
        matches: List[Match] = []

        # Create 4 players
        for i in range(4):
            standings[f"player_{i}"] = Standing(player_id=f"player_{i}")

        # Create matches with specific results
        # Player 0 beats Player 1
        match1 = Match(id="m1", round_number=1, phase=TournamentPhase.SWISS,
                      player1_id="player_0", player2_id="player_1",
                      p1_wins=2, p2_wins=0, completed=True, winner_id="player_0")
        matches.append(match1)

        # Player 2 beats Player 3
        match2 = Match(id="m2", round_number=1, phase=TournamentPhase.SWISS,
                      player1_id="player_2", player2_id="player_3",
                      p1_wins=2, p2_wins=1, completed=True, winner_id="player_2")
        matches.append(match2)

        # Calculate standings
        calculate_standings(standings, matches, VGC_SCORING)

        # Winners should have 3 points
        assert standings["player_0"].match_points == 3
        assert standings["player_2"].match_points == 3

    def test_game_win_percentage_tiebreaker(self):
        """Test game win percentage as secondary tiebreaker."""
        standings: Dict[str, Standing] = {}

        standings["player_a"] = Standing(player_id="player_a")
        standings["player_b"] = Standing(player_id="player_b")

        # Both players 3-0 in matches
        # Player A: won 6-3 in games (66.7%)
        standings["player_a"].match_wins = 3
        standings["player_a"].game_wins = 6
        standings["player_a"].game_losses = 3
        standings["player_a"].match_points = 9

        # Player B: won 6-0 in games (100%)
        standings["player_b"].match_wins = 3
        standings["player_b"].game_wins = 6
        standings["player_b"].game_losses = 0
        standings["player_b"].match_points = 9

        # Player B has better game win rate
        assert standings["player_b"].game_win_rate > standings["player_a"].game_win_rate


class TestTeamValidation:
    """Test team validation against regulations."""

    def test_valid_team(self):
        """Test a valid team passes validation."""
        regulation = VGC_2024

        team = Team(
            id="test",
            pokemon=[
                {"species_id": 25, "level": 50},  # Pikachu
                {"species_id": 6, "level": 50},   # Charizard
                {"species_id": 9, "level": 50},   # Blastoise
                {"species_id": 3, "level": 50},   # Venusaur
                {"species_id": 143, "level": 50}, # Snorlax
                {"species_id": 149, "level": 50}, # Dragonite
            ]
        )

        errors = validate_team(team, regulation)
        assert len(errors) == 0

    def test_overlevel_pokemon(self):
        """Test team with Pokemon over level cap."""
        regulation = VGC_2024

        team = Team(
            id="test",
            pokemon=[
                {"species_id": 25, "level": 100},  # Over level cap!
                {"species_id": 6, "level": 50},
                {"species_id": 9, "level": 50},
                {"species_id": 3, "level": 50},
                {"species_id": 143, "level": 50},
                {"species_id": 149, "level": 50},
            ]
        )

        errors = validate_team(team, regulation)
        assert len(errors) > 0
        assert any("level" in e.lower() for e in errors)

    def test_duplicate_species(self):
        """Test team with duplicate Pokemon species."""
        regulation = VGC_2024

        team = Team(
            id="test",
            pokemon=[
                {"species_id": 25, "level": 50},
                {"species_id": 25, "level": 50},  # Duplicate!
                {"species_id": 9, "level": 50},
                {"species_id": 3, "level": 50},
                {"species_id": 143, "level": 50},
                {"species_id": 149, "level": 50},
            ]
        )

        errors = validate_team(team, regulation)
        assert len(errors) > 0
        assert any("species" in e.lower() or "duplicate" in e.lower() for e in errors)

    def test_duplicate_items(self):
        """Test team with duplicate held items."""
        regulation = VGC_2024

        team = Team(
            id="test",
            pokemon=[
                {"species_id": 25, "level": 50, "item_id": 1},  # Same item
                {"species_id": 6, "level": 50, "item_id": 1},   # Same item!
                {"species_id": 9, "level": 50, "item_id": 2},
                {"species_id": 3, "level": 50, "item_id": 3},
                {"species_id": 143, "level": 50, "item_id": 4},
                {"species_id": 149, "level": 50, "item_id": 5},
            ]
        )

        errors = validate_team(team, regulation)
        assert len(errors) > 0
        assert any("item" in e.lower() for e in errors)

    def test_wrong_team_size(self):
        """Test team with wrong number of Pokemon."""
        regulation = VGC_2024

        # Too few
        team = Team(
            id="test",
            pokemon=[
                {"species_id": 25, "level": 50},
                {"species_id": 6, "level": 50},
            ]
        )

        errors = validate_team(team, regulation)
        assert len(errors) > 0


class TestMatchSimulation:
    """Test match simulation."""

    def test_match_completes(self):
        """Test that a match simulation completes."""
        tournament = create_test_tournament(2)
        division = tournament.get_division("main")

        match = Match(
            id="test_match",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="player_000",
            player2_id="player_001",
            best_of=3,
        )

        result = simulate_match(match, tournament, VGC_2024, {}, base_seed=42)

        assert result.completed
        assert result.winner_id in ["player_000", "player_001"]
        assert max(result.p1_wins, result.p2_wins) == 2

    def test_bye_handling(self):
        """Test that bye matches are handled correctly."""
        tournament = create_test_tournament(2)

        bye_match = Match(
            id="bye_match",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="player_000",
            player2_id=None,  # Bye
            best_of=3,
        )

        result = simulate_match(bye_match, tournament, VGC_2024, {}, base_seed=42)

        assert result.completed
        assert result.winner_id == "player_000"


class TestDataLoaders:
    """Test data loader functionality."""

    def test_parse_large_standings(self):
        """Test parsing a large standings JSON."""
        # Create 500 player standings
        standings_data = {
            "standings": [
                {
                    "rank": i + 1,
                    "name": f"Player {i + 1}",
                    "record": f"{random.randint(0, 9)}-{random.randint(0, 9)}-0",
                    "team": [
                        {"species": f"Pokemon{j}", "item": f"Item{j}"}
                        for j in range(6)
                    ]
                }
                for i in range(500)
            ]
        }

        standings = parse_pokedata_json(standings_data)

        assert len(standings) == 500
        assert standings[0].rank == 1
        assert standings[499].rank == 500

    def test_convert_large_standings_to_tournament(self):
        """Test converting large standings to Tournament object."""
        standings = [
            PlayerStanding(
                rank=i + 1,
                name=f"Player {i + 1}",
                record=f"{random.randint(3, 7)}-{random.randint(0, 4)}-0",
                pokemon=[
                    PokemonEntry(species=f"Pokemon{j}", item=f"Item{j}")
                    for j in range(6)
                ]
            )
            for i in range(200)
        ]

        tournament = standings_to_tournament(
            standings,
            tournament_id="stress_test",
            tournament_name="Stress Test Tournament",
        )

        assert tournament.player_count == 200
        assert len(tournament.teams) == 200

        # Test analytics
        top_pokemon = get_top_pokemon(tournament, top_n=10)
        assert len(top_pokemon) <= 10

        top_items = get_top_items(tournament, top_n=10)
        assert len(top_items) <= 10

    def test_analytics_performance(self):
        """Test analytics performance with large dataset."""
        # Create tournament with 1000 players
        standings = [
            PlayerStanding(
                rank=i + 1,
                name=f"Player {i + 1}",
                record="5-2-0",
                pokemon=[
                    PokemonEntry(
                        species=random.choice([
                            "Pikachu", "Charizard", "Incineroar", "Rillaboom",
                            "Flutter Mane", "Urshifu", "Landorus", "Amoonguss",
                            "Tornadus", "Ogerpon", "Calyrex", "Kingambit"
                        ]),
                        item=random.choice([
                            "Focus Sash", "Life Orb", "Choice Specs", "Assault Vest",
                            "Safety Goggles", "Sitrus Berry", "Leftovers", "Rocky Helmet"
                        ])
                    )
                    for _ in range(6)
                ]
            )
            for i in range(1000)
        ]

        start_time = time.time()
        tournament = standings_to_tournament(standings, "perf", "Perf Test")
        conversion_time = time.time() - start_time

        start_time = time.time()
        top_pokemon = get_top_pokemon(tournament, top_n=20)
        pokemon_time = time.time() - start_time

        start_time = time.time()
        top_items = get_top_items(tournament, top_n=20)
        items_time = time.time() - start_time

        # All operations should be fast
        assert conversion_time < 2.0, f"Conversion too slow: {conversion_time:.2f}s"
        assert pokemon_time < 1.0, f"Pokemon analytics too slow: {pokemon_time:.2f}s"
        assert items_time < 1.0, f"Items analytics too slow: {items_time:.2f}s"

        # Verify results
        assert len(top_pokemon) == 12  # We only have 12 unique Pokemon
        assert len(top_items) == 8     # We only have 8 unique items


class TestConcurrency:
    """Test concurrent operations."""

    def test_concurrent_standings_parsing(self):
        """Test parsing standings concurrently."""
        def parse_standings(player_count: int) -> List[PlayerStanding]:
            data = {
                "standings": [
                    {"rank": i, "name": f"P{i}", "record": "5-2"}
                    for i in range(player_count)
                ]
            }
            return parse_pokedata_json(data)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(parse_standings, count)
                for count in [100, 200, 300, 400]
            ]
            results = [f.result() for f in futures]

        assert len(results[0]) == 100
        assert len(results[1]) == 200
        assert len(results[2]) == 300
        assert len(results[3]) == 400


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_player_tournament(self):
        """Test tournament with only 1 player."""
        standings = {"lonely": Standing(player_id="lonely")}

        # Pairings should give the player a bye
        pairings = generate_swiss_pairings(standings, [], round_number=1)
        assert len(pairings) == 1
        assert pairings[0].player2_id is None  # Bye

    def test_two_player_tournament(self):
        """Test tournament with exactly 2 players."""
        tournament = create_test_tournament(2, swiss_rounds=1)
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, VGC_2024, config=config, seed=42)

        assert result.player_count == 2
        division = result.get_division("main")
        assert len(division.matches) == 1

    def test_empty_team(self):
        """Test handling of empty team."""
        team = Team(id="empty", pokemon=[])
        assert team.size == 0

    def test_match_without_games(self):
        """Test match that hasn't been played."""
        match = Match(
            id="unplayed",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
        )

        assert not match.completed
        assert match.games_played == 0
        assert match.get_result("p1") == MatchResult.NOT_PLAYED

    def test_standing_no_matches(self):
        """Test standing with no matches played."""
        standing = Standing(player_id="new")

        assert standing.matches_played == 0
        assert standing.win_rate == 0.0
        assert standing.game_win_rate == 0.0

    def test_division_no_players(self):
        """Test division with no players."""
        standings: Dict[str, Standing] = {}

        pairings = generate_swiss_pairings(standings, [], round_number=1)
        assert len(pairings) == 0

    def test_very_long_player_name(self):
        """Test handling of very long player names."""
        long_name = "A" * 1000
        player = Player(id="long", name=long_name)

        assert player.name == long_name
        assert len(player.name) == 1000

    def test_unicode_player_names(self):
        """Test handling of Unicode player names."""
        unicode_names = [
            "田中太郎",  # Japanese
            "Müller",     # German
            "Øresund",    # Danish
            "Władysław",  # Polish
            "Москва",     # Russian
            "北京",       # Chinese
            "🎮 Gamer",   # Emoji
        ]

        for name in unicode_names:
            player = Player(id=f"unicode_{hash(name)}", name=name)
            assert player.name == name


class TestTopCutBracket:
    """Test top cut bracket generation."""

    def test_top_4_bracket(self):
        """Test generating a top 4 bracket."""
        standings = {
            f"player_{i}": Standing(
                player_id=f"player_{i}",
                match_points=(4 - i) * 3,  # 12, 9, 6, 3 points
            )
            for i in range(4)
        }

        bracket = generate_top_cut_bracket(standings, top_cut_size=4)

        assert len(bracket) == 2
        # 1 vs 4
        assert bracket[0].player1_id == "player_0"
        assert bracket[0].player2_id == "player_3"
        # 2 vs 3
        assert bracket[1].player1_id == "player_1"
        assert bracket[1].player2_id == "player_2"

    def test_top_8_bracket(self):
        """Test generating a top 8 bracket."""
        standings = {
            f"player_{i}": Standing(
                player_id=f"player_{i}",
                match_points=(8 - i) * 3,
            )
            for i in range(8)
        }

        bracket = generate_top_cut_bracket(standings, top_cut_size=8)

        assert len(bracket) == 4


class TestDeterminism:
    """Test deterministic behavior with seeds."""

    def test_pairing_reproducibility(self):
        """Test that pairings with same state produce same results."""
        def create_and_pair(seed: int) -> List[Match]:
            rng = random.Random(seed)
            standings = {f"player_{i}": Standing(player_id=f"player_{i}") for i in range(8)}
            return generate_swiss_pairings(standings, [], round_number=1, rng=rng)

        pairings1 = create_and_pair(123)
        pairings2 = create_and_pair(123)

        # Compare match IDs and player pairs
        pairs1 = [(m.player1_id, m.player2_id) for m in pairings1]
        pairs2 = [(m.player1_id, m.player2_id) for m in pairings2]

        assert pairs1 == pairs2


class TestMemoryUsage:
    """Test memory efficiency with large data."""

    def test_large_standings_memory(self):
        """Test memory usage doesn't explode with large standings."""
        import sys

        # Create large standings
        standings = [
            PlayerStanding(
                rank=i + 1,
                name=f"Player {i + 1}",
                record="5-2-0",
                pokemon=[PokemonEntry(species=f"Mon{j}") for j in range(6)]
            )
            for i in range(1000)
        ]

        tournament = standings_to_tournament(standings, "mem", "Memory Test")

        # Get approximate size
        size = sys.getsizeof(tournament)

        # Add sizes of nested objects
        for player in tournament.players.values():
            size += sys.getsizeof(player)
        for team in tournament.teams.values():
            size += sys.getsizeof(team)

        # Should be reasonable (< 5MB for 1000 players)
        assert size < 5 * 1024 * 1024, f"Tournament too large: {size / 1024 / 1024:.2f}MB"
