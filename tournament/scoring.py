"""Tournament scoring and standings calculation.

Calculates standings, applies tiebreakers, and manages point systems.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from tournament.model import Match, MatchResult, Standing


@dataclass
class ScoringProfile:
    """Defines how matches are scored.

    Attributes:
        win_points: Points awarded for a match win
        loss_points: Points awarded for a match loss
        draw_points: Points awarded for a draw
        bye_points: Points awarded for a bye
        tiebreakers: List of tiebreaker functions in priority order
    """
    win_points: int = 3
    loss_points: int = 0
    draw_points: int = 1
    bye_points: int = 3  # Byes usually count as wins

    def __post_init__(self):
        """Set up default tiebreakers."""
        self.tiebreakers: List[Callable[[Standing], float]] = [
            lambda s: s.match_points,           # Primary: match points
            lambda s: s.resistance,             # Secondary: opponent win %
            lambda s: s.game_win_rate,          # Tertiary: game win %
            lambda s: s.game_wins - s.game_losses,  # Quaternary: game differential
        ]


# Common scoring profiles
VGC_SCORING = ScoringProfile(
    win_points=3,
    loss_points=0,
    draw_points=1,
    bye_points=3,
)

SWISS_SCORING = ScoringProfile(
    win_points=1,
    loss_points=0,
    draw_points=0,
    bye_points=1,
)


def calculate_standings(
    standings: Dict[str, Standing],
    matches: List[Match],
    scoring: ScoringProfile,
) -> Dict[str, Standing]:
    """Calculate standings from match results.

    Args:
        standings: Existing standings dict (will be modified)
        matches: List of completed matches
        scoring: Scoring profile to use

    Returns:
        Updated standings dict with ranks assigned
    """
    # Process each match
    for match in matches:
        if not match.completed:
            continue

        p1_standing = standings.get(match.player1_id)
        if p1_standing is None:
            continue

        if match.is_bye:
            # Handle bye
            p1_standing.match_wins += 1
            p1_standing.match_points += scoring.bye_points
            continue

        p2_standing = standings.get(match.player2_id)
        if p2_standing is None:
            continue

        # Determine results
        if match.winner_id == match.player1_id:
            p1_result = MatchResult.WIN
            p2_result = MatchResult.LOSS
        elif match.winner_id == match.player2_id:
            p1_result = MatchResult.LOSS
            p2_result = MatchResult.WIN
        else:
            p1_result = MatchResult.DRAW
            p2_result = MatchResult.DRAW

        # Record for player 1
        p1_standing.record_match(
            result=p1_result,
            opponent_id=match.player2_id,
            games_won=match.p1_wins,
            games_lost=match.p2_wins,
            win_points=scoring.win_points,
            loss_points=scoring.loss_points,
            draw_points=scoring.draw_points,
        )

        # Record for player 2
        p2_standing.record_match(
            result=p2_result,
            opponent_id=match.player1_id,
            games_won=match.p2_wins,
            games_lost=match.p1_wins,
            win_points=scoring.win_points,
            loss_points=scoring.loss_points,
            draw_points=scoring.draw_points,
        )

    # Calculate resistance (opponent win percentage)
    _calculate_resistance(standings)

    # Assign ranks using tiebreakers
    _assign_ranks(standings, scoring)

    return standings


def _calculate_resistance(standings: Dict[str, Standing]) -> None:
    """Calculate opponent match-win percentage for each player."""
    for player_id, standing in standings.items():
        if not standing.opponents_faced:
            standing.resistance = 0.0
            continue

        total_opponent_wins = 0
        total_opponent_matches = 0

        for opp_id in standing.opponents_faced:
            opp_standing = standings.get(opp_id)
            if opp_standing:
                # Use at least 25% win rate to avoid penalizing for weak opponents
                opp_win_rate = max(0.25, opp_standing.win_rate)
                total_opponent_wins += opp_standing.match_wins
                total_opponent_matches += opp_standing.matches_played

        if total_opponent_matches > 0:
            standing.resistance = total_opponent_wins / total_opponent_matches
        else:
            standing.resistance = 0.0


def _assign_ranks(
    standings: Dict[str, Standing],
    scoring: ScoringProfile,
) -> None:
    """Assign ranks to players using tiebreakers."""
    # Build sort key from tiebreakers
    def sort_key(player_id: str) -> Tuple:
        standing = standings[player_id]
        return tuple(tb(standing) for tb in scoring.tiebreakers)

    # Sort players
    sorted_players = sorted(
        standings.keys(),
        key=sort_key,
        reverse=True,  # Higher is better
    )

    # Assign ranks (handle ties)
    current_rank = 1
    prev_key = None

    for i, player_id in enumerate(sorted_players):
        player_key = sort_key(player_id)

        if prev_key is not None and player_key != prev_key:
            current_rank = i + 1

        standings[player_id].rank = current_rank
        prev_key = player_key


def get_sorted_standings(
    standings: Dict[str, Standing],
    scoring: Optional[ScoringProfile] = None,
) -> List[Standing]:
    """Get standings sorted by rank.

    Args:
        standings: Standings dict
        scoring: Scoring profile for tiebreakers (optional)

    Returns:
        List of Standing objects sorted by rank
    """
    if scoring is None:
        scoring = VGC_SCORING

    # Recalculate ranks if needed
    _calculate_resistance(standings)
    _assign_ranks(standings, scoring)

    return sorted(standings.values(), key=lambda s: s.rank)


def format_standings(
    standings: Dict[str, Standing],
    player_names: Dict[str, str],
    top_n: Optional[int] = None,
) -> str:
    """Format standings as a readable string.

    Args:
        standings: Standings dict
        player_names: Map from player ID to name
        top_n: Only show top N players (None = all)

    Returns:
        Formatted standings string
    """
    sorted_standings = get_sorted_standings(standings)

    if top_n is not None:
        sorted_standings = sorted_standings[:top_n]

    lines = []
    lines.append(f"{'Rank':<6}{'Player':<20}{'W-L-D':<10}{'Pts':<6}{'Res%':<8}")
    lines.append("-" * 50)

    for standing in sorted_standings:
        name = player_names.get(standing.player_id, standing.player_id)
        record = f"{standing.match_wins}-{standing.match_losses}-{standing.match_draws}"
        resistance = f"{standing.resistance * 100:.1f}%"

        lines.append(
            f"{standing.rank:<6}{name:<20}{record:<10}"
            f"{standing.match_points:<6}{resistance:<8}"
        )

    return "\n".join(lines)
