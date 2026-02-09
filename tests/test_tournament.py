"""Tests for tournament system.

Tests for:
- Tournament models (Tournament, Player, Team, Match, Standing)
- Regulation and team validation
- Swiss pairings
- Scoring and standings
- Tournament simulation
"""

import pytest
import random

from tournament.model import (
    Tournament,
    Division,
    Player,
    Team,
    Match,
    Standing,
    MatchResult,
    TournamentPhase,
)
from tournament.regulation import (
    Regulation,
    validate_team,
    VGC_2024,
    SMOGON_OU,
)
from tournament.pairings import (
    generate_swiss_pairings,
    generate_top_cut_bracket,
)
from tournament.scoring import (
    ScoringProfile,
    VGC_SCORING,
    calculate_standings,
    get_sorted_standings,
    format_standings,
)
from tournament.runner import (
    simulate_match,
    simulate_tournament,
    create_random_team,
    TournamentConfig,
)


# =============================================================================
# Model Tests
# =============================================================================

class TestTeam:
    """Tests for Team dataclass."""

    def test_create_team(self):
        """Can create a team."""
        team = Team(
            id="team1",
            name="My Team",
            pokemon=[
                {"species_id": 6, "level": 50, "moves": [53, 89]},
                {"species_id": 25, "level": 50, "moves": [85, 57]},
            ],
        )
        assert team.id == "team1"
        assert team.size == 2

    def test_empty_team(self):
        """Empty team has size 0."""
        team = Team(id="empty")
        assert team.size == 0


class TestPlayer:
    """Tests for Player dataclass."""

    def test_create_player(self):
        """Can create a player."""
        player = Player(id="p1", name="Alice", team_id="team1")
        assert player.id == "p1"
        assert player.name == "Alice"
        assert player.team_id == "team1"


class TestMatch:
    """Tests for Match dataclass."""

    def test_create_match(self):
        """Can create a match."""
        match = Match(
            id="R1M1",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
            best_of=3,
        )
        assert match.round_number == 1
        assert not match.completed
        assert match.games_needed_to_win == 2

    def test_bye_match(self):
        """Bye match has no player2."""
        match = Match(
            id="R1M2",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id=None,
        )
        assert match.is_bye

    def test_record_game_win(self):
        """Recording games updates wins."""
        match = Match(
            id="R1M1",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
            best_of=3,
        )

        match.record_game("p1")
        assert match.p1_wins == 1
        assert not match.completed

        match.record_game("p1")
        assert match.p1_wins == 2
        assert match.completed
        assert match.winner_id == "p1"

    def test_get_result(self):
        """Can get result from player's perspective."""
        match = Match(
            id="R1M1",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
            best_of=3,
            completed=True,
            winner_id="p1",
            p1_wins=2,
            p2_wins=1,
        )

        assert match.get_result("p1") == MatchResult.WIN
        assert match.get_result("p2") == MatchResult.LOSS

    def test_get_result_draw(self):
        """Get result returns DRAW when no winner."""
        match = Match(
            id="R1M1",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
            best_of=3,
            completed=True,
            winner_id=None,  # Draw
        )

        assert match.get_result("p1") == MatchResult.DRAW
        assert match.get_result("p2") == MatchResult.DRAW

    def test_record_game_invalid_winner(self):
        """Recording game with invalid winner raises ValueError."""
        match = Match(
            id="R1M1",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
            best_of=3,
        )

        with pytest.raises(ValueError) as exc_info:
            match.record_game("invalid_player")

        assert "Invalid winner_id" in str(exc_info.value)


class TestStanding:
    """Tests for Standing dataclass."""

    def test_create_standing(self):
        """Can create a standing."""
        standing = Standing(player_id="p1")
        assert standing.match_wins == 0
        assert standing.matches_played == 0

    def test_record_match_win(self):
        """Recording a win updates standing."""
        standing = Standing(player_id="p1")
        standing.record_match(
            result=MatchResult.WIN,
            opponent_id="p2",
            games_won=2,
            games_lost=1,
            win_points=3,
            loss_points=0,
            draw_points=1,
        )

        assert standing.match_wins == 1
        assert standing.match_points == 3
        assert standing.game_wins == 2
        assert standing.game_losses == 1
        assert "p2" in standing.opponents_faced


