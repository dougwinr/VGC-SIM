"""Tournament simulation runner.

Simulates matches and entire tournaments using the battle engine.
"""

import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from tournament.model import (
    Division,
    Match,
    Player,
    Standing,
    Team,
    Tournament,
    TournamentPhase,
)
from tournament.regulation import Regulation, validate_team
from tournament.pairings import generate_swiss_pairings, generate_top_cut_bracket
from tournament.scoring import ScoringProfile, VGC_SCORING, calculate_standings

from core.battle_state import BattleState
from core.battle import BattleEngine, Choice
from core.layout import (
    P_SPECIES, P_LEVEL, P_STAT_HP, P_CURRENT_HP,
    P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_TYPE1, P_TYPE2, P_MOVE1, P_PP1,
)
from data.moves_loader import MOVE_REGISTRY, get_move
from data.species import get_species, SPECIES_REGISTRY
from agents import Agent, RandomAgent, HeuristicAgent, Action, ActionKind


@dataclass
class TournamentConfig:
    """Configuration for tournament simulation.

    Attributes:
        scoring: Scoring profile for match points
        default_agent_class: Default AI agent class for players
        max_turns_per_game: Maximum turns before game is declared draw
        verbose: Print progress during simulation
    """
    scoring: ScoringProfile = field(default_factory=lambda: VGC_SCORING)
    default_agent_class: Type[Agent] = RandomAgent
    max_turns_per_game: int = 100
    verbose: bool = True


def simulate_game(
    team1: Team,
    team2: Team,
    regulation: Regulation,
    agent1: Agent,
    agent2: Agent,
    seed: int,
    max_turns: int = 100,
) -> Tuple[Optional[int], int]:
    """Simulate a single game between two teams.

    Args:
        team1: First player's team
        team2: Second player's team
        regulation: Tournament regulation rules
        agent1: Agent controlling team 1
        agent2: Agent controlling team 2
        seed: Random seed for battle
        max_turns: Maximum turns before draw

    Returns:
        Tuple of (winner_side, turns). winner_side is 0, 1, or None for draw.
    """
    # Create battle state
    active_slots = 1 if regulation.game_type == "singles" else 2

    state = BattleState(
        num_sides=2,
        team_size=regulation.team_size,
        active_slots=active_slots,
        seed=seed,
        game_type=regulation.game_type,
    )

    # Set up teams
    _setup_team_on_state(state, 0, team1, regulation)
    _setup_team_on_state(state, 1, team2, regulation)

    # Create engine
    engine = BattleEngine(state, MOVE_REGISTRY)
    state.start_battle()

    # Run battle
    agents = {0: agent1, 1: agent2}

    for turn in range(max_turns):
        if engine.ended:
            break

        # Get choices from agents
        choices = {}
        for side, agent in agents.items():
            side_choices = []
            for active_slot in range(state.active_slots):
                team_slot = state.active[side, active_slot]
                if team_slot < 0:
                    continue

                pokemon = state.get_pokemon(side, team_slot)
                if pokemon.is_fainted:
                    continue

                obs = state.get_observation(side)
                legal = _get_legal_actions(state, side, active_slot)

                if legal:
                    action = agent.act(obs, legal, {"side": side})
                    choice = _action_to_choice(action, side)
                    side_choices.append(choice)

            choices[side] = side_choices

        engine.step(choices)
        _handle_forced_switches(state, engine)

    return engine.winner, state.turn


def _setup_team_on_state(
    state: BattleState,
    side: int,
    team: Team,
    regulation: Regulation,
) -> None:
    """Set up a team on the battle state."""
    rng = random.Random(abs(hash(team.id)) % (2**31))

    for slot, poke_data in enumerate(team.pokemon[:state.team_size]):
        pokemon = state.pokemons[side, slot]

        species_id = poke_data.get("species_id", 1)
        species = get_species(species_id)

        pokemon[P_SPECIES] = species_id
        pokemon[P_LEVEL] = min(poke_data.get("level", 50), regulation.level_cap)

        # Stats
        if species and species.base_stats:
            base = species.base_stats
            pokemon[P_STAT_HP] = base.hp + 60
            pokemon[P_CURRENT_HP] = base.hp + 60
            pokemon[P_STAT_ATK] = base.atk + 30
            pokemon[P_STAT_DEF] = base.defense + 30
            pokemon[P_STAT_SPA] = base.spa + 30
            pokemon[P_STAT_SPD] = base.spd + 30
            pokemon[P_STAT_SPE] = base.spe + 30
        else:
            pokemon[P_STAT_HP] = 100
            pokemon[P_CURRENT_HP] = 100
            pokemon[P_STAT_ATK] = 80
            pokemon[P_STAT_DEF] = 80
            pokemon[P_STAT_SPA] = 80
            pokemon[P_STAT_SPD] = 80
            pokemon[P_STAT_SPE] = 80

        # Types
        if species and species.types:
            pokemon[P_TYPE1] = species.types[0].value if hasattr(species.types[0], 'value') else int(species.types[0])
            pokemon[P_TYPE2] = species.types[1].value if len(species.types) > 1 else 0
        else:
            pokemon[P_TYPE1] = 1
            pokemon[P_TYPE2] = 0

        # Moves
        moves = poke_data.get("moves", [])
        if not moves:
            # Generate random moves
            available_moves = [m for m, mv in MOVE_REGISTRY.items() if 0 < mv.base_power < 200]
            if len(available_moves) >= 4:
                moves = rng.sample(available_moves, 4)
            else:
                moves = [89, 53, 57, 85]

        for i, move_id in enumerate(moves[:4]):
            move = get_move(move_id)
            pokemon[P_MOVE1 + i] = move_id
            pokemon[P_PP1 + i] = move.pp if move else 10


