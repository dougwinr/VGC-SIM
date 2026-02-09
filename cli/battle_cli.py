#!/usr/bin/env python3
"""Friendly CLI for playing Pokemon battles.

Usage:
    python -m cli.battle_cli [OPTIONS]

Options:
    --opponent TYPE    Opponent type: random, heuristic, defensive (default: heuristic)
    --format FORMAT    Battle format: singles, doubles (default: doubles)
    --seed SEED        Random seed for reproducibility
    --no-color         Disable colored output
"""
import argparse
import sys
import random
from typing import Any, Dict, List, Optional, Tuple

from core.battle_state import BattleState, WEATHER_NAMES, TERRAIN_NAMES
from core.battle import BattleEngine, Choice
from core.layout import (
    P_SPECIES, P_LEVEL, P_CURRENT_HP, P_STAT_HP, P_STATUS,
    P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_MOVE1, P_PP1, P_TYPE1, P_TYPE2,
    STATUS_NONE, STATUS_BURN, STATUS_FREEZE, STATUS_PARALYSIS,
    STATUS_POISON, STATUS_BADLY_POISONED, STATUS_SLEEP,
)
from agents import (
    Agent, Action, ActionKind,
    RandomAgent, HeuristicAgent, TypeMatchupAgent, DefensiveAgent,
)
from data.moves import MoveData
from data.moves_loader import get_move, get_move_count, MOVE_REGISTRY
from data.species import SpeciesData
from data.species import get_species, get_species_count, SPECIES_REGISTRY
from data.types import Type


# =============================================================================
# Color and Formatting Utilities
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # Type colors
    TYPE_COLORS = {
        "normal": "\033[38;5;250m",
        "fire": "\033[38;5;208m",
        "water": "\033[38;5;39m",
        "grass": "\033[38;5;82m",
        "electric": "\033[38;5;226m",
        "ice": "\033[38;5;51m",
        "fighting": "\033[38;5;167m",
        "poison": "\033[38;5;129m",
        "ground": "\033[38;5;215m",
        "flying": "\033[38;5;147m",
        "psychic": "\033[38;5;205m",
        "bug": "\033[38;5;142m",
        "rock": "\033[38;5;137m",
        "ghost": "\033[38;5;99m",
        "dragon": "\033[38;5;63m",
        "dark": "\033[38;5;240m",
        "steel": "\033[38;5;249m",
        "fairy": "\033[38;5;218m",
    }


class Formatter:
    """Text formatting utilities."""

    def __init__(self, use_color: bool = True):
        self.use_color = use_color

    def color(self, text: str, color: str) -> str:
        """Apply color to text."""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def bold(self, text: str) -> str:
        """Make text bold."""
        return self.color(text, Colors.BOLD)

    def dim(self, text: str) -> str:
        """Make text dim."""
        return self.color(text, Colors.DIM)

    def type_color(self, type_name: str) -> str:
        """Get color for a Pokemon type."""
        color = Colors.TYPE_COLORS.get(type_name.lower(), Colors.WHITE)
        return self.color(type_name.upper(), color)

    def hp_bar(self, current: int, maximum: int, width: int = 20) -> str:
        """Create an HP bar visualization."""
        if maximum == 0:
            return "[" + "-" * width + "]"

        ratio = current / maximum
        filled = int(ratio * width)
        empty = width - filled

        if ratio > 0.5:
            color = Colors.GREEN
        elif ratio > 0.25:
            color = Colors.YELLOW
        else:
            color = Colors.RED

        bar = "█" * filled + "░" * empty
        if self.use_color:
            bar = f"{color}{bar}{Colors.RESET}"

        return f"[{bar}]"

    def status_text(self, status: int) -> str:
        """Format status condition."""
        status_map = {
            STATUS_NONE: "",
            STATUS_BURN: self.color("BRN", Colors.RED),
            STATUS_FREEZE: self.color("FRZ", Colors.CYAN),
            STATUS_PARALYSIS: self.color("PAR", Colors.YELLOW),
            STATUS_POISON: self.color("PSN", Colors.MAGENTA),
            STATUS_BADLY_POISONED: self.color("TOX", Colors.MAGENTA),
            STATUS_SLEEP: self.color("SLP", Colors.DIM),
        }
        return status_map.get(status, "")


# =============================================================================
# Pokemon Display
# =============================================================================