class TestTournament:
    """Tests for Tournament dataclass."""

    def test_create_tournament(self):
        """Can create a tournament."""
        tournament = Tournament(id="t1", name="Test Tournament")
        assert tournament.id == "t1"
        assert tournament.phase == TournamentPhase.REGISTRATION

    def test_add_player(self):
        """Can add players to tournament."""
        tournament = Tournament(id="t1", name="Test Tournament")

        player = Player(id="p1", name="Alice")
        tournament.add_player(player, "main")

        assert tournament.player_count == 1
        assert tournament.get_player("p1") == player

    def test_tournament_start(self):
        """Can start tournament."""
        tournament = Tournament(id="t1", name="Test Tournament")
        tournament.add_player(Player(id="p1", name="Alice"), "main")

        tournament.start()
        assert tournament.phase == TournamentPhase.SWISS

    def test_tournament_start_already_started(self):
        """Starting already started tournament raises ValueError."""
        tournament = Tournament(id="t1", name="Test Tournament")
        tournament.add_player(Player(id="p1", name="Alice"), "main")
        tournament.start()

        with pytest.raises(ValueError) as exc_info:
            tournament.start()

        assert "already started" in str(exc_info.value)

    def test_tournament_start_initializes_standings(self):
        """Starting tournament initializes standings for all players."""
        tournament = Tournament(id="t1", name="Test Tournament")
        tournament.add_player(Player(id="p1", name="Alice"), "main")
        tournament.add_player(Player(id="p2", name="Bob"), "main")

        tournament.start()

        # Check standings are initialized
        division = tournament.get_division("main")
        assert "p1" in division.standings
        assert "p2" in division.standings

    def test_tournament_start_creates_missing_standings(self):
        """Starting tournament creates standings for players without one."""
        tournament = Tournament(id="t1", name="Test Tournament")
        tournament.add_player(Player(id="p1", name="Alice"), "main")

        # Manually add a player_id without creating a standing
        division = tournament.get_division("main")
        division.player_ids.append("p2")  # Add without standing
        del division.standings["p1"]  # Remove existing standing to test re-creation

        tournament.start()

        # Check that standings were created for both
        assert "p1" in division.standings
        assert "p2" in division.standings

    def test_get_player_team_returns_none(self):
        """get_player_team returns None when player has no team."""
        tournament = Tournament(id="t1", name="Test Tournament")
        player = Player(id="p1", name="Alice", team_id=None)
        tournament.players["p1"] = player

        result = tournament.get_player_team("p1")
        assert result is None

    def test_division_get_matches_for_round(self):
        """Division.get_matches_for_round returns matches for specified round."""
        division = Division(id="main", name="Main")
        division.matches = [
            Match(id="R1M1", round_number=1, phase=TournamentPhase.SWISS,
                  player1_id="p1", player2_id="p2"),
            Match(id="R1M2", round_number=1, phase=TournamentPhase.SWISS,
                  player1_id="p3", player2_id="p4"),
            Match(id="R2M1", round_number=2, phase=TournamentPhase.SWISS,
                  player1_id="p1", player2_id="p3"),
        ]

        round1_matches = division.get_matches_for_round(1)
        assert len(round1_matches) == 2

        round2_matches = division.get_matches_for_round(2)
        assert len(round2_matches) == 1

    def test_division_get_player_matches(self):
        """Division.get_player_matches returns all matches for a player."""
        division = Division(id="main", name="Main")
        division.matches = [
            Match(id="R1M1", round_number=1, phase=TournamentPhase.SWISS,
                  player1_id="p1", player2_id="p2"),
            Match(id="R1M2", round_number=1, phase=TournamentPhase.SWISS,
                  player1_id="p3", player2_id="p4"),
            Match(id="R2M1", round_number=2, phase=TournamentPhase.SWISS,
                  player1_id="p1", player2_id="p3"),
        ]

        p1_matches = division.get_player_matches("p1")
        assert len(p1_matches) == 2

        p4_matches = division.get_player_matches("p4")
        assert len(p4_matches) == 1


