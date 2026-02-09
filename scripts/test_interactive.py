#!/usr/bin/env python3
"""Interactive test scenarios for manual testing.

Usage:
    python scripts/test_interactive.py [--scenario NAME] [--list]

Scenarios:
    basic       - Basic battle, verify moves and damage
    quick_win   - Fast battle to verify win condition
    forced      - Test forced switch after KO
    all_agents  - Play against different agent types
"""
import argparse
import sys
from typing import Optional

from cli.battle_cli import BattleCLI, create_opponent, get_pokemon_name
from agents import RandomAgent, HeuristicAgent, DefensiveAgent, TypeMatchupAgent
from core.layout import P_CURRENT_HP, P_STAT_HP


class TestScenario:
    """Base class for test scenarios."""

    name: str = "base"
    description: str = "Base scenario"

    def setup(self, cli: BattleCLI) -> None:
        """Set up the scenario (modify battle state if needed)."""
        pass

    def instructions(self) -> str:
        """Return instructions for the tester."""
        return "Follow the prompts and verify behavior."


class BasicBattleScenario(TestScenario):
    """Basic battle - verify moves deal damage."""

    name = "basic"
    description = "Basic battle to verify moves and damage"

    def instructions(self) -> str:
        return """
=== BASIC BATTLE TEST ===

Instructions:
1. Select a move (not a switch) for each Pokemon
2. Verify damage is dealt (opponent HP decreases)
3. Play 3-5 turns
4. Verify HP bars update correctly
5. Press 'q' to quit when done

Checklist:
[ ] Moves are listed with type and base power
[ ] Selecting a move works
[ ] Opponent HP decreases after your attack
[ ] Your HP may decrease from opponent's attack
[ ] Turn counter increases
"""


class QuickWinScenario(TestScenario):
    """Quick win - opponent starts with low HP."""

    name = "quick_win"
    description = "Quick battle to verify win condition"

    def setup(self, cli: BattleCLI) -> None:
        """Set opponent Pokemon to low HP."""
        for slot in range(cli.state.team_size):
            # Set opponent HP to 1
            cli.state.pokemons[1, slot, P_CURRENT_HP] = 1
        print("\n  [TEST] Opponent Pokemon set to 1 HP each\n")

    def instructions(self) -> str:
        return """
=== QUICK WIN TEST ===

Instructions:
1. Opponent Pokemon all have 1 HP
2. Use any attack to KO them
3. Verify forced switches happen
4. Continue until you win
5. Verify victory message appears

Checklist:
[ ] Attacks KO opponent Pokemon
[ ] "Opponent sends in X!" message appears
[ ] Battle ends when all opponents fainted
[ ] "YOU WIN!" message displayed
"""


class ForcedSwitchScenario(TestScenario):
    """Test forced switch mechanics."""

    name = "forced"
    description = "Test forced switch after KO"

    def setup(self, cli: BattleCLI) -> None:
        """Set one opponent Pokemon to 1 HP."""
        # Set first active opponent to 1 HP
        active_slot = cli.state.active[1, 0]
        cli.state.pokemons[1, active_slot, P_CURRENT_HP] = 1
        pokemon = cli.state.get_pokemon(1, active_slot)
        name = get_pokemon_name(pokemon.species_id)
        print(f"\n  [TEST] Opponent's {name} set to 1 HP\n")

    def instructions(self) -> str:
        return """
=== FORCED SWITCH TEST ===

Instructions:
1. One opponent Pokemon has 1 HP
2. KO it with an attack
3. Verify opponent sends in replacement
4. Verify you can still use moves after

Checklist:
[ ] Attack KOs the 1 HP Pokemon
[ ] "Opponent sends in X!" message
[ ] New Pokemon appears in active slot
[ ] You can use moves against new Pokemon
"""


class AllAgentsScenario(TestScenario):
    """Test against all agent types."""

    name = "all_agents"
    description = "Play against different AI types"

    def instructions(self) -> str:
        return """
=== ALL AGENTS TEST ===

This will run separate battles against each agent type.
Press 'q' to skip to next agent after testing.

Agents to test:
1. Random - Makes random moves
2. Heuristic - Uses simple scoring
3. Defensive - Prefers defensive plays
4. Type Matchup - Uses type effectiveness

For each, verify:
[ ] Battle starts correctly
[ ] AI makes valid moves
[ ] Battle can end with winner
"""


def run_scenario(scenario_name: str, seed: Optional[int] = None):
    """Run a specific test scenario."""
    scenarios = {
        "basic": BasicBattleScenario(),
        "quick_win": QuickWinScenario(),
        "forced": ForcedSwitchScenario(),
        "all_agents": AllAgentsScenario(),
    }

    if scenario_name not in scenarios:
        print(f"Unknown scenario: {scenario_name}")
        print(f"Available: {list(scenarios.keys())}")
        return

    scenario = scenarios[scenario_name]
    print(scenario.instructions())

    if scenario_name == "all_agents":
        # Special handling - run against each agent
        for agent_type in ["random", "heuristic", "defensive", "type"]:
            print(f"\n{'='*60}")
            print(f"  Testing against: {agent_type.upper()} agent")
            print(f"{'='*60}")

            input("Press Enter to start this battle...")

            opponent = create_opponent(agent_type, seed=seed or 42)
            cli = BattleCLI(
                opponent=opponent,
                game_type="doubles",
                seed=seed,
                use_color=True,
            )
            try:
                cli.run()
            except (KeyboardInterrupt, SystemExit):
                print("\n  Skipping to next agent...\n")
                continue
    else:
        # Normal scenario
        opponent = create_opponent("random", seed=seed or 42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=seed,
            use_color=True,
        )

        cli.setup_battle()
        scenario.setup(cli)
        cli.print_header()

        # Run battle loop
        max_turns = 100
        while not cli.engine.ended and cli.state.turn < max_turns:
            cli.print_battle_state()

            player_choices = cli.get_player_choices()
            opponent_choices = cli.get_opponent_choices()

            all_choices = {**player_choices, **opponent_choices}

            print()
            print(cli.fmt.dim("  Executing turn..."))

            cli.engine.step(all_choices)
            cli.handle_forced_switches()
            cli.print_turn_result()

            if cli.engine.ended:
                break

        cli.print_battle_state()
        cli.print_winner(cli.engine.winner)


def list_scenarios():
    """List all available test scenarios."""
    scenarios = {
        "basic": BasicBattleScenario(),
        "quick_win": QuickWinScenario(),
        "forced": ForcedSwitchScenario(),
        "all_agents": AllAgentsScenario(),
    }

    print("\nAvailable Test Scenarios:")
    print("=" * 50)
    for name, scenario in scenarios.items():
        print(f"  {name:15} - {scenario.description}")
    print()
    print("Usage: python scripts/test_interactive.py --scenario NAME")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive test scenarios for manual testing"
    )
    parser.add_argument(
        "--scenario", "-s",
        default="basic",
        help="Test scenario to run (default: basic)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available scenarios"
    )

    args = parser.parse_args()

    if args.list:
        list_scenarios()
        return

    try:
        run_scenario(args.scenario, args.seed)
    except KeyboardInterrupt:
        print("\n\nTest interrupted. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
