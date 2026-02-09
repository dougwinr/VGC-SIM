#!/usr/bin/env python3
"""Run World Championships 2025 (Tournament 399) simulation.

This script loads actual team data from Limitless VGC tournament 399
and simulates battles between the top players.

Usage:
    python scripts/run_tournament_399.py [OPTIONS]

Options:
    --top N          Number of top players to include (default: 8)
    --rounds N       Number of Swiss rounds (default: 3)
    --best-of N      Games per match (default: 3)
    --seed N         Random seed (default: random)
    --quiet          Suppress verbose output
    --offline        Use offline fixture data instead of fetching from web
"""

import argparse
import random
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tournament import (
    Tournament,
    Division,
    Player,
    Team,
    Regulation,
    simulate_tournament,
    TournamentConfig,
)
from tournament.limitless_loader import (
    load_tournament_info,
    load_team,
    parse_tournament_page,
    parse_team_page,
    TournamentInfo,
)
from tournament.scoring import VGC_SCORING, format_standings
from agents import RandomAgent, HeuristicAgent
from data.species import get_species_id
from data.moves_loader import get_move_id
from data.items import get_item_id
from data.abilities import get_ability_id


def convert_pokemon_to_ids(pokemon_data: dict) -> dict:
    """Convert Pokemon data from names to IDs for the battle engine.

    Args:
        pokemon_data: Dict with species, moves, item, ability as strings

    Returns:
        Dict with species_id, moves (as IDs), item_id, ability_id
    """
    result = {}

    # Convert species name to ID
    species_name = pokemon_data.get("species", "")
    species_id = get_species_id(species_name)
    if species_id is None:
        # Try some variations
        for variant in [species_name.replace(" ", ""), species_name.replace("-", "")]:
            species_id = get_species_id(variant)
            if species_id:
                break

    if species_id is None:
        print(f"    Warning: Unknown species '{species_name}', using Pikachu")
        species_id = 25  # Default to Pikachu

    result["species_id"] = species_id
    result["name"] = species_name
    result["level"] = 50

    # Convert moves
    move_ids = []
    for move_name in pokemon_data.get("moves", []):
        move_id = get_move_id(move_name)
        if move_id is None:
            # Try variations
            for variant in [move_name.replace(" ", ""), move_name.replace("-", "")]:
                move_id = get_move_id(variant)
                if move_id:
                    break
        if move_id is not None:
            move_ids.append(move_id)

    # Ensure we have 4 moves (pad with Tackle if needed)
    while len(move_ids) < 4:
        move_ids.append(33)  # Tackle
    result["moves"] = move_ids[:4]

    # Convert item
    item_name = pokemon_data.get("item")
    if item_name:
        item_id = get_item_id(item_name)
        if item_id is not None:
            result["item_id"] = item_id

    # Convert ability
    ability_name = pokemon_data.get("ability")
    if ability_name:
        ability_id = get_ability_id(ability_name)
        if ability_id is not None:
            result["ability_id"] = ability_id

    return result

# Path to test fixtures for offline mode
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"


def load_tournament_399_offline() -> TournamentInfo:
    """Load tournament 399 from offline fixture."""
    fixture_path = FIXTURES_DIR / "tournament_399.html"
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Offline fixture not found: {fixture_path}\n"
            "Run without --offline to fetch from web."
        )
    html = fixture_path.read_text(encoding="utf-8")
    return parse_tournament_page(html, 399)


def load_team_offline(team_id: int):
    """Load team from offline fixture."""
    fixture_path = FIXTURES_DIR / f"team_{team_id}.html"
    if not fixture_path.exists():
        return None
    html = fixture_path.read_text(encoding="utf-8")
    return parse_team_page(html, team_id)