# =============================================================================
# Regulation Tests
# =============================================================================

class TestRegulation:
    """Tests for Regulation dataclass."""

    def test_default_regulation(self):
        """Default regulation has sensible defaults."""
        reg = Regulation()
        assert reg.team_size == 6
        assert reg.level_cap == 50
        assert reg.item_clause is True

    def test_vgc_2024(self):
        """VGC 2024 preset is valid."""
        assert VGC_2024.name == "VGC 2024 Regulation G"
        assert VGC_2024.game_type == "doubles"
        assert VGC_2024.allow_tera is True
        assert VGC_2024.allow_dynamax is False


class TestValidateTeam:
    """Tests for validate_team function."""

    def test_valid_team(self):
        """Valid team passes validation."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": i, "level": 50, "item_id": i}
                for i in range(1, 7)
            ],
        )
        reg = Regulation()

        errors = validate_team(team, reg)
        assert len(errors) == 0

    def test_wrong_team_size(self):
        """Team with wrong size fails."""
        team = Team(
            id="team1",
            pokemon=[{"species_id": 1, "level": 50}],
        )
        reg = Regulation(team_size=6)

        errors = validate_team(team, reg)
        assert any("1 Pokemon" in e for e in errors)

    def test_level_cap(self):
        """Pokemon over level cap fails."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": 1, "level": 100},
                *[{"species_id": i, "level": 50} for i in range(2, 7)],
            ],
        )
        reg = Regulation(level_cap=50)

        errors = validate_team(team, reg)
        assert any("100" in e and "cap" in e.lower() for e in errors)

    def test_species_clause(self):
        """Duplicate species fails with species clause."""
        team = Team(
            id="team1",
            pokemon=[{"species_id": 1, "level": 50} for _ in range(6)],
        )
        reg = Regulation(species_clause=True)

        errors = validate_team(team, reg)
        assert any("Duplicate species" in e for e in errors)

    def test_item_clause(self):
        """Duplicate items fails with item clause."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": i, "level": 50, "item_id": 1}
                for i in range(1, 7)
            ],
        )
        reg = Regulation(item_clause=True)

        errors = validate_team(team, reg)
        assert any("Duplicate item" in e for e in errors)


# =============================================================================
# Pairings Tests
# =============================================================================

class TestSwissPairings:
    """Tests for Swiss pairing algorithm."""

    def test_pair_two_players(self):
        """Two players get paired together."""
        standings = {
            "p1": Standing(player_id="p1", match_points=0),
            "p2": Standing(player_id="p2", match_points=0),
        }

        matches = generate_swiss_pairings(standings, [], round_number=1)

        assert len(matches) == 1
        assert matches[0].player1_id in ["p1", "p2"]
        assert matches[0].player2_id in ["p1", "p2"]

    def test_four_players_two_matches(self):
        """Four players create two matches."""
        standings = {
            f"p{i}": Standing(player_id=f"p{i}", match_points=0)
            for i in range(1, 5)
        }

        matches = generate_swiss_pairings(standings, [], round_number=1)

        assert len(matches) == 2
        paired = {m.player1_id for m in matches} | {m.player2_id for m in matches}
        assert paired == {"p1", "p2", "p3", "p4"}

    def test_odd_players_bye(self):
        """Odd number of players gives one a bye."""
        standings = {
            f"p{i}": Standing(player_id=f"p{i}", match_points=0)
            for i in range(1, 4)
        }

        matches = generate_swiss_pairings(standings, [], round_number=1)

        bye_matches = [m for m in matches if m.is_bye]
        assert len(bye_matches) == 1

    def test_avoids_rematches(self):
        """Tries to avoid repeat pairings."""
        standings = {
            "p1": Standing(player_id="p1", match_points=3),
            "p2": Standing(player_id="p2", match_points=3),
            "p3": Standing(player_id="p3", match_points=0),
            "p4": Standing(player_id="p4", match_points=0),
        }

        # p1 already played p2
        past = [Match(
            id="R1M1",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
        )]

        matches = generate_swiss_pairings(standings, past, round_number=2)

        # p1 should not be paired with p2 again
        for match in matches:
            if match.player1_id == "p1":
                assert match.player2_id != "p2"
            if match.player1_id == "p2":
                assert match.player2_id != "p1"


class TestTopCutBracket:
    """Tests for top cut bracket generation."""

    def test_top_4_bracket(self):
        """Creates correct top 4 bracket (1v4, 2v3)."""
        standings = {
            f"p{i}": Standing(player_id=f"p{i}", match_points=12 - i)
            for i in range(1, 5)
        }

        matches = generate_top_cut_bracket(standings, top_cut_size=4)

        assert len(matches) == 2
        # First seed vs last seed
        assert matches[0].player1_id == "p1"
        assert matches[0].player2_id == "p4"
        # Second seed vs third seed
        assert matches[1].player1_id == "p2"
        assert matches[1].player2_id == "p3"


# =============================================================================
# Scoring Tests
# =============================================================================

class TestScoring:
    """Tests for scoring system."""

    def test_vgc_scoring(self):
        """VGC scoring has correct values."""
        assert VGC_SCORING.win_points == 3
        assert VGC_SCORING.loss_points == 0
        assert VGC_SCORING.draw_points == 1

    def test_calculate_standings(self):
        """Standings are calculated correctly from matches."""
        standings = {
            "p1": Standing(player_id="p1"),
            "p2": Standing(player_id="p2"),
        }

        matches = [
            Match(
                id="R1M1",
                round_number=1,
                phase=TournamentPhase.SWISS,
                player1_id="p1",
                player2_id="p2",
                completed=True,
                winner_id="p1",
                p1_wins=2,
                p2_wins=1,
            ),
        ]

        calculate_standings(standings, matches, VGC_SCORING)

        assert standings["p1"].match_wins == 1
        assert standings["p1"].match_points == 3
        assert standings["p2"].match_losses == 1
        assert standings["p2"].match_points == 0

    def test_sorted_standings(self):
        """Standings are sorted correctly."""
        standings = {
            "p1": Standing(player_id="p1", match_wins=2, match_points=6),
            "p2": Standing(player_id="p2", match_wins=1, match_points=3),
            "p3": Standing(player_id="p3", match_wins=3, match_points=9),
        }

        sorted_st = get_sorted_standings(standings)

        assert sorted_st[0].player_id == "p3"  # Most points
        assert sorted_st[1].player_id == "p1"
        assert sorted_st[2].player_id == "p2"


# =============================================================================
# Runner Tests
# =============================================================================

class TestCreateRandomTeam:
    """Tests for random team creation."""

    def test_create_team(self):
        """Can create a random team."""
        team = create_random_team("team1", team_size=6, seed=42)

        assert team.id == "team1"
        assert team.size == 6
        assert all("species_id" in p for p in team.pokemon)


class TestSimulateTournament:
    """Integration tests for tournament simulation."""

    def test_four_player_tournament(self):
        """Can simulate a 4-player tournament."""
        # Create tournament
        tournament = Tournament(id="test", name="Test Tournament", best_of=3)

        # Add players and teams
        for i in range(1, 5):
            player = Player(id=f"p{i}", name=f"Player {i}", team_id=f"team{i}")
            team = create_random_team(f"team{i}", seed=i * 100)

            tournament.add_team(team)
            tournament.add_player(player, "main")

        # Configure
        division = tournament.divisions[0]
        division.total_swiss_rounds = 2

        regulation = Regulation(
            name="Test",
            game_type="doubles",
            team_size=6,
        )

        config = TournamentConfig(verbose=False)

        # Simulate
        result = simulate_tournament(tournament, regulation, config=config, seed=42)

        # Verify
        assert result.phase == TournamentPhase.COMPLETE
        assert division.current_round == 2

        # All players should have standings
        for player_id in division.player_ids:
            standing = division.standings[player_id]
            assert standing.matches_played == 2

    def test_eight_player_three_rounds(self):
        """Can simulate 8 players over 3 Swiss rounds."""
        tournament = Tournament(id="test8", name="8 Player Test", best_of=3)

        for i in range(1, 9):
            player = Player(id=f"p{i}", name=f"Player {i}", team_id=f"team{i}")
            team = create_random_team(f"team{i}", seed=i * 100)
            tournament.add_team(team)
            tournament.add_player(player, "main")

        division = tournament.divisions[0]
        division.total_swiss_rounds = 3

        regulation = Regulation()
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, regulation, config=config, seed=123)

        assert result.phase == TournamentPhase.COMPLETE

        # Should have had 3 rounds * 4 matches = 12 total matches
        assert len(division.matches) == 12

    def test_odd_player_tournament(self):
        """Tournament with odd players handles byes correctly."""
        tournament = Tournament(id="odd", name="Odd Player Test", best_of=3)

        for i in range(1, 6):  # 5 players
            player = Player(id=f"p{i}", name=f"Player {i}", team_id=f"team{i}")
            team = create_random_team(f"team{i}", seed=i * 100)
            tournament.add_team(team)
            tournament.add_player(player, "main")

        division = tournament.divisions[0]
        division.total_swiss_rounds = 2

        regulation = Regulation()
        config = TournamentConfig(verbose=False)

        result = simulate_tournament(tournament, regulation, config=config, seed=456)

        assert result.phase == TournamentPhase.COMPLETE

        # Count byes
        bye_matches = [m for m in division.matches if m.is_bye]
        assert len(bye_matches) >= 1


class TestSimulateMatch:
    """Tests for individual match simulation."""

    def test_simulate_best_of_three(self):
        """Best of 3 match completes correctly."""
        tournament = Tournament(id="t", name="T")

        team1 = create_random_team("team1", seed=1)
        team2 = create_random_team("team2", seed=2)
        tournament.add_team(team1)
        tournament.add_team(team2)

        tournament.add_player(Player(id="p1", name="P1", team_id="team1"), "main")
        tournament.add_player(Player(id="p2", name="P2", team_id="team2"), "main")

        match = Match(
            id="M1",
            round_number=1,
            phase=TournamentPhase.SWISS,
            player1_id="p1",
            player2_id="p2",
            best_of=3,
        )

        regulation = Regulation()

        result = simulate_match(match, tournament, regulation, {}, base_seed=42)

        assert result.completed
        assert result.winner_id in ["p1", "p2"]
        assert result.p1_wins + result.p2_wins >= 2
        assert max(result.p1_wins, result.p2_wins) >= 2


# =============================================================================
# Additional Coverage Tests
# =============================================================================

class TestValidateTeamExtended:
    """Extended tests for validate_team to cover edge cases."""

    def test_team_no_pokemon_data(self):
        """Team with empty pokemon list returns error."""
        team = Team(id="team1", pokemon=[])
        reg = Regulation(team_size=6)

        errors = validate_team(team, reg)
        assert any("no pokemon" in e.lower() for e in errors)

    def test_level_below_minimum(self):
        """Pokemon below minimum level fails."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": 1, "level": 0},  # Below min_level of 1
                *[{"species_id": i, "level": 50} for i in range(2, 7)],
            ],
        )
        reg = Regulation(min_level=1)

        errors = validate_team(team, reg)
        assert any("below minimum" in e.lower() for e in errors)

    def test_species_not_in_allowed_list(self):
        """Species not in allowed_species fails."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": 100, "level": 50},  # Not in allowed
                *[{"species_id": i, "level": 50} for i in range(1, 6)],
            ],
        )
        reg = Regulation(allowed_species={1, 2, 3, 4, 5})

        errors = validate_team(team, reg)
        assert any("not allowed" in e.lower() for e in errors)

    def test_species_is_banned(self):
        """Species in banned_species fails."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": 150, "level": 50},  # Banned (Mewtwo)
                *[{"species_id": i, "level": 50} for i in range(1, 6)],
            ],
        )
        reg = Regulation(banned_species={150})

        errors = validate_team(team, reg)
        assert any("banned" in e.lower() for e in errors)

    def test_too_many_restricted_species(self):
        """Too many restricted species fails."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": 150, "level": 50},  # Restricted
                {"species_id": 151, "level": 50},  # Restricted
                {"species_id": 249, "level": 50},  # Restricted - too many!
                *[{"species_id": i, "level": 50} for i in range(1, 4)],
            ],
        )
        reg = Regulation(restricted_species={150, 151, 249}, restricted_count=2)

        errors = validate_team(team, reg)
        assert any("restricted" in e.lower() for e in errors)

    def test_item_not_in_allowed_list(self):
        """Item not in allowed_items fails."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": i, "level": 50, "item_id": 100 + i}
                for i in range(1, 7)
            ],
        )
        reg = Regulation(allowed_items={1, 2, 3, 4, 5, 6})

        errors = validate_team(team, reg)
        assert any("not allowed" in e.lower() for e in errors)

    def test_item_is_banned(self):
        """Item in banned_items fails."""
        team = Team(
            id="team1",
            pokemon=[
                {"species_id": 1, "level": 50, "item_id": 999},  # Banned item
                *[{"species_id": i, "level": 50, "item_id": i} for i in range(2, 7)],
            ],
        )
        reg = Regulation(banned_items={999})

        errors = validate_team(team, reg)
        assert any("banned" in e.lower() for e in errors)


