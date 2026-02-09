"""Automated battles between different agent types.

These tests verify that battles complete correctly with various
agent combinations and formats.
"""
import pytest
import time
import random
from typing import Tuple, Optional, Callable

from agents import (
    RandomAgent, HeuristicAgent, DefensiveAgent, TypeMatchupAgent,
    Agent, Action,
)
from ai import BattleEnv, EnvConfig
from core.layout import (
    P_SPECIES, P_LEVEL, P_STAT_HP, P_CURRENT_HP,
    P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_TYPE1, P_TYPE2, P_MOVE1, P_PP1,
)
from data.moves_loader import MOVE_REGISTRY, get_move
from data.species import SPECIES_REGISTRY, get_species


def create_team_generator(seed: int) -> Callable[[int], None]:
    """Create a team generator function for BattleEnv.

    Args:
        seed: Random seed for team generation

    Returns:
        Function that generates teams given a side index
    """
    def generate_team(side: int) -> None:
        """Generate a random team for the given side."""
        # This is called by BattleEnv._set_team which expects
        # team data, but our version modifies state directly
        pass

    return generate_team


def setup_random_teams(state, seed: int) -> None:
    """Set up random teams on a BattleState.

    Args:
        state: BattleState to modify
        seed: Random seed
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

    # Get available damaging moves
    available_moves = []
    for move_id, move in MOVE_REGISTRY.items():
        if move.base_power > 0 and move.base_power < 200:
            available_moves.append(move_id)

    # Generate teams for both sides
    for side in range(2):
        # Sample species for team
        if len(available_species) >= 6:
            team_species_ids = rng.sample(available_species, 6)
        else:
            team_species_ids = [1, 4, 7, 25, 94, 143]

        for slot, species_id in enumerate(team_species_ids):
            pokemon = state.pokemons[side, slot]
            species = get_species(species_id)

            pokemon[P_SPECIES] = species_id
            pokemon[P_LEVEL] = 50

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
            if len(available_moves) >= 4:
                team_moves = rng.sample(available_moves, 4)
            else:
                team_moves = [89, 53, 57, 85]

            for i, move_id in enumerate(team_moves):
                move = get_move(move_id)
                pokemon[P_MOVE1 + i] = move_id
                pokemon[P_PP1 + i] = move.pp if move else 10


def create_agent(agent_type: str, seed: int = 42) -> Agent:
    """Factory function to create agents by type name."""
    agents = {
        "random": lambda: RandomAgent(name="Random", seed=seed),
        "heuristic": lambda: HeuristicAgent(name="Heuristic", seed=seed),
        "defensive": lambda: DefensiveAgent(name="Defensive", seed=seed),
        "type": lambda: TypeMatchupAgent(name="TypeMatchup", seed=seed),
    }
    return agents[agent_type]()


def run_battle(
    agent1: Agent,
    agent2: Agent,
    game_type: str = "doubles",
    seed: int = 42,
    max_turns: int = 100,
) -> Tuple[Optional[int], int]:
    """Run a battle between two agents.

    Returns:
        Tuple of (winner_side, num_turns). Winner is -1 for draw.
    """
    from core.battle_state import BattleState
    from core.battle import BattleEngine
    from data.moves_loader import MOVE_REGISTRY

    # Create battle state
    active_slots = 1 if game_type == "singles" else 2
    state = BattleState(
        num_sides=2,
        team_size=6,
        active_slots=active_slots,
        seed=seed,
        game_type=game_type,
    )

    # Set up random teams
    setup_random_teams(state, seed)

    # Create engine
    engine = BattleEngine(state, MOVE_REGISTRY)

    # Start battle
    state.start_battle()

    # Run battle loop
    for turn in range(max_turns):
        if engine.ended:
            break

        # Get choices from agents
        choices = {}
        for side, agent in [(0, agent1), (1, agent2)]:
            side_choices = []
            for active_slot in range(state.active_slots):
                team_slot = state.active[side, active_slot]
                if team_slot < 0:
                    continue

                pokemon = state.get_pokemon(side, team_slot)
                if pokemon.is_fainted:
                    continue

                # Get observation and legal actions
                obs = state.get_observation(side)
                legal = _get_legal_actions(state, side, active_slot)

                if legal:
                    action = agent.act(obs, legal, {"side": side})
                    choice = _action_to_choice(action, side)
                    side_choices.append(choice)

            choices[side] = side_choices

        # Execute turn
        engine.step(choices)

        # Handle forced switches
        _handle_forced_switches(state, engine)

    return engine.winner, state.turn


def _get_legal_actions(state, side: int, active_slot: int):
    """Get legal actions for an active slot."""
    from agents import Action

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
        pp = pokemon.get_pp(move_slot)
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


def _action_to_choice(action, player_side: int):
    """Convert Action to Choice."""
    from core.battle import Choice
    from agents import ActionKind

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


def _handle_forced_switches(state, engine):
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

            # Pick first available
            new_team_slot = available[0]
            engine.apply_forced_switch(side, active_slot, new_team_slot)


class TestAgentBattleCompletion:
    """Test that battles between agents complete without hanging."""

    @pytest.mark.parametrize("agent1_type,agent2_type", [
        ("random", "random"),
        ("random", "heuristic"),
        ("heuristic", "heuristic"),
        ("heuristic", "defensive"),
        ("defensive", "type"),
        ("random", "defensive"),
        ("random", "type"),
        ("heuristic", "type"),
        ("defensive", "defensive"),
        ("type", "type"),
    ])
    def test_battle_completes(self, agent1_type: str, agent2_type: str):
        """Test that battles between agent types complete."""
        agent1 = create_agent(agent1_type, seed=42)
        agent2 = create_agent(agent2_type, seed=43)

        winner, turns = run_battle(agent1, agent2, seed=42)

        # Battle should end within max turns
        assert turns <= 100, f"Battle took too long: {turns} turns"
        # Winner should be valid (-1 for draw, 0 or 1 for win)
        assert winner in [-1, 0, 1], f"Invalid winner: {winner}"

    @pytest.mark.parametrize("game_format", ["singles", "doubles"])
    def test_battle_formats(self, game_format: str):
        """Test both singles and doubles formats."""
        agent1 = RandomAgent(seed=42)
        agent2 = RandomAgent(seed=43)

        winner, turns = run_battle(agent1, agent2, game_type=game_format, seed=42)

        assert turns <= 100
        assert winner in [-1, 0, 1]

    @pytest.mark.parametrize("seed", [42, 123, 456, 789, 1000, 2024, 9999])
    def test_different_seeds(self, seed: int):
        """Test battles with different seeds."""
        agent1 = RandomAgent(seed=seed)
        agent2 = RandomAgent(seed=seed + 1)

        winner, turns = run_battle(agent1, agent2, seed=seed)

        assert turns <= 100
        assert winner in [-1, 0, 1]


class TestDeterministicReplay:
    """Test that battles are deterministic with same seed."""

    def test_same_seed_same_result(self):
        """Running battle twice with same seed gives same result."""
        results = []
        for _ in range(2):
            agent1 = RandomAgent(seed=42)
            agent2 = RandomAgent(seed=43)
            winner, turns = run_battle(agent1, agent2, seed=100)
            results.append((winner, turns))

        assert results[0] == results[1], "Battle not deterministic"

    def test_different_seeds_different_results(self):
        """Different seeds should (usually) give different results."""
        results = set()
        for seed in range(10):
            agent1 = RandomAgent(seed=seed)
            agent2 = RandomAgent(seed=seed + 100)
            winner, turns = run_battle(agent1, agent2, seed=seed)
            results.add((winner, turns))

        # Should have at least some variation
        assert len(results) > 1, "All battles had same result"


class TestBattleOutcomes:
    """Test expected battle outcomes."""

    def test_battle_has_winner(self):
        """Most battles should have a winner."""
        battles_with_winner = 0
        for seed in range(20):
            agent1 = RandomAgent(seed=seed)
            agent2 = RandomAgent(seed=seed + 100)
            winner, _ = run_battle(agent1, agent2, seed=seed)
            if winner in [0, 1]:
                battles_with_winner += 1

        # At least 80% should have winner
        assert battles_with_winner >= 16, "Too many battles without winner"

    def test_winner_is_valid_side(self):
        """Winner should always be side 0, 1, or -1 (draw)."""
        for seed in range(10):
            agent1 = RandomAgent(seed=seed)
            agent2 = HeuristicAgent(seed=seed + 100)
            winner, _ = run_battle(agent1, agent2, seed=seed)

            assert winner in [-1, 0, 1]


class TestAgentReset:
    """Test that agents reset correctly between battles."""

    def test_agent_reset_between_battles(self):
        """Agents should work correctly across multiple battles."""
        agent1 = HeuristicAgent(seed=42)
        agent2 = RandomAgent(seed=43)

        # Run multiple battles with same agents
        for seed in range(5):
            agent1.reset()
            agent2.reset()
            winner, turns = run_battle(agent1, agent2, seed=seed)
            assert turns <= 100


class TestBattleSpeed:
    """Basic performance tests."""

    def test_battle_completes_quickly(self):
        """A single battle should complete in reasonable time."""
        agent1 = RandomAgent(seed=42)
        agent2 = RandomAgent(seed=43)

        start = time.time()
        winner, turns = run_battle(agent1, agent2, seed=42)
        elapsed = time.time() - start

        # Should complete in under 5 seconds
        assert elapsed < 5.0, f"Battle too slow: {elapsed:.2f}s"

    def test_ten_battles_speed(self):
        """Ten battles should complete quickly."""
        start = time.time()
        for seed in range(10):
            agent1 = RandomAgent(seed=seed)
            agent2 = RandomAgent(seed=seed + 100)
            run_battle(agent1, agent2, seed=seed)
        elapsed = time.time() - start

        # Should average at least 2 battles/second
        assert elapsed < 5.0, f"Battles too slow: {elapsed:.2f}s for 10 battles"
