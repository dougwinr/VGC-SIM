#!/usr/bin/env python3
"""Quick launcher for Pokemon battle CLI.

Usage:
    python play.py [OPTIONS]

Play a Pokemon battle against a Random AI opponent.
For full options, run: python play.py --help
"""
import sys

from cli.battle_cli import BattleCLI, create_opponent
from agents import RandomAgent


def main():
    """Launch a battle against a RandomAgent."""
    import argparse
    import random

    parser = argparse.ArgumentParser(
        description="Play a Pokemon battle against an AI opponent!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python play.py                          # Default: doubles vs random bot
  python play.py --format singles         # Singles battle
  python play.py --opponent heuristic     # Battle vs smarter bot
  python play.py --seed 12345             # Set random seed

During battle:
  Enter the number of your chosen action
  Type 'q' or 'quit' to exit
        """
    )

    parser.add_argument(
        "--opponent", "-o",
        choices=["random", "heuristic", "defensive", "type"],
        default="random",
        help="Opponent AI type (default: random)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["singles", "doubles"],
        default="doubles",
        help="Battle format (default: doubles)"
    )

    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    # Special mechanics arguments
    parser.add_argument(
        "--tera", "--terastallize",
        action="store_true",
        default=True,
        help="Enable Terastallization (default: enabled)"
    )
    parser.add_argument(
        "--no-tera",
        action="store_true",
        help="Disable Terastallization"
    )
    parser.add_argument(
        "--mega",
        action="store_true",
        help="Enable Mega Evolution"
    )
    parser.add_argument(
        "--zmoves", "--z-moves",
        action="store_true",
        help="Enable Z-Moves"
    )
    parser.add_argument(
        "--dynamax",
        action="store_true",
        help="Enable Dynamax/Gigantamax"
    )

    args = parser.parse_args()

    # Set seed
    seed = args.seed if args.seed is not None else random.randint(0, 2**31)

    # Create opponent
    opponent = create_opponent(args.opponent, seed + 1000)

    # Create and run CLI
    cli = BattleCLI(
        opponent=opponent,
        game_type=args.format,
        seed=seed,
        use_color=not args.no_color,
        enable_tera=not args.no_tera,
        enable_mega=args.mega,
        enable_zmoves=args.zmoves,
        enable_dynamax=args.dynamax,
    )

    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\n  Battle interrupted. Goodbye!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