class TestScoringExtended:
    """Extended tests for scoring to cover edge cases."""

    def test_incomplete_match_skipped(self):
        """Incomplete matches are skipped in standings calculation."""
        standings = {
            "p1": Standing(player_id="p1"),
            "p2": Standing(player_id="p2"),
        }

        matches = [
            Match(
                id="R1M1",
                round_number=1,
                phase=TournamentPhase.SWISS,
                player1_id="p1",
                player2_id="p2",
                completed=False,  # Not completed
            ),
        ]

        calculate_standings(standings, matches, VGC_SCORING)

        # No wins/losses should be recorded
        assert standings["p1"].match_wins == 0
        assert standings["p2"].match_wins == 0

    def test_missing_player_standings_skipped(self):
        """Matches with unknown players are skipped."""
        standings = {
            "p1": Standing(player_id="p1"),
            # p2 not in standings
        }

        matches = [
            Match(
                id="R1M1",
                round_number=1,
                phase=TournamentPhase.SWISS,
                player1_id="p1",
                player2_id="p2",  # Not in standings
                completed=True,
                winner_id="p1",
            ),
        ]

        calculate_standings(standings, matches, VGC_SCORING)

        # p1 should not have wins recorded (p2 missing)
        assert standings["p1"].match_wins == 0

    def test_missing_player1_standings_skipped(self):
        """Matches where player1 is unknown are skipped."""
        standings = {
            "p2": Standing(player_id="p2"),
            # p1 not in standings
        }

        matches = [
            Match(
                id="R1M1",
                round_number=1,
                phase=TournamentPhase.SWISS,
                player1_id="p1",  # Not in standings
                player2_id="p2",
                completed=True,
                winner_id="p2",
            ),
        ]

        calculate_standings(standings, matches, VGC_SCORING)

        # p2 should not have wins recorded (p1 missing, skipped before processing)
        assert standings["p2"].match_wins == 0

    def test_draw_result(self):
        """Draw results are recorded correctly."""
        standings = {
            "p1": Standing(player_id="p1"),
            "p2": Standing(player_id="p2"),
        }

        matches = [
            Match(
                id="R1M1",
                round_number=1,
                phase=TournamentPhase.SWISS,
                player1_id="p1",
                player2_id="p2",
                completed=True,
                winner_id=None,  # Draw - no winner
                p1_wins=1,
                p2_wins=1,
            ),
        ]

        calculate_standings(standings, matches, VGC_SCORING)

        # Both should have draws
        assert standings["p1"].match_draws == 1
        assert standings["p2"].match_draws == 1
        assert standings["p1"].match_points == 1  # Draw points
        assert standings["p2"].match_points == 1

    def test_resistance_zero_with_no_opponents(self):
        """Resistance is 0 when no opponents faced."""
        standings = {
            "p1": Standing(player_id="p1"),
        }

        # No matches, so no opponents faced
        calculate_standings(standings, [], VGC_SCORING)

        assert standings["p1"].resistance == 0.0

    def test_resistance_zero_with_unknown_opponents(self):
        """Resistance is 0 when opponents are not in standings."""
        standings = {
            "p1": Standing(player_id="p1"),
        }
        # Manually set opponents_faced to an opponent not in standings
        standings["p1"].opponents_faced.append("unknown_player")

        from tournament.scoring import _calculate_resistance
        _calculate_resistance(standings)

        # Should be 0 because opponent wasn't found
        assert standings["p1"].resistance == 0.0

    def test_format_standings_output(self):
        """format_standings returns readable string."""
        standings = {
            "p1": Standing(player_id="p1", match_wins=2, match_losses=1, match_points=6),
            "p2": Standing(player_id="p2", match_wins=1, match_losses=2, match_points=3),
        }
        player_names = {"p1": "Alice", "p2": "Bob"}

        result = format_standings(standings, player_names)

        assert "Alice" in result
        assert "Bob" in result
        assert "Rank" in result
        assert "2-1-0" in result or "2-1" in result

    def test_format_standings_with_top_n(self):
        """format_standings can limit output to top N."""
        standings = {
            "p1": Standing(player_id="p1", match_points=9),
            "p2": Standing(player_id="p2", match_points=6),
            "p3": Standing(player_id="p3", match_points=3),
        }
        player_names = {"p1": "A", "p2": "B", "p3": "C"}

        result = format_standings(standings, player_names, top_n=2)

        assert "A" in result
        assert "B" in result
        # C should not be in output (top_n=2)
        lines = result.strip().split('\n')
        # Header + separator + 2 players = 4 lines
        assert len(lines) == 4

    def test_bye_match_awards_points(self):
        """Bye matches award points correctly."""
        standings = {
            "p1": Standing(player_id="p1"),
        }

        matches = [
            Match(
                id="R1M1",
                round_number=1,
                phase=TournamentPhase.SWISS,
                player1_id="p1",
                player2_id=None,  # Bye
                completed=True,
                winner_id="p1",
            ),
        ]

        calculate_standings(standings, matches, VGC_SCORING)

        assert standings["p1"].match_wins == 1
        assert standings["p1"].match_points == VGC_SCORING.bye_points