def get_pokemon_name(species_id: int) -> str:
    """Get Pokemon name from species ID."""
    try:
        species = get_species(species_id)
        if species:
            return species.name.title()
    except:
        pass
    return f"Pokemon#{species_id}"


def get_move_name(move_id: int) -> str:
    """Get move name from move ID."""
    if move_id == 0:
        return "---"
    try:
        move = get_move(move_id)
        if move:
            return move.name.replace("-", " ").title()
    except:
        pass
    return f"Move#{move_id}"


def get_move_info(move_id: int) -> Optional[MoveData]:
    """Get full move data."""
    if move_id == 0:
        return None
    try:
        return get_move(move_id)
    except:
        return None


# =============================================================================
# Battle CLI
# =============================================================================

class BattleCLI:
    """Interactive CLI for Pokemon battles."""

    def __init__(
        self,
        opponent: Agent,
        game_type: str = "doubles",
        seed: Optional[int] = None,
        use_color: bool = True,
        enable_tera: bool = True,
        enable_mega: bool = False,
        enable_zmoves: bool = False,
        enable_dynamax: bool = False,
    ):
        """Initialize the battle CLI.

        Args:
            opponent: AI opponent agent
            game_type: "singles" or "doubles"
            seed: Random seed
            use_color: Whether to use colored output
            enable_tera: Enable Terastallization mechanic
            enable_mega: Enable Mega Evolution mechanic
            enable_zmoves: Enable Z-Moves mechanic
            enable_dynamax: Enable Dynamax mechanic
        """
        self.opponent = opponent
        self.game_type = game_type
        self.seed = seed or random.randint(0, 2**31)
        self.fmt = Formatter(use_color)

        self.player_side = 0
        self.opponent_side = 1

        # Special mechanics settings
        self.enable_tera = enable_tera
        self.enable_mega = enable_mega
        self.enable_zmoves = enable_zmoves
        self.enable_dynamax = enable_dynamax

        # Track if mechanics have been used (once per battle per side)
        self.tera_used = {0: False, 1: False}
        self.mega_used = {0: False, 1: False}
        self.zmove_used = {0: False, 1: False}
        self.dynamax_used = {0: False, 1: False}

        self.state: Optional[BattleState] = None
        self.engine: Optional[BattleEngine] = None

    def setup_battle(self) -> None:
        """Initialize a new battle with random teams."""
        active_slots = 1 if self.game_type == "singles" else 2

        self.state = BattleState(
            num_sides=2,
            team_size=6,
            active_slots=active_slots,
            seed=self.seed,
            game_type=self.game_type,
        )

        # Generate random teams
        self._generate_random_team(0)
        self._generate_random_team(1)

        # Create engine with move registry for damage calculation
        self.engine = BattleEngine(self.state, MOVE_REGISTRY)

        # Start battle
        self.state.start_battle()

    def _generate_random_team(self, side: int) -> None:
        """Generate a random team for a side using real data."""
        rng = random.Random(self.seed + side)

        # Get available species (filter to reasonable ones)
        available_species = []
        for species_id, species in SPECIES_REGISTRY.items():
            # Skip forms, megas, etc. - just base species with reasonable stats
            try:
                hp = species.base_stats.hp if species.base_stats else 0
                if (hp > 0 and hp < 300 and
                    not any(x in species.name.lower() for x in ["mega", "gmax", "totem"])):
                    available_species.append(species_id)
            except:
                pass

        # Get available damaging moves
        available_moves = []
        for move_id, move in MOVE_REGISTRY.items():
            if move.base_power > 0 and move.base_power < 200:
                available_moves.append(move_id)

        # Sample team
        if len(available_species) >= 6:
            team_species_ids = rng.sample(available_species, 6)
        else:
            # Fallback to simple IDs
            team_species_ids = [1, 4, 7, 25, 94, 143]

        for slot, species_id in enumerate(team_species_ids):
            pokemon = self.state.pokemons[side, slot]
            species = get_species(species_id)

            # Basic stats
            pokemon[P_SPECIES] = species_id
            pokemon[P_LEVEL] = 50

            # Calculate stats from base stats
            # Simplified stat formula: base_stat + level + 5 (approximates real formula)
            if species and species.base_stats:
                base = species.base_stats
                # HP formula is different: base + level + 10
                calculated_hp = base.hp + 50 + 10
                # Other stats: base + level/2 + 5 (simplified)
                calculated_atk = base.atk + 25 + 5
                calculated_def = base.defense + 25 + 5
                calculated_spa = base.spa + 25 + 5
                calculated_spd = base.spd + 25 + 5
                calculated_spe = base.spe + 25 + 5
            else:
                calculated_hp = 100 + rng.randint(0, 50)
                calculated_atk = 80 + rng.randint(0, 40)
                calculated_def = 80 + rng.randint(0, 40)
                calculated_spa = 80 + rng.randint(0, 40)
                calculated_spd = 80 + rng.randint(0, 40)
                calculated_spe = 80 + rng.randint(0, 40)

            pokemon[P_STAT_HP] = calculated_hp
            pokemon[P_CURRENT_HP] = calculated_hp
            pokemon[P_STAT_ATK] = calculated_atk
            pokemon[P_STAT_DEF] = calculated_def
            pokemon[P_STAT_SPA] = calculated_spa
            pokemon[P_STAT_SPD] = calculated_spd
            pokemon[P_STAT_SPE] = calculated_spe

            # Set types from species data
            if species and species.types:
                pokemon[P_TYPE1] = species.types[0].value if hasattr(species.types[0], 'value') else int(species.types[0])
                pokemon[P_TYPE2] = species.types[1].value if len(species.types) > 1 and hasattr(species.types[1], 'value') else 0
            else:
                pokemon[P_TYPE1] = 1  # Normal
                pokemon[P_TYPE2] = 0

            # Assign random moves
            if len(available_moves) >= 4:
                team_moves = rng.sample(available_moves, 4)
            else:
                team_moves = [89, 53, 57, 85]  # Earthquake, Flamethrower, Surf, Thunderbolt

            for i, move_id in enumerate(team_moves):
                move = get_move(move_id)
                pokemon[P_MOVE1 + i] = move_id
                pokemon[P_PP1 + i] = move.pp if move else 10

    def print_header(self) -> None:
        """Print the battle header."""
        print()
        print(self.fmt.bold("=" * 60))
        print(self.fmt.bold(f"  POKEMON BATTLE - {self.game_type.upper()}"))
        print(self.fmt.bold("=" * 60))
        print(f"  Seed: {self.seed}")
        print(f"  Opponent: {self.opponent.name}")

        # Show enabled mechanics
        mechanics = []
        if self.enable_tera:
            mechanics.append("Tera")
        if self.enable_mega:
            mechanics.append("Mega")
        if self.enable_zmoves:
            mechanics.append("Z-Moves")
        if self.enable_dynamax:
            mechanics.append("Dynamax")
        if mechanics:
            print(f"  Mechanics: {', '.join(mechanics)}")

        print(self.fmt.bold("=" * 60))
        print()

    def print_field_conditions(self) -> None:
        """Print active field conditions."""
        conditions = []

        weather = self.state.weather
        if weather > 0:
            weather_name = WEATHER_NAMES.get(weather, "Unknown")
            conditions.append(f"Weather: {weather_name}")

        terrain = self.state.terrain
        if terrain > 0:
            terrain_name = TERRAIN_NAMES.get(terrain, "Unknown")
            conditions.append(f"Terrain: {terrain_name}")

        if self.state.trick_room:
            conditions.append("Trick Room")

        if conditions:
            print(self.fmt.dim(f"  Field: {', '.join(conditions)}"))
            print()

    def print_pokemon_status(self, side: int, slot: int, is_active: bool = False) -> str:
        """Format a Pokemon's status for display."""
        pokemon = self.state.get_pokemon(side, slot)

        if pokemon.max_hp == 0:
            return self.fmt.dim("  (empty)")

        name = get_pokemon_name(pokemon.species_id)
        hp = pokemon.current_hp
        max_hp = pokemon.max_hp

        # Fainted check
        if pokemon.is_fainted:
            return self.fmt.dim(f"  {name} - FAINTED")

        # HP bar
        hp_bar = self.fmt.hp_bar(hp, max_hp, width=15)
        hp_text = f"{hp}/{max_hp}"

        # Status
        status = self.fmt.status_text(pokemon.status)
        status_str = f" {status}" if status else ""

        # Active marker
        active_marker = self.fmt.color("*", Colors.GREEN) if is_active else " "

        return f"{active_marker} {name:12} {hp_bar} {hp_text:>7}{status_str}"

    def print_battle_state(self) -> None:
        """Print the current battle state."""
        print()
        print(self.fmt.bold(f"  Turn {self.state.turn}"))
        print(self.fmt.bold("-" * 50))

        self.print_field_conditions()

        # Opponent's side
        print(self.fmt.color("  OPPONENT", Colors.RED))
        active_opp = set(self.state.active[self.opponent_side])
        for slot in range(self.state.team_size):
            is_active = slot in active_opp
            print(self.print_pokemon_status(self.opponent_side, slot, is_active))

        print()
        print(self.fmt.dim("  " + "-" * 40))
        print()

        # Player's side
        print(self.fmt.color("  YOUR TEAM", Colors.GREEN))
        active_player = set(self.state.active[self.player_side])
        for slot in range(self.state.team_size):
            is_active = slot in active_player
            print(self.print_pokemon_status(self.player_side, slot, is_active))

        print()

    def get_legal_actions(self, active_slot: int) -> List[Tuple[Action, str]]:
        """Get legal actions for an active slot with descriptions."""
        team_slot = self.state.active[self.player_side, active_slot]
        if team_slot < 0:
            return [(Action.pass_action(active_slot), "Pass")]

        pokemon = self.state.get_pokemon(self.player_side, team_slot)
        if pokemon.is_fainted:
            return [(Action.pass_action(active_slot), "Pass (fainted)")]

        actions = []

        # Move actions
        for move_slot in range(4):
            move_id = pokemon.get_move(move_slot)
            if move_id == 0:
                continue

            pp = self.state.pokemons[self.player_side, team_slot, P_PP1 + move_slot]
            if pp <= 0:
                continue

            move_name = get_move_name(move_id)
            move_info = get_move_info(move_id)

            # Get type and power info
            type_str = ""
            power_str = ""
            if move_info:
                type_str = f" [{move_info.type.name}]"
                if move_info.base_power > 0:
                    power_str = f" (BP: {move_info.base_power})"

            if self.state.active_slots == 1:
                # Singles: just the move
                action = Action.move(active_slot, move_slot)
                desc = f"Use {move_name}{type_str}{power_str} (PP: {pp})"
                actions.append((action, desc))
            else:
                # Doubles: add targeting
                for target_slot in range(self.state.active_slots):
                    opp_team_slot = self.state.active[self.opponent_side, target_slot]
                    if opp_team_slot >= 0:
                        opp_pokemon = self.state.get_pokemon(self.opponent_side, opp_team_slot)
                        if not opp_pokemon.is_fainted:
                            target_name = get_pokemon_name(opp_pokemon.species_id)
                            action = Action.move(active_slot, move_slot, self.opponent_side, target_slot)
                            desc = f"Use {move_name}{type_str}{power_str} -> {target_name}"
                            actions.append((action, desc))

        # Switch actions
        for bench_slot in range(self.state.team_size):
            if bench_slot in self.state.active[self.player_side]:
                continue

            bench_pokemon = self.state.get_pokemon(self.player_side, bench_slot)
            if bench_pokemon.is_fainted or bench_pokemon.max_hp == 0:
                continue

            name = get_pokemon_name(bench_pokemon.species_id)
            hp = bench_pokemon.current_hp
            max_hp = bench_pokemon.max_hp

            action = Action.switch(active_slot, bench_slot)
            desc = f"Switch to {name} ({hp}/{max_hp} HP)"
            actions.append((action, desc))

        if not actions:
            actions.append((Action.pass_action(active_slot), "Pass (no valid actions)"))

        return actions

    def prompt_action(self, active_slot: int) -> Tuple[Action, Dict[str, bool]]:
        """Prompt the player to choose an action for an active slot.

        Returns:
            Tuple of (Action, mechanics_flags dict with terastallize, mega, zmove, dynamax)
        """
        team_slot = self.state.active[self.player_side, active_slot]
        if team_slot < 0:
            return Action.pass_action(active_slot), {}

        pokemon = self.state.get_pokemon(self.player_side, team_slot)
        pokemon_name = get_pokemon_name(pokemon.species_id)

        print()
        print(self.fmt.bold(f"  Choose action for {pokemon_name}:"))

        # Show available mechanics
        available_mechanics = []
        if self.enable_tera and not self.tera_used[self.player_side]:
            available_mechanics.append(self.fmt.color("[T]era", Colors.CYAN))
        if self.enable_mega and not self.mega_used[self.player_side]:
            available_mechanics.append(self.fmt.color("[M]ega", Colors.MAGENTA))
        if self.enable_zmoves and not self.zmove_used[self.player_side]:
            available_mechanics.append(self.fmt.color("[Z]-Move", Colors.YELLOW))
        if self.enable_dynamax and not self.dynamax_used[self.player_side]:
            available_mechanics.append(self.fmt.color("[D]ynamax", Colors.RED))

        if available_mechanics:
            print(f"  Available: {', '.join(available_mechanics)}")

        print()

        actions = self.get_legal_actions(active_slot)

        for i, (action, desc) in enumerate(actions):
            print(f"    {self.fmt.bold(str(i + 1))}. {desc}")

        print()

        while True:
            try:
                choice = input(self.fmt.color("  Enter choice (number): ", Colors.CYAN))
                choice = choice.strip()

                if choice.lower() in ('q', 'quit', 'exit'):
                    print("\n  Quitting battle...\n")
                    sys.exit(0)

                idx = int(choice) - 1
                if 0 <= idx < len(actions):
                    selected_action = actions[idx][0]
                    mechanics = {}

                    # If it's a move action, offer special mechanics
                    if selected_action.kind == ActionKind.MOVE and available_mechanics:
                        mechanics = self._prompt_mechanics(active_slot)

                    return selected_action, mechanics
                else:
                    print(self.fmt.color(f"  Please enter 1-{len(actions)}", Colors.RED))
            except ValueError:
                print(self.fmt.color("  Please enter a number", Colors.RED))
            except KeyboardInterrupt:
                print("\n\n  Quitting battle...\n")
                sys.exit(0)

    def _prompt_mechanics(self, active_slot: int) -> Dict[str, bool]:
        """Prompt player to activate special mechanics."""
        mechanics = {
            'terastallize': False,
            'mega': False,
            'zmove': False,
            'dynamax': False,
        }

        options = []
        if self.enable_tera and not self.tera_used[self.player_side]:
            options.append(('t', 'terastallize', 'Terastallize'))
        if self.enable_mega and not self.mega_used[self.player_side]:
            options.append(('m', 'mega', 'Mega Evolve'))
        if self.enable_zmoves and not self.zmove_used[self.player_side]:
            options.append(('z', 'zmove', 'Z-Move'))
        if self.enable_dynamax and not self.dynamax_used[self.player_side]:
            options.append(('d', 'dynamax', 'Dynamax'))

        if not options:
            return mechanics

        print()
        option_strs = [f"[{key.upper()}] {name}" for key, _, name in options]
        print(f"  Special mechanics: {', '.join(option_strs)}, or [Enter] to skip")

        try:
            choice = input(self.fmt.color("  Activate mechanic? ", Colors.CYAN)).strip().lower()

            if choice == '':
                return mechanics

            for key, mech_key, name in options:
                if choice == key:
                    mechanics[mech_key] = True
                    print(self.fmt.color(f"  {name} activated!", Colors.GREEN))
                    break

        except KeyboardInterrupt:
            pass

        return mechanics

    def get_player_choices(self) -> Dict[int, List[Choice]]:
        """Get all player choices for the turn."""
        choices = []

        for active_slot in range(self.state.active_slots):
            team_slot = self.state.active[self.player_side, active_slot]
            if team_slot < 0:
                continue

            pokemon = self.state.get_pokemon(self.player_side, team_slot)
            if pokemon.is_fainted:
                continue

            action, mechanics = self.prompt_action(active_slot)
            choice = self._action_to_choice(action, mechanics)

            # Track used mechanics
            if mechanics.get('terastallize'):
                self.tera_used[self.player_side] = True
            if mechanics.get('mega'):
                self.mega_used[self.player_side] = True
            if mechanics.get('zmove'):
                self.zmove_used[self.player_side] = True
            if mechanics.get('dynamax'):
                self.dynamax_used[self.player_side] = True

            choices.append(choice)

        return {self.player_side: choices}

    def get_opponent_choices(self) -> Dict[int, List[Choice]]:
        """Get opponent AI choices."""
        choices = []

        for active_slot in range(self.state.active_slots):
            team_slot = self.state.active[self.opponent_side, active_slot]
            if team_slot < 0:
                continue

            pokemon = self.state.get_pokemon(self.opponent_side, team_slot)
            if pokemon.is_fainted:
                continue

            # Get observation and legal actions
            obs = self.state.get_observation(self.opponent_side)
            legal = self._get_legal_actions_for_agent(self.opponent_side, active_slot)

            # Query opponent agent
            action = self.opponent.act(obs, legal, {"side": self.opponent_side})
            choice = self._action_to_choice(action)
            choices.append(choice)

        return {self.opponent_side: choices}

    def _get_legal_actions_for_agent(self, side: int, active_slot: int) -> List[Action]:
        """Get legal actions for the agent interface."""
        team_slot = self.state.active[side, active_slot]
        if team_slot < 0:
            return [Action.pass_action(active_slot)]

        pokemon = self.state.get_pokemon(side, team_slot)
        if pokemon.is_fainted:
            return [Action.pass_action(active_slot)]

        actions = []

        # Moves
        for move_slot in range(4):
            move_id = pokemon.get_move(move_slot)
            if move_id == 0:
                continue
            pp = self.state.pokemons[side, team_slot, P_PP1 + move_slot]
            if pp <= 0:
                continue

            if self.state.active_slots == 1:
                actions.append(Action.move(active_slot, move_slot))
            else:
                for target_slot in range(self.state.active_slots):
                    opp_side = 1 - side
                    opp_team_slot = self.state.active[opp_side, target_slot]
                    if opp_team_slot >= 0:
                        opp_pokemon = self.state.get_pokemon(opp_side, opp_team_slot)
                        if not opp_pokemon.is_fainted:
                            actions.append(Action.move(active_slot, move_slot, opp_side, target_slot))

        # Switches
        for bench_slot in range(self.state.team_size):
            if bench_slot in self.state.active[side]:
                continue
            bench_pokemon = self.state.get_pokemon(side, bench_slot)
            if not bench_pokemon.is_fainted and bench_pokemon.max_hp > 0:
                actions.append(Action.switch(active_slot, bench_slot))

        if not actions:
            actions.append(Action.pass_action(active_slot))

        return actions

    def _action_to_choice(self, action: Action, mechanics: Optional[Dict[str, bool]] = None) -> Choice:
        """Convert Action to Choice for the engine."""
        mechanics = mechanics or {}

        if action.kind == ActionKind.MOVE:
            target = 0
            if action.target_side >= 0 and action.target_slot >= 0:
                if action.target_side == self.player_side:
                    target = -(action.target_slot + 1)
                else:
                    target = action.target_slot + 1

            return Choice(
                choice_type='move',
                slot=action.slot,
                move_slot=action.arg,
                target=target,
                terastallize=mechanics.get('terastallize', False),
                mega=mechanics.get('mega', False),
                zmove=mechanics.get('zmove', False),
                dynamax=mechanics.get('dynamax', False),
            )
        elif action.kind == ActionKind.SWITCH:
            return Choice(
                choice_type='switch',
                slot=action.slot,
                switch_to=action.arg,
            )
        else:
            return Choice(choice_type='pass', slot=action.slot)

    def print_turn_result(self) -> None:
        """Print what happened during the turn."""
        # In a full implementation, we'd track and display events
        # For now, we just show the updated state
        pass

    def print_winner(self, winner: int) -> None:
        """Print the battle result."""
        print()
        print(self.fmt.bold("=" * 60))

        if winner == self.player_side:
            print(self.fmt.color("  YOU WIN!", Colors.GREEN + Colors.BOLD))
            print("  Congratulations!")
        elif winner == self.opponent_side:
            print(self.fmt.color("  YOU LOSE!", Colors.RED + Colors.BOLD))
            print(f"  {self.opponent.name} wins!")
        else:
            print(self.fmt.color("  DRAW!", Colors.YELLOW + Colors.BOLD))

        print(self.fmt.bold("=" * 60))
        print()

    def handle_forced_switches(self) -> None:
        """Handle any forced switches after faints."""
        while True:
            # Check if battle has ended (one side has no Pokemon left)
            if self.engine.check_victory() is not None:
                return

            forced = self.engine.get_forced_switches()
            if not forced:
                break

            for side, active_slot in forced:
                # Get available Pokemon to switch in
                available = []
                for team_slot in range(self.state.team_size):
                    pokemon = self.state.get_pokemon(side, team_slot)
                    if (pokemon.max_hp > 0 and
                        not pokemon.is_fainted and
                        not self.state.is_pokemon_active(side, team_slot)):
                        available.append(team_slot)

                if not available:
                    # No Pokemon available - side has lost, battle should end
                    # Clear the pending switch since it can't be fulfilled
                    if (side, active_slot) in self.engine._pending_switches:
                        self.engine._pending_switches.remove((side, active_slot))
                    continue

                if side == self.player_side:
                    # Player chooses replacement
                    print()
                    print(self.fmt.bold("  A Pokemon fainted! Choose a replacement:"))
                    print()

                    for i, team_slot in enumerate(available):
                        pokemon = self.state.get_pokemon(side, team_slot)
                        name = get_pokemon_name(pokemon.species_id)
                        hp = pokemon.current_hp
                        max_hp = pokemon.max_hp
                        print(f"    {self.fmt.bold(str(i + 1))}. {name} ({hp}/{max_hp} HP)")

                    print()

                    while True:
                        try:
                            choice = input(self.fmt.color("  Enter choice (number): ", Colors.CYAN))
                            idx = int(choice.strip()) - 1
                            if 0 <= idx < len(available):
                                new_team_slot = available[idx]
                                break
                            else:
                                print(self.fmt.color(f"  Please enter 1-{len(available)}", Colors.RED))
                        except ValueError:
                            print(self.fmt.color("  Please enter a number", Colors.RED))
                        except KeyboardInterrupt:
                            print("\n\n  Quitting battle...\n")
                            sys.exit(0)
                else:
                    # Opponent AI chooses replacement (pick first available)
                    new_team_slot = available[0]
                    pokemon = self.state.get_pokemon(side, new_team_slot)
                    name = get_pokemon_name(pokemon.species_id)
                    print(self.fmt.dim(f"  Opponent sends in {name}!"))

                self.engine.apply_forced_switch(side, active_slot, new_team_slot)

    def run(self) -> int:
        """Run the battle CLI.

        Returns:
            Winner side index (-1 for draw)
        """
        self.setup_battle()
        self.print_header()

        max_turns = 100

        while not self.engine.ended and self.state.turn < max_turns:
            self.print_battle_state()

            # Get choices
            player_choices = self.get_player_choices()
            opponent_choices = self.get_opponent_choices()

            # Merge choices
            all_choices = {**player_choices, **opponent_choices}

            # Execute turn
            print()
            print(self.fmt.dim("  Executing turn..."))

            self.engine.step(all_choices)

            # Handle any forced switches from faints
            self.handle_forced_switches()

            self.print_turn_result()

            # Check victory after forced switches
            if self.engine.ended:
                break

        # Final state
        self.print_battle_state()
        self.print_winner(self.engine.winner)

        return self.engine.winner


# =============================================================================
# Main Entry Point
# =============================================================================

def create_opponent(opponent_type: str, seed: int) -> Agent:
    """Create an opponent agent."""
    if opponent_type == "random":
        return RandomAgent(name="Random Bot", seed=seed)
    elif opponent_type == "defensive":
        return DefensiveAgent(name="Defensive Bot", seed=seed)
    elif opponent_type == "type":
        return TypeMatchupAgent(name="Type Expert Bot", seed=seed)
    else:  # heuristic (default)
        return HeuristicAgent(name="Heuristic Bot", seed=seed)


def main():
    """Main entry point for the battle CLI."""
    parser = argparse.ArgumentParser(
        description="Play a Pokemon battle against an AI opponent!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.battle_cli                     # Default: doubles vs heuristic bot
  python -m cli.battle_cli --format singles    # Singles battle
  python -m cli.battle_cli --opponent random   # Battle vs random bot
  python -m cli.battle_cli --seed 12345        # Set random seed

During battle:
  Enter the number of your chosen action
  Type 'q' or 'quit' to exit
        """
    )

    parser.add_argument(
        "--opponent", "-o",
        choices=["random", "heuristic", "defensive", "type"],
        default="heuristic",
        help="Opponent AI type (default: heuristic)"
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