def _get_legal_actions(state: BattleState, side: int, active_slot: int) -> List[Action]:
    """Get legal actions for an active slot."""
    team_slot = state.active[side, active_slot]
    if team_slot < 0:
        return [Action.pass_action(active_slot)]

    pokemon = state.get_pokemon(side, team_slot)
    if pokemon.is_fainted:
        return [Action.pass_action(active_slot)]

    actions = []

    # Moves
    for move_slot in range(4):
        move_id = pokemon.get_move(move_slot)
        if move_id == 0:
            continue
        pp = state.pokemons[side, team_slot, P_PP1 + move_slot]
        if pp <= 0:
            continue

        if state.active_slots == 1:
            actions.append(Action.move(active_slot, move_slot))
        else:
            for target_slot in range(state.active_slots):
                opp_side = 1 - side
                opp_team_slot = state.active[opp_side, target_slot]
                if opp_team_slot >= 0:
                    opp = state.get_pokemon(opp_side, opp_team_slot)
                    if not opp.is_fainted:
                        actions.append(Action.move(active_slot, move_slot, opp_side, target_slot))

    # Switches
    for bench_slot in range(state.team_size):
        if bench_slot in state.active[side]:
            continue
        bench = state.get_pokemon(side, bench_slot)
        if not bench.is_fainted and bench.max_hp > 0:
            actions.append(Action.switch(active_slot, bench_slot))

    if not actions:
        actions.append(Action.pass_action(active_slot))

    return actions


def _action_to_choice(action: Action, player_side: int) -> Choice:
    """Convert Action to Choice."""
    if action.kind == ActionKind.MOVE:
        target = 0
        if action.target_side >= 0 and action.target_slot >= 0:
            if action.target_side == player_side:
                target = -(action.target_slot + 1)
            else:
                target = action.target_slot + 1

        return Choice(
            choice_type='move',
            slot=action.slot,
            move_slot=action.arg,
            target=target,
        )
    elif action.kind == ActionKind.SWITCH:
        return Choice(
            choice_type='switch',
            slot=action.slot,
            switch_to=action.arg,
        )
    else:
        return Choice(choice_type='pass', slot=action.slot)


def _handle_forced_switches(state: BattleState, engine: BattleEngine) -> None:
    """Handle forced switches after faints."""
    while True:
        if engine.check_victory() is not None:
            return

        forced = engine.get_forced_switches()
        if not forced:
            break

        for side, active_slot in forced:
            available = []
            for team_slot in range(state.team_size):
                pokemon = state.get_pokemon(side, team_slot)
                if (pokemon.max_hp > 0 and
                    not pokemon.is_fainted and
                    not state.is_pokemon_active(side, team_slot)):
                    available.append(team_slot)

            if not available:
                if (side, active_slot) in engine._pending_switches:
                    engine._pending_switches.remove((side, active_slot))
                continue

            engine.apply_forced_switch(side, active_slot, available[0])


def simulate_match(
    match: Match,
    tournament: Tournament,
    regulation: Regulation,
    agents: Dict[str, Agent],
    base_seed: int,
    max_turns: int = 100,
) -> Match:
    """Simulate a match between two players.

    Args:
        match: Match to simulate
        tournament: Tournament context
        regulation: Tournament regulation
        agents: Map from player ID to agent
        base_seed: Base random seed
        max_turns: Max turns per game

    Returns:
        Updated Match object with results
    """
    if match.is_bye:
        match.completed = True
        match.winner_id = match.player1_id
        match.p1_wins = match.games_needed_to_win
        return match

    # Get teams
    team1 = tournament.get_player_team(match.player1_id)
    team2 = tournament.get_player_team(match.player2_id)

    if team1 is None or team2 is None:
        raise ValueError(f"Missing team for match {match.id}")

    # Get or create agents
    agent1 = agents.get(match.player1_id)
    agent2 = agents.get(match.player2_id)

    if agent1 is None:
        agent1 = RandomAgent(seed=abs(hash(match.player1_id)) % (2**31))
    if agent2 is None:
        agent2 = RandomAgent(seed=abs(hash(match.player2_id)) % (2**31))

    # Play games until someone wins the series
    game_num = 0
    while not match.completed:
        game_seed = base_seed + match.round_number * 1000 + game_num

        winner_side, turns = simulate_game(
            team1, team2, regulation,
            agent1, agent2, game_seed, max_turns
        )

        if winner_side == 0:
            match.record_game(match.player1_id)
        elif winner_side == 1:
            match.record_game(match.player2_id)
        else:
            # Draw - flip coin
            rng = random.Random(game_seed)
            if rng.random() < 0.5:
                match.record_game(match.player1_id)
            else:
                match.record_game(match.player2_id)

        game_num += 1

        # Safety limit
        if game_num > match.best_of * 2:
            match.completed = True
            if match.p1_wins > match.p2_wins:
                match.winner_id = match.player1_id
            elif match.p2_wins > match.p1_wins:
                match.winner_id = match.player2_id

    return match