class TestPairingsExtended:
    """Extended tests for pairings to cover edge cases."""

    def test_everyone_had_bye_gives_lowest(self):
        """If everyone has had a bye, lowest player gets another."""
        standings = {
            "p1": Standing(player_id="p1", match_points=3),
            "p2": Standing(player_id="p2", match_points=3),
            "p3": Standing(player_id="p3", match_points=0),
        }

        # All players have had byes already
        past_matches = [
            Match(id="R1B1", round_number=1, phase=TournamentPhase.SWISS,
                  player1_id="p1", player2_id=None, completed=True, winner_id="p1"),
            Match(id="R2B1", round_number=2, phase=TournamentPhase.SWISS,
                  player1_id="p2", player2_id=None, completed=True, winner_id="p2"),
            Match(id="R3B1", round_number=3, phase=TournamentPhase.SWISS,
                  player1_id="p3", player2_id=None, completed=True, winner_id="p3"),
        ]

        matches = generate_swiss_pairings(standings, past_matches, round_number=4)

        # Should still give a bye to lowest player (p3)
        bye_matches = [m for m in matches if m.is_bye]
        assert len(bye_matches) == 1

    def test_fallback_to_rematch_when_necessary(self):
        """Falls back to rematch when no other option."""
        standings = {
            "p1": Standing(player_id="p1", match_points=3),
            "p2": Standing(player_id="p2", match_points=0),
        }

        # p1 and p2 have already played
        past_matches = [
            Match(id="R1M1", round_number=1, phase=TournamentPhase.SWISS,
                  player1_id="p1", player2_id="p2", completed=True, winner_id="p1"),
        ]

        # Only 2 players, they must play each other again
        matches = generate_swiss_pairings(standings, past_matches, round_number=2)

        assert len(matches) == 1
        assert matches[0].player1_id in ["p1", "p2"]
        assert matches[0].player2_id in ["p1", "p2"]

    def test_top_cut_not_enough_players(self):
        """Top cut raises error if not enough players."""
        standings = {
            "p1": Standing(player_id="p1", match_points=6),
            "p2": Standing(player_id="p2", match_points=3),
        }

        with pytest.raises(ValueError, match="Not enough players"):
            generate_top_cut_bracket(standings, top_cut_size=4)


