"""Tournament data models.

Dataclasses for representing tournaments, players, teams, matches, and standings.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from datetime import datetime


class TournamentPhase(Enum):
    """Phase of the tournament."""
    REGISTRATION = auto()
    SWISS = auto()
    TOP_CUT = auto()
    FINALS = auto()
    COMPLETE = auto()


class MatchResult(Enum):
    """Result of a match from player 1's perspective."""
    WIN = auto()
    LOSS = auto()
    DRAW = auto()
    NOT_PLAYED = auto()


@dataclass
class Team:
    """A player's team of Pokemon.

    Attributes:
        id: Unique team identifier
        name: Optional team name
        pokemon: List of Pokemon data (species IDs, moves, etc.)
        team_text: Optional Showdown-format team text
        metadata: Additional team data
    """
    id: str
    name: str = ""
    pokemon: List[Dict[str, Any]] = field(default_factory=list)
    team_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Number of Pokemon on the team."""
        return len(self.pokemon)


@dataclass
class Player:
    """A tournament participant.

    Attributes:
        id: Unique player identifier
        name: Player's display name
        team_id: ID of the player's registered team
        metadata: Additional player data (rating, country, etc.)
    """
    id: str
    name: str
    team_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Match:
    """A match between two players.

    Attributes:
        id: Unique match identifier
        round_number: Round this match belongs to
        phase: Tournament phase (Swiss, Top Cut, etc.)
        player1_id: First player's ID
        player2_id: Second player's ID (None for bye)
        p1_wins: Games won by player 1
        p2_wins: Games won by player 2
        best_of: Number of games in the series
        completed: Whether the match has been played
        winner_id: ID of the winning player (None for draw/not played)
        metadata: Additional match data (timestamps, game logs, etc.)
    """
    id: str
    round_number: int
    phase: TournamentPhase
    player1_id: str
    player2_id: Optional[str] = None  # None for bye
    p1_wins: int = 0
    p2_wins: int = 0
    best_of: int = 3
    completed: bool = False
    winner_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_bye(self) -> bool:
        """Check if this is a bye (no opponent)."""
        return self.player2_id is None

    @property
    def games_played(self) -> int:
        """Total games played in this match."""
        return self.p1_wins + self.p2_wins

    @property
    def games_needed_to_win(self) -> int:
        """Games needed to win the series."""
        return (self.best_of // 2) + 1

    def get_result(self, player_id: str) -> MatchResult:
        """Get the result from a specific player's perspective."""
        if not self.completed:
            return MatchResult.NOT_PLAYED

        if self.winner_id is None:
            return MatchResult.DRAW
        elif self.winner_id == player_id:
            return MatchResult.WIN
        else:
            return MatchResult.LOSS

    def record_game(self, winner_id: str) -> bool:
        """Record a game result. Returns True if match is now complete."""
        if winner_id == self.player1_id:
            self.p1_wins += 1
        elif winner_id == self.player2_id:
            self.p2_wins += 1
        else:
            raise ValueError(f"Invalid winner_id: {winner_id}")

        # Check if someone won the series
        if self.p1_wins >= self.games_needed_to_win:
            self.completed = True
            self.winner_id = self.player1_id
        elif self.p2_wins >= self.games_needed_to_win:
            self.completed = True
            self.winner_id = self.player2_id

        return self.completed


@dataclass
class Standing:
    """A player's standing in the tournament.

    Attributes:
        player_id: Player's ID
        match_wins: Number of matches won
        match_losses: Number of matches lost
        match_draws: Number of matches drawn
        game_wins: Total games won across all matches
        game_losses: Total games lost across all matches
        match_points: Points from match results
        opponents_faced: List of opponent IDs faced
        resistance: Opponent win percentage (tiebreaker)
        rank: Current rank in standings
    """
    player_id: str
    match_wins: int = 0
    match_losses: int = 0
    match_draws: int = 0
    game_wins: int = 0
    game_losses: int = 0
    match_points: int = 0
    opponents_faced: List[str] = field(default_factory=list)
    resistance: float = 0.0
    rank: int = 0

    @property
    def matches_played(self) -> int:
        """Total matches played."""
        return self.match_wins + self.match_losses + self.match_draws

    @property
    def win_rate(self) -> float:
        """Match win rate."""
        if self.matches_played == 0:
            return 0.0
        return self.match_wins / self.matches_played

    @property
    def game_win_rate(self) -> float:
        """Game win rate across all matches."""
        total = self.game_wins + self.game_losses
        if total == 0:
            return 0.0
        return self.game_wins / total

    def record_match(
        self,
        result: MatchResult,
        opponent_id: str,
        games_won: int,
        games_lost: int,
        win_points: int,
        loss_points: int,
        draw_points: int,
    ) -> None:
        """Record a match result."""
        self.opponents_faced.append(opponent_id)
        self.game_wins += games_won
        self.game_losses += games_lost

        if result == MatchResult.WIN:
            self.match_wins += 1
            self.match_points += win_points
        elif result == MatchResult.LOSS:
            self.match_losses += 1
            self.match_points += loss_points
        elif result == MatchResult.DRAW:
            self.match_draws += 1
            self.match_points += draw_points