def simulate_tournament(
    tournament: Tournament,
    regulation: Regulation,
    agents: Optional[Dict[str, Agent]] = None,
    config: Optional[TournamentConfig] = None,
    seed: int = 42,
) -> Tournament:
    """Simulate an entire tournament.

    Args:
        tournament: Tournament to simulate
        regulation: Tournament regulation
        agents: Map from player ID to agent (optional)
        config: Tournament configuration (optional)
        seed: Random seed

    Returns:
        Tournament with completed results
    """
    if config is None:
        config = TournamentConfig()

    if agents is None:
        agents = {}

    # Create default agents for players without one
    for player_id in tournament.players:
        if player_id not in agents:
            # Use abs() to ensure positive seed (hash can be negative)
            player_seed = abs(hash(player_id) + seed) % (2**31)
            agents[player_id] = config.default_agent_class(
                name=player_id,
                seed=player_seed,
            )

    rng = random.Random(seed)
    tournament.start()

    # Simulate each division
    for division in tournament.divisions:
        if config.verbose:
            print(f"\n=== Division: {division.name} ===")
            print(f"Players: {len(division.player_ids)}")
            print(f"Swiss Rounds: {division.total_swiss_rounds}")

        # Swiss rounds
        for round_num in range(1, division.total_swiss_rounds + 1):
            division.current_round = round_num

            if config.verbose:
                print(f"\n--- Round {round_num} ---")

            # Generate pairings
            matches = generate_swiss_pairings(
                division.standings,
                division.matches,
                round_num,
                tournament.best_of,
                rng,
            )

            # Simulate matches
            for match in matches:
                simulate_match(
                    match, tournament, regulation, agents,
                    seed + round_num * 1000,
                    config.max_turns_per_game,
                )
                division.matches.append(match)

                if config.verbose:
                    p1_name = tournament.players[match.player1_id].name
                    if match.is_bye:
                        print(f"  {p1_name} gets a bye")
                    else:
                        p2_name = tournament.players[match.player2_id].name
                        winner_name = tournament.players[match.winner_id].name
                        print(f"  {p1_name} vs {p2_name}: {match.p1_wins}-{match.p2_wins} ({winner_name} wins)")

            # Update standings
            calculate_standings(
                division.standings,
                matches,
                config.scoring,
            )

        # Print final standings
        if config.verbose:
            print("\n=== Final Standings ===")
            sorted_standings = sorted(
                division.standings.values(),
                key=lambda s: (s.match_points, s.resistance),
                reverse=True,
            )
            for i, standing in enumerate(sorted_standings, 1):
                player = tournament.players[standing.player_id]
                print(f"{i}. {player.name}: {standing.match_wins}-{standing.match_losses} ({standing.match_points} pts)")

    tournament.complete()
    return tournament


def create_random_team(team_id: str, team_size: int = 6, seed: int = 42) -> Team:
    """Create a random team for testing.

    Args:
        team_id: Team identifier
        team_size: Number of Pokemon
        seed: Random seed

    Returns:
        Team with random Pokemon
    """
    rng = random.Random(seed)

    # Get available species
    available_species = []
    for species_id, species in SPECIES_REGISTRY.items():
        try:
            hp = species.base_stats.hp if species.base_stats else 0
            if hp > 0 and hp < 300:
                available_species.append(species_id)
        except:
            pass

    # Get available moves
    available_moves = []
    for move_id, move in MOVE_REGISTRY.items():
        if move.base_power > 0 and move.base_power < 200:
            available_moves.append(move_id)

    # Build team
    pokemon = []
    if len(available_species) >= team_size:
        team_species = rng.sample(available_species, team_size)
    else:
        team_species = [1, 4, 7, 25, 94, 143][:team_size]

    for species_id in team_species:
        species = get_species(species_id)
        name = species.name if species else f"Pokemon#{species_id}"

        moves = []
        if len(available_moves) >= 4:
            moves = rng.sample(available_moves, 4)
        else:
            moves = [89, 53, 57, 85]

        pokemon.append({
            "name": name,
            "species_id": species_id,
            "level": 50,
            "moves": moves,
        })

    return Team(id=team_id, name=f"Team {team_id}", pokemon=pokemon)
