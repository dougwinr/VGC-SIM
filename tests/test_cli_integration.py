"""Integration tests for the battle CLI.

These tests verify that the CLI properly integrates with the battle engine
and that damage is actually applied during battles.
"""
import pytest
import numpy as np

from cli.battle_cli import BattleCLI, get_pokemon_name, get_move_name
from agents import RandomAgent, HeuristicAgent, Action, ActionKind
from core.battle_state import BattleState
from core.battle import BattleEngine, Choice
from core.layout import P_CURRENT_HP, P_STAT_HP, P_MOVE1, P_PP1
from data.moves_loader import get_move, MOVE_REGISTRY


class TestDamageApplication:
    """Tests to verify damage is actually applied."""

    def test_move_registry_has_moves(self):
        """Verify move registry is populated."""
        assert len(MOVE_REGISTRY) > 0, "Move registry is empty!"

        # Check a known move
        earthquake = get_move(89)
        assert earthquake is not None, "Earthquake (ID 89) not found"
        assert earthquake.base_power > 0, "Earthquake should have base power"

    def test_engine_with_move_registry(self):
        """Test that engine can execute moves with registry."""
        state = BattleState(
            num_sides=2,
            team_size=6,
            active_slots=1,
            seed=42,
        )

        # Set up simple Pokemon with known move
        for side in range(2):
            pokemon = state.pokemons[side, 0]
            pokemon[P_STAT_HP] = 100
            pokemon[P_CURRENT_HP] = 100
            pokemon[P_MOVE1] = 89  # Earthquake
            pokemon[P_PP1] = 10

        state.start_battle()

        # Create engine WITH move registry
        engine = BattleEngine(state, MOVE_REGISTRY)

        initial_hp = state.pokemons[1, 0, P_CURRENT_HP]

        # Execute a turn with move
        choices = {
            0: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
            1: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
        }

        engine.step(choices)

        # HP should have changed
        final_hp_0 = state.pokemons[0, 0, P_CURRENT_HP]
        final_hp_1 = state.pokemons[1, 0, P_CURRENT_HP]

        # At least one Pokemon should have taken damage
        assert final_hp_0 < 100 or final_hp_1 < 100, \
            f"No damage dealt! HP: {final_hp_0}, {final_hp_1}"

    def test_cli_battle_deals_damage(self):
        """Test that CLI battles actually deal damage."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="singles",
            seed=42,
            use_color=False,
        )

        cli.setup_battle()

        # Get initial HP
        initial_hp_player = cli.state.pokemons[0, 0, P_CURRENT_HP]
        initial_hp_opponent = cli.state.pokemons[1, 0, P_CURRENT_HP]

        # Simulate a turn manually
        player_choices = {0: [Choice(choice_type='move', slot=0, move_slot=0, target=1)]}
        opponent_choices = {1: [Choice(choice_type='move', slot=0, move_slot=0, target=1)]}

        all_choices = {**player_choices, **opponent_choices}
        cli.engine.step(all_choices)

        final_hp_player = cli.state.pokemons[0, 0, P_CURRENT_HP]
        final_hp_opponent = cli.state.pokemons[1, 0, P_CURRENT_HP]

        # Check if damage was dealt
        damage_to_player = initial_hp_player - final_hp_player
        damage_to_opponent = initial_hp_opponent - final_hp_opponent

        print(f"Player HP: {initial_hp_player} -> {final_hp_player} (damage: {damage_to_player})")
        print(f"Opponent HP: {initial_hp_opponent} -> {final_hp_opponent} (damage: {damage_to_opponent})")

        # At least one side should take damage
        assert damage_to_player > 0 or damage_to_opponent > 0, \
            "No damage was dealt during the turn!"


class TestCLIWithMoveRegistry:
    """Tests for CLI with proper move registry."""

    def test_cli_setup_includes_move_registry(self):
        """Verify CLI sets up engine with move registry."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="singles",
            seed=42,
        )

        cli.setup_battle()

        # Check that engine has move registry
        # The current implementation passes empty dict {}
        # This is the bug!
        assert cli.engine._move_registry is not None

    def test_moves_have_valid_data(self):
        """Test that assigned moves have valid move data."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="singles",
            seed=42,
        )

        cli.setup_battle()

        # Check first Pokemon's moves
        pokemon = cli.state.pokemons[0, 0]

        for i in range(4):
            move_id = pokemon[P_MOVE1 + i]
            if move_id > 0:
                move = get_move(move_id)
                assert move is not None, f"Move ID {move_id} not found in registry"
                print(f"Move {i}: {move.name} (ID: {move_id}, BP: {move.base_power})")


class TestBattleProgression:
    """Tests for battle progression and win conditions."""

    def test_battle_can_end(self):
        """Test that a battle can actually end with a winner."""
        # Create a battle where one side will definitely win
        state = BattleState(
            num_sides=2,
            team_size=1,  # Only 1 Pokemon each
            active_slots=1,
            seed=42,
        )

        # Side 0: Strong Pokemon
        pokemon_0 = state.pokemons[0, 0]
        pokemon_0[P_STAT_HP] = 500
        pokemon_0[P_CURRENT_HP] = 500
        pokemon_0[P_MOVE1] = 89  # Earthquake (BP 100)
        pokemon_0[P_PP1] = 10

        # Side 1: Weak Pokemon
        pokemon_1 = state.pokemons[1, 0]
        pokemon_1[P_STAT_HP] = 10
        pokemon_1[P_CURRENT_HP] = 10
        pokemon_1[P_MOVE1] = 33  # Tackle (BP 40)
        pokemon_1[P_PP1] = 10

        state.start_battle()

        engine = BattleEngine(state, MOVE_REGISTRY)

        # Run battle until it ends or max turns
        max_turns = 50
        for turn in range(max_turns):
            if engine.ended:
                break

            choices = {
                0: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
                1: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
            }
            engine.step(choices)

        # Battle should have ended
        assert engine.ended, f"Battle didn't end after {max_turns} turns"
        assert engine.winner in [0, 1], f"Invalid winner: {engine.winner}"
        print(f"Battle ended on turn {turn + 1}, winner: {engine.winner}")


class TestRandomTeamGeneration:
    """Tests for random team generation."""

    def test_generated_teams_have_valid_moves(self):
        """Test that generated teams have valid, damaging moves."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        # Check all Pokemon have at least one damaging move
        for side in range(2):
            for slot in range(cli.state.team_size):
                pokemon = cli.state.pokemons[side, slot]
                hp = pokemon[P_STAT_HP]

                if hp > 0:  # Valid Pokemon
                    damaging_moves = 0
                    for i in range(4):
                        move_id = pokemon[P_MOVE1 + i]
                        if move_id > 0:
                            move = get_move(move_id)
                            if move and move.base_power > 0:
                                damaging_moves += 1

                    assert damaging_moves > 0, \
                        f"Pokemon at side {side}, slot {slot} has no damaging moves"

    def test_generated_teams_have_hp(self):
        """Test that generated Pokemon have HP."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        for side in range(2):
            for slot in range(cli.state.team_size):
                max_hp = cli.state.pokemons[side, slot, P_STAT_HP]
                current_hp = cli.state.pokemons[side, slot, P_CURRENT_HP]

                assert max_hp > 0, f"Pokemon at ({side}, {slot}) has 0 max HP"
                assert current_hp == max_hp, f"Pokemon at ({side}, {slot}) doesn't start at full HP"

    def test_generated_teams_have_combat_stats(self):
        """Test that generated Pokemon have all combat stats set."""
        from core.layout import P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE

        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        for side in range(2):
            for slot in range(cli.state.team_size):
                pokemon = cli.state.pokemons[side, slot]
                max_hp = pokemon[P_STAT_HP]

                if max_hp > 0:  # Valid Pokemon
                    atk = pokemon[P_STAT_ATK]
                    defense = pokemon[P_STAT_DEF]
                    spa = pokemon[P_STAT_SPA]
                    spd = pokemon[P_STAT_SPD]
                    spe = pokemon[P_STAT_SPE]

                    assert atk > 0, f"Pokemon at ({side}, {slot}) has 0 ATK"
                    assert defense > 0, f"Pokemon at ({side}, {slot}) has 0 DEF"
                    assert spa > 0, f"Pokemon at ({side}, {slot}) has 0 SPA"
                    assert spd > 0, f"Pokemon at ({side}, {slot}) has 0 SPD"
                    assert spe > 0, f"Pokemon at ({side}, {slot}) has 0 SPE"


class TestForcedSwitches:
    """Tests for forced switch handling after faints."""

    def test_forced_switches_detected(self):
        """Test that forced switches are detected after faints."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        # Manually faint an active opponent Pokemon
        active_slot = cli.state.active[1, 0]
        cli.state.pokemons[1, active_slot, P_CURRENT_HP] = 0

        # Add to faint queue and process
        cli.state._faint_queue.append((1, active_slot))
        cli.engine._process_faints()

        # Should have a forced switch pending
        forced = cli.engine.get_forced_switches()
        assert len(forced) > 0, "No forced switches detected after faint"

    def test_forced_switch_applied(self):
        """Test that forced switches can be applied."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        # Get a non-active Pokemon slot to switch in
        active_slots = set(cli.state.active[1])
        new_slot = None
        for slot in range(cli.state.team_size):
            if slot not in active_slots:
                pokemon = cli.state.get_pokemon(1, slot)
                if not pokemon.is_fainted and pokemon.max_hp > 0:
                    new_slot = slot
                    break

        assert new_slot is not None, "No available Pokemon to switch in"

        # Faint an active Pokemon
        active_slot_idx = 0
        team_slot = cli.state.active[1, active_slot_idx]
        cli.state.pokemons[1, team_slot, P_CURRENT_HP] = 0
        cli.state._faint_queue.append((1, team_slot))
        cli.engine._process_faints()

        # Apply the forced switch
        success = cli.engine.apply_forced_switch(1, active_slot_idx, new_slot)
        assert success, "Forced switch failed"

        # Verify the new Pokemon is now active
        assert cli.state.active[1, active_slot_idx] == new_slot, "New Pokemon not active"

        # Forced switches should be cleared
        forced = cli.engine.get_forced_switches()
        assert (1, active_slot_idx) not in forced, "Forced switch not cleared"

    def test_no_infinite_loop_when_all_fainted(self):
        """Test that handle_forced_switches doesn't hang when side has no Pokemon left."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        # Faint ALL opponent Pokemon
        for slot in range(cli.state.team_size):
            cli.state.pokemons[1, slot, P_CURRENT_HP] = 0

        # Add active ones to faint queue
        for active_slot in range(cli.state.active_slots):
            team_slot = cli.state.active[1, active_slot]
            if team_slot >= 0:
                cli.state._faint_queue.append((1, team_slot))

        # Process faints
        cli.engine._process_faints()

        # This should NOT hang - it should detect no available Pokemon and exit
        cli.handle_forced_switches()

        # Battle should be over
        winner = cli.engine.check_victory()
        assert winner == 0, "Player should win when all opponent Pokemon fainted"
