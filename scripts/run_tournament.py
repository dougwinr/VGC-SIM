#!/usr/bin/env python3
"""Run a sample Pokemon tournament.

Usage:
    python scripts/run_tournament.py [OPTIONS]

Options:
    --players N      Number of players (default: 8)
    --rounds N       Number of Swiss rounds (default: 3)
    --best-of N      Games per match (default: 3)
    --seed N         Random seed (default: random)
    --quiet          Suppress verbose output
"""

import argparse
import random
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tournament import (
    Tournament,
    Division,
    Player,
    Regulation,
    simulate_tournament,
    create_random_team,
    TournamentConfig,
)
from tournament.scoring import VGC_SCORING, format_standings
from agents import RandomAgent, HeuristicAgent


# Fun player names
PLAYER_NAMES = [
    "Ash", "Misty", "Brock", "Gary", "Lance", "Cynthia",
    "Red", "Blue", "Green", "Silver", "N", "Ghetsis",
    "Steven", "Wallace", "Leon", "Raihan", "Hop", "Marnie",
    "Nemona", "Arven", "Penny", "Geeta", "Rika", "Larry",
    "Iris", "Alder", "Diantha", "Malva", "Wikstrom", "Drasna",
    "Bruno", "Lorelei", "Agatha", "Karen", "Will", "Koga",
]


def main():
    parser = argparse.ArgumentParser(
        description="Run a Pokemon tournament simulation"
    )
    parser.add_argument(
        "--players", "-p",
        type=int,
        default=8,
        help="Number of players (default: 8)"
    )
    parser.add_argument(
        "--rounds", "-r",
        type=int,
        default=3,
        help="Number of Swiss rounds (default: 3)"
    )
    parser.add_argument(
        "--best-of", "-b",
        type=int,
        default=3,
        help="Games per match (default: 3)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )
    parser.add_argument(
        "--mixed-agents",
        action="store_true",
        help="Use mix of Random and Heuristic agents"
    )

    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 2**31)
    rng = random.Random(seed)

    print("=" * 60)
    print("  POKEMON TOURNAMENT SIMULATOR")
    print("=" * 60)
    print(f"  Players: {args.players}")
    print(f"  Swiss Rounds: {args.rounds}")
    print(f"  Best of: {args.best_of}")
    print(f"  Seed: {seed}")
    print("=" * 60)
    print()

    # Create tournament
    tournament = Tournament(
        id="tournament1",
        name="Pokemon Championship",
        best_of=args.best_of,
    )

    # Shuffle player names
    names = PLAYER_NAMES[:args.players] if args.players <= len(PLAYER_NAMES) else [
        f"Player {i}" for i in range(1, args.players + 1)
    ]
    rng.shuffle(names)

    # Add players and teams
    agents = {}
    for i, name in enumerate(names):
        player_id = f"p{i + 1}"
        team_id = f"team{i + 1}"

        # Create team
        team = create_random_team(team_id, seed=seed + i * 100)
        tournament.add_team(team)

        # Create player
        player = Player(id=player_id, name=name, team_id=team_id)
        tournament.add_player(player, "main")

        # Create agent
        if args.mixed_agents and i % 2 == 0:
            agents[player_id] = HeuristicAgent(name=name, seed=seed + i)
        else:
            agents[player_id] = RandomAgent(name=name, seed=seed + i)

    # Configure division
    division = tournament.divisions[0]
    division.total_swiss_rounds = args.rounds

    # Create regulation
    regulation = Regulation(
        name="Tournament Rules",
        game_type="doubles",
        team_size=6,
        level_cap=50,
        item_clause=True,
        species_clause=True,
    )

    # Configure simulation
    config = TournamentConfig(
        scoring=VGC_SCORING,
        verbose=not args.quiet,
        max_turns_per_game=100,
    )

    # Run tournament
    print("Starting tournament...\n")
    result = simulate_tournament(tournament, regulation, agents, config, seed)

    # Print final results
    print("\n" + "=" * 60)
    print("  FINAL STANDINGS")
    print("=" * 60)

    player_names = {p.id: p.name for p in tournament.players.values()}
    standings_str = format_standings(division.standings, player_names)
    print(standings_str)

    print()

    # Determine winner
    sorted_standings = sorted(
        division.standings.values(),
        key=lambda s: (s.match_points, s.resistance),
        reverse=True,
    )
    winner = tournament.players[sorted_standings[0].player_id]
    print(f"🏆 Tournament Winner: {winner.name}!")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