@dataclass
class Division:
    """A division within a tournament (e.g., Masters, Seniors, Juniors).

    Attributes:
        id: Unique division identifier
        name: Division name
        player_ids: List of player IDs in this division
        matches: List of matches in this division
        standings: Current standings
        current_round: Current round number
        total_swiss_rounds: Total number of Swiss rounds
        top_cut_size: Number of players advancing to top cut (0 = no cut)
    """
    id: str
    name: str
    player_ids: List[str] = field(default_factory=list)
    matches: List[Match] = field(default_factory=list)
    standings: Dict[str, Standing] = field(default_factory=dict)
    current_round: int = 0
    total_swiss_rounds: int = 5
    top_cut_size: int = 0

    def add_player(self, player_id: str) -> None:
        """Add a player to the division."""
        if player_id not in self.player_ids:
            self.player_ids.append(player_id)
            self.standings[player_id] = Standing(player_id=player_id)

    def get_matches_for_round(self, round_number: int) -> List[Match]:
        """Get all matches for a specific round."""
        return [m for m in self.matches if m.round_number == round_number]

    def get_player_matches(self, player_id: str) -> List[Match]:
        """Get all matches for a specific player."""
        return [
            m for m in self.matches
            if m.player1_id == player_id or m.player2_id == player_id
        ]


@dataclass
class Tournament:
    """A Pokemon tournament.

    Attributes:
        id: Unique tournament identifier
        name: Tournament name
        divisions: List of divisions (usually just one for simple tournaments)
        players: Dict mapping player ID to Player
        teams: Dict mapping team ID to Team
        phase: Current tournament phase
        best_of: Default number of games per match
        metadata: Additional tournament data (date, location, format, etc.)
    """
    id: str
    name: str
    divisions: List[Division] = field(default_factory=list)
    players: Dict[str, Player] = field(default_factory=dict)
    teams: Dict[str, Team] = field(default_factory=dict)
    phase: TournamentPhase = TournamentPhase.REGISTRATION
    best_of: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_player(self, player: Player, division_id: str = "main") -> None:
        """Add a player to the tournament."""
        self.players[player.id] = player

        # Find or create division
        division = self.get_division(division_id)
        if division is None:
            division = Division(id=division_id, name=division_id.title())
            self.divisions.append(division)

        division.add_player(player.id)

    def add_team(self, team: Team) -> None:
        """Register a team."""
        self.teams[team.id] = team

    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID."""
        return self.players.get(player_id)

    def get_team(self, team_id: str) -> Optional[Team]:
        """Get a team by ID."""
        return self.teams.get(team_id)

    def get_division(self, division_id: str) -> Optional[Division]:
        """Get a division by ID."""
        for div in self.divisions:
            if div.id == division_id:
                return div
        return None

    def get_player_team(self, player_id: str) -> Optional[Team]:
        """Get a player's team."""
        player = self.get_player(player_id)
        if player and player.team_id:
            return self.get_team(player.team_id)
        return None

    @property
    def player_count(self) -> int:
        """Total number of players."""
        return len(self.players)

    def start(self) -> None:
        """Start the tournament (move from registration to Swiss)."""
        if self.phase != TournamentPhase.REGISTRATION:
            raise ValueError("Tournament already started")

        self.phase = TournamentPhase.SWISS

        # Initialize standings for all players
        for division in self.divisions:
            for player_id in division.player_ids:
                if player_id not in division.standings:
                    division.standings[player_id] = Standing(player_id=player_id)

    def complete(self) -> None:
        """Mark the tournament as complete."""
        self.phase = TournamentPhase.COMPLETE
