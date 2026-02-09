"""Tournament pairing algorithms.

Implements Swiss pairing and other tournament pairing methods.
"""

import random
from typing import Dict, List, Optional, Set, Tuple

from tournament.model import Match, Standing, TournamentPhase


def generate_swiss_pairings(
    standings: Dict[str, Standing],
    past_matches: List[Match],
    round_number: int,
    best_of: int = 3,
    rng: Optional[random.Random] = None,
) -> List[Match]:
    """Generate Swiss pairings for the next round.

    Simple algorithm:
    1. Sort players by match points (descending)
    2. Pair adjacent players, avoiding rematches
    3. If odd number of players, lowest-ranked without a bye gets the bye

    Args:
        standings: Current standings for all players
        past_matches: All matches played so far
        round_number: Round number to generate pairings for
        best_of: Number of games per match
        rng: Random number generator for tiebreaking

    Returns:
        List of Match objects for the round
    """
    if rng is None:
        rng = random.Random()

    # Build set of past matchups to avoid
    past_opponents: Dict[str, Set[str]] = {}
    players_with_bye: Set[str] = set()

    for match in past_matches:
        p1, p2 = match.player1_id, match.player2_id

        if p1 not in past_opponents:
            past_opponents[p1] = set()

        if p2 is None:
            # This was a bye
            players_with_bye.add(p1)
        else:
            if p2 not in past_opponents:
                past_opponents[p2] = set()
            past_opponents[p1].add(p2)
            past_opponents[p2].add(p1)

    # Sort players by match points (with random tiebreak for equal points)
    sorted_players = sorted(
        standings.keys(),
        key=lambda p: (standings[p].match_points, rng.random()),
        reverse=True,
    )

    matches = []
    paired: Set[str] = set()
    match_id = 1

    # If odd number of players, assign bye to lowest player without one
    if len(sorted_players) % 2 == 1:
        # Find lowest player who hasn't had a bye
        for player_id in reversed(sorted_players):
            if player_id not in players_with_bye:
                bye_match = Match(
                    id=f"R{round_number}M{match_id}",
                    round_number=round_number,
                    phase=TournamentPhase.SWISS,
                    player1_id=player_id,
                    player2_id=None,  # Bye
                    best_of=best_of,
                    completed=True,
                    winner_id=player_id,  # Bye counts as win
                )
                matches.append(bye_match)
                paired.add(player_id)
                match_id += 1
                break
        else:
            # Everyone has had a bye, give it to lowest player
            player_id = sorted_players[-1]
            bye_match = Match(
                id=f"R{round_number}M{match_id}",
                round_number=round_number,
                phase=TournamentPhase.SWISS,
                player1_id=player_id,
                player2_id=None,
                best_of=best_of,
                completed=True,
                winner_id=player_id,
            )
            matches.append(bye_match)
            paired.add(player_id)
            match_id += 1

    # Pair remaining players
    for i, player1 in enumerate(sorted_players):
        if player1 in paired:
            continue

        # Find best opponent (closest in standings, not yet played)
        best_opponent = None
        for j in range(i + 1, len(sorted_players)):
            player2 = sorted_players[j]
            if player2 in paired:
                continue

            # Check if they've already played
            p1_opponents = past_opponents.get(player1, set())
            if player2 not in p1_opponents:
                best_opponent = player2
                break

        # If no valid opponent found (everyone already played), pair with closest
        if best_opponent is None:
            for j in range(i + 1, len(sorted_players)):
                player2 = sorted_players[j]
                if player2 not in paired:
                    best_opponent = player2
                    break

        if best_opponent is not None:
            match = Match(
                id=f"R{round_number}M{match_id}",
                round_number=round_number,
                phase=TournamentPhase.SWISS,
                player1_id=player1,
                player2_id=best_opponent,
                best_of=best_of,
            )
            matches.append(match)
            paired.add(player1)
            paired.add(best_opponent)
            match_id += 1

    return matches


def generate_top_cut_bracket(
    standings: Dict[str, Standing],
    top_cut_size: int,
    best_of: int = 3,
) -> List[Match]:
    """Generate single-elimination bracket for top cut.

    Args:
        standings: Current standings after Swiss
        top_cut_size: Number of players in top cut (4, 8, 16, etc.)
        best_of: Number of games per match

    Returns:
        List of Match objects for top cut round 1
    """
    # Sort by final standings
    sorted_players = sorted(
        standings.keys(),
        key=lambda p: (standings[p].match_points, standings[p].resistance),
        reverse=True,
    )

    # Take top N players
    top_players = sorted_players[:top_cut_size]

    if len(top_players) < top_cut_size:
        raise ValueError(
            f"Not enough players for top cut: {len(top_players)} < {top_cut_size}"
        )

    # Generate bracket pairings (1 vs N, 2 vs N-1, etc.)
    matches = []
    n = len(top_players)

    for i in range(n // 2):
        seed1 = i  # Higher seed
        seed2 = n - 1 - i  # Lower seed

        match = Match(
            id=f"TOP{n}M{i + 1}",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id=top_players[seed1],
            player2_id=top_players[seed2],
            best_of=best_of,
            metadata={"seed1": seed1 + 1, "seed2": seed2 + 1},
        )
        matches.append(match)

    return matches


def generate_next_bracket_round(
    previous_matches: List[Match],
    round_number: int,
    best_of: int = 3,
) -> List[Match]:
    """Generate next round of single-elimination bracket.

    Args:
        previous_matches: Matches from the previous round
        round_number: Round number for new matches
        best_of: Number of games per match

    Returns:
        List of Match objects for next round
    """
    # Get winners from previous round
    winners = []
    for match in previous_matches:
        if not match.completed or match.winner_id is None:
            raise ValueError(f"Match {match.id} not completed")
        winners.append(match.winner_id)

    if len(winners) < 2:
        return []  # Tournament complete

    # Pair winners in order
    matches = []
    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            match = Match(
                id=f"TOP{len(winners)}R{round_number}M{i // 2 + 1}",
                round_number=round_number,
                phase=TournamentPhase.TOP_CUT if len(winners) > 2 else TournamentPhase.FINALS,
                player1_id=winners[i],
                player2_id=winners[i + 1],
                best_of=best_of,
            )
            matches.append(match)

    return matches