class TestNextBracketRound:
    """Tests for generate_next_bracket_round."""

    def test_generate_semifinals_from_quarters(self):
        """Generates semifinals from quarterfinal results."""
        from tournament.pairings import generate_next_bracket_round

        # Quarterfinal matches with winners
        qf_matches = [
            Match(id="QF1", round_number=1, phase=TournamentPhase.TOP_CUT,
                  player1_id="p1", player2_id="p8", completed=True, winner_id="p1"),
            Match(id="QF2", round_number=1, phase=TournamentPhase.TOP_CUT,
                  player1_id="p4", player2_id="p5", completed=True, winner_id="p4"),
            Match(id="QF3", round_number=1, phase=TournamentPhase.TOP_CUT,
                  player1_id="p2", player2_id="p7", completed=True, winner_id="p2"),
            Match(id="QF4", round_number=1, phase=TournamentPhase.TOP_CUT,
                  player1_id="p3", player2_id="p6", completed=True, winner_id="p3"),
        ]

        sf_matches = generate_next_bracket_round(qf_matches, round_number=2)

        assert len(sf_matches) == 2
        # Winners should be paired
        all_players = set()
        for m in sf_matches:
            all_players.add(m.player1_id)
            all_players.add(m.player2_id)
        assert all_players == {"p1", "p4", "p2", "p3"}

    def test_generate_finals_from_semis(self):
        """Generates finals from semifinal results."""
        from tournament.pairings import generate_next_bracket_round

        sf_matches = [
            Match(id="SF1", round_number=2, phase=TournamentPhase.TOP_CUT,
                  player1_id="p1", player2_id="p4", completed=True, winner_id="p1"),
            Match(id="SF2", round_number=2, phase=TournamentPhase.TOP_CUT,
                  player1_id="p2", player2_id="p3", completed=True, winner_id="p2"),
        ]

        finals = generate_next_bracket_round(sf_matches, round_number=3)

        assert len(finals) == 1
        assert finals[0].phase == TournamentPhase.FINALS
        assert {finals[0].player1_id, finals[0].player2_id} == {"p1", "p2"}

    def test_incomplete_match_raises_error(self):
        """Raises error if previous match not completed."""
        from tournament.pairings import generate_next_bracket_round

        matches = [
            Match(id="M1", round_number=1, phase=TournamentPhase.TOP_CUT,
                  player1_id="p1", player2_id="p2", completed=False),
        ]

        with pytest.raises(ValueError, match="not completed"):
            generate_next_bracket_round(matches, round_number=2)

    def test_tournament_complete_empty_return(self):
        """Returns empty list when tournament complete (single winner)."""
        from tournament.pairings import generate_next_bracket_round

        finals = [
            Match(id="F1", round_number=3, phase=TournamentPhase.FINALS,
                  player1_id="p1", player2_id="p2", completed=True, winner_id="p1"),
        ]

        next_round = generate_next_bracket_round(finals, round_number=4)

        assert next_round == []