def main():
    parser = argparse.ArgumentParser(
        description="Run World Championships 2025 (Tournament 399) simulation"
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=8,
        help="Number of top players to include (default: 8)"
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
        "--offline",
        action="store_true",
        help="Use offline fixture data instead of fetching from web"
    )
    parser.add_argument(
        "--heuristic",
        action="store_true",
        help="Use heuristic agents instead of random"
    )

    args = parser.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 2**31)
    rng = random.Random(seed)

    print("=" * 60)
    print("  WORLD CHAMPIONSHIPS 2025 (Tournament 399)")
    print("=" * 60)
    print(f"  Top Players: {args.top}")
    print(f"  Swiss Rounds: {args.rounds}")
    print(f"  Best of: {args.best_of}")
    print(f"  Seed: {seed}")
    print(f"  Mode: {'Offline' if args.offline else 'Online'}")
    print("=" * 60)
    print()

    # Load tournament data
    print("Loading tournament data...")
    try:
        if args.offline:
            info = load_tournament_399_offline()
        else:
            info = load_tournament_info(399)
    except Exception as e:
        print(f"Error loading tournament: {e}")
        return 1

    print(f"Tournament: {info.name}")
    print(f"Players in tournament: {info.player_count}")
    print(f"Standings loaded: {len(info.standings)}")
    print()

    # Limit to top N players
    top_standings = info.standings[:args.top]

    if len(top_standings) < args.top:
        print(f"Warning: Only {len(top_standings)} standings available")
        if len(top_standings) < 2:
            print("Error: Need at least 2 players to run tournament")
            return 1

    # Create tournament
    tournament = Tournament(
        id="wc2025",
        name="World Championships 2025 Simulation",
        best_of=args.best_of,
        metadata={
            "source": "limitlessvgc.com",
            "original_tournament_id": 399,
        }
    )

    # Load teams and add players
    print("Loading teams...")
    agents = {}

    for i, standing in enumerate(top_standings):
        player_id = f"p{i + 1}"
        team_id = f"team{i + 1}"

        # Try to load detailed team data
        team_pokemon = []
        if args.offline:
            team_data = load_team_offline(standing.team_id)
        else:
            try:
                team_data = load_team(standing.team_id) if standing.team_id else None
                import time
                time.sleep(0.5)  # Be nice to the server
            except Exception as e:
                print(f"  Warning: Could not load team {standing.team_id}: {e}")
                team_data = None

        if team_data and team_data.pokemon:
            for poke in team_data.pokemon:
                pokemon_dict = {
                    "species": poke.species,
                    "item": poke.item,
                    "ability": poke.ability,
                    "tera_type": poke.tera_type,
                    "moves": poke.moves,
                }
                # Convert to IDs for battle engine
                converted = convert_pokemon_to_ids(pokemon_dict)
                team_pokemon.append(converted)
            print(f"  {standing.rank}. {standing.name} - Team loaded ({len(team_data.pokemon)} Pokemon)")
        else:
            # Fall back to basic Pokemon names - need to convert to IDs
            for name in standing.pokemon_names:
                converted = convert_pokemon_to_ids({"species": name, "moves": []})
                team_pokemon.append(converted)
            print(f"  {standing.rank}. {standing.name} - Basic team ({len(standing.pokemon_names)} Pokemon)")

        # Create team
        team = Team(
            id=team_id,
            name=f"{standing.name}'s Team",
            pokemon=team_pokemon,
            metadata={
                "original_rank": standing.rank,
                "limitless_team_id": standing.team_id,
                "country": standing.country,
            }
        )
        tournament.add_team(team)

        # Create player
        player = Player(
            id=player_id,
            name=standing.name,
            team_id=team_id,
            metadata={
                "original_rank": standing.rank,
                "country": standing.country,
            }
        )
        tournament.add_player(player, "main")

        # Create agent
        if args.heuristic:
            agents[player_id] = HeuristicAgent(name=standing.name, seed=seed + i)
        else:
            agents[player_id] = RandomAgent(name=standing.name, seed=seed + i)

    print()

    # Configure division
    division = tournament.divisions[0]
    division.total_swiss_rounds = args.rounds

    # Create regulation (VGC 2025 rules)
    regulation = Regulation(
        name="VGC 2025 Rules",
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
    print("Starting tournament simulation...\n")
    result = simulate_tournament(tournament, regulation, agents, config, seed)

    # Print final results
    print("\n" + "=" * 60)
    print("  SIMULATION FINAL STANDINGS")
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
    print(f"Simulation Winner: {winner.name}!")

    # Compare with original ranking
    original_winner = top_standings[0].name
    print(f"Original Tournament Winner: {original_winner}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
