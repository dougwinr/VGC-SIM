"""Tests for the Battle Engine.

Comprehensive tests covering:
- Action sorting (priority, speed, random tie-break)
- Move execution (damage, accuracy, PP)
- Target resolution
- Protection mechanics
- Switch handling
- Faint processing and victory detection
- Residual effects (weather, status, Leech Seed)
- Full battle integration
"""
import pytest
import numpy as np

from core.battle import (
    BattleEngine,
    Action,
    ActionType,
    Choice,
    compare_actions,
    sort_actions,
    resolve_targets,
)
from core.battle_state import (
    BattleState,
    FIELD_WEATHER, FIELD_WEATHER_TURNS, FIELD_TERRAIN, FIELD_TERRAIN_TURNS,
    FIELD_TRICK_ROOM,
    WEATHER_NONE, WEATHER_SAND, WEATHER_HAIL,
    TERRAIN_GRASSY,
    SC_STEALTH_ROCK, SC_SPIKES, SC_TOXIC_SPIKES, SC_STICKY_WEB,
    SC_WIDE_GUARD, SC_QUICK_GUARD,
)
from core.layout import (
    P_SPECIES, P_LEVEL, P_CURRENT_HP, P_STAT_HP, P_STAT_SPE,
    P_STATUS, P_STATUS_COUNTER, P_TYPE1, P_TYPE2,
    P_MOVE1, P_MOVE2, P_PP1, P_PP2,
    P_STAGE_ATK, P_STAGE_SPE,
    P_VOL_PROTECT, P_VOL_FLINCH, P_VOL_CONFUSION, P_VOL_LEECH_SEED,
    STATUS_NONE, STATUS_BURN, STATUS_POISON, STATUS_BADLY_POISONED,
    STATUS_PARALYSIS, STATUS_SLEEP, STATUS_FREEZE,
)
from core.pokemon import Pokemon
from data.moves import MoveData, MoveCategory, MoveTarget, MoveFlag, SecondaryEffect
from data.types import Type


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def basic_state():
    """Create a basic battle state with two teams."""
    state = BattleState(seed=12345)

    # Set up team 0 (two Pokemon)
    for slot in range(2):
        state.pokemons[0, slot, P_SPECIES] = 25 + slot  # Pikachu, Raichu
        state.pokemons[0, slot, P_LEVEL] = 50
        state.pokemons[0, slot, P_STAT_HP] = 100
        state.pokemons[0, slot, P_CURRENT_HP] = 100
        state.pokemons[0, slot, P_STAT_SPE] = 90 + slot * 10
        state.pokemons[0, slot, P_TYPE1] = Type.ELECTRIC.value
        state.pokemons[0, slot, P_TYPE2] = -1
        state.pokemons[0, slot, P_MOVE1] = 85  # Thunderbolt
        state.pokemons[0, slot, P_PP1] = 15
        state.active[0, slot] = slot

    # Set up team 1 (two Pokemon)
    for slot in range(2):
        state.pokemons[1, slot, P_SPECIES] = 6 + slot  # Charizard, Blastoise
        state.pokemons[1, slot, P_LEVEL] = 50
        state.pokemons[1, slot, P_STAT_HP] = 120
        state.pokemons[1, slot, P_CURRENT_HP] = 120
        state.pokemons[1, slot, P_STAT_SPE] = 80 + slot * 10
        state.pokemons[1, slot, P_TYPE1] = Type.FIRE.value if slot == 0 else Type.WATER.value
        state.pokemons[1, slot, P_TYPE2] = Type.FLYING.value if slot == 0 else -1
        state.pokemons[1, slot, P_MOVE1] = 53 if slot == 0 else 56  # Flamethrower, Hydro Pump
        state.pokemons[1, slot, P_PP1] = 15
        state.active[1, slot] = slot

    return state


@pytest.fixture
def basic_move():
    """A basic damaging move."""
    return MoveData(
        id=85,
        name="Thunderbolt",
        type=Type.ELECTRIC,
        category=MoveCategory.SPECIAL,
        base_power=90,
        accuracy=100,
        pp=15,
        priority=0,
        target=MoveTarget.NORMAL,
        flags=MoveFlag.PROTECT,
    )


@pytest.fixture
def priority_move():
    """A priority move."""
    return MoveData(
        id=98,
        name="Quick Attack",
        type=Type.NORMAL,
        category=MoveCategory.PHYSICAL,
        base_power=40,
        accuracy=100,
        pp=30,
        priority=1,
        target=MoveTarget.NORMAL,
        flags=MoveFlag.CONTACT | MoveFlag.PROTECT,
    )


@pytest.fixture
def spread_move():
    """A spread move that hits all foes."""
    return MoveData(
        id=89,
        name="Earthquake",
        type=Type.GROUND,
        category=MoveCategory.PHYSICAL,
        base_power=100,
        accuracy=100,
        pp=10,
        priority=0,
        target=MoveTarget.ALL_ADJACENT,
        flags=MoveFlag.PROTECT,
    )


@pytest.fixture
def move_registry(basic_move, priority_move, spread_move):
    """Registry of moves for the engine."""
    return {
        85: basic_move,
        98: priority_move,
        89: spread_move,
    }


@pytest.fixture
def engine(basic_state, move_registry):
    """Battle engine with basic state and moves."""
    return BattleEngine(basic_state, move_registry)


# =============================================================================
# Action Sorting Tests
# =============================================================================

class TestActionSorting:
    """Tests for action priority sorting."""

    def test_switch_before_move(self, basic_state):
        """Switches should execute before moves."""
        actions = [
            Action(ActionType.MOVE, side=0, slot=0, priority=0, speed=100),
            Action(ActionType.SWITCH, side=1, slot=0, priority=0, speed=80),
        ]
        sorted_actions = sort_actions(actions, basic_state)

        assert sorted_actions[0].action_type == ActionType.SWITCH
        assert sorted_actions[1].action_type == ActionType.MOVE

    def test_priority_ordering(self, basic_state):
        """Higher priority moves should execute first."""
        actions = [
            Action(ActionType.MOVE, side=0, slot=0, priority=0, speed=100),
            Action(ActionType.MOVE, side=1, slot=0, priority=1, speed=80),
        ]
        sorted_actions = sort_actions(actions, basic_state)

        assert sorted_actions[0].priority == 1
        assert sorted_actions[1].priority == 0

    def test_speed_tiebreak(self, basic_state):
        """Faster Pokemon should move first at equal priority."""
        actions = [
            Action(ActionType.MOVE, side=0, slot=0, priority=0, speed=80),
            Action(ActionType.MOVE, side=1, slot=0, priority=0, speed=100),
        ]
        sorted_actions = sort_actions(actions, basic_state)

        assert sorted_actions[0].speed == 100
        assert sorted_actions[1].speed == 80

    def test_trick_room_inverts_speed(self, basic_state):
        """Under Trick Room, slower Pokemon should move first."""
        basic_state.field[FIELD_TRICK_ROOM] = 5  # Active Trick Room

        actions = [
            Action(ActionType.MOVE, side=0, slot=0, priority=0, speed=100),
            Action(ActionType.MOVE, side=1, slot=0, priority=0, speed=80),
        ]
        sorted_actions = sort_actions(actions, basic_state)

        # Slower Pokemon (80 speed) should go first in Trick Room
        assert sorted_actions[0].speed == 80
        assert sorted_actions[1].speed == 100

    def test_random_tiebreak_deterministic(self, basic_state):
        """Speed ties should be broken deterministically by PRNG."""
        actions = [
            Action(ActionType.MOVE, side=0, slot=0, priority=0, speed=100, move_id=1),
            Action(ActionType.MOVE, side=1, slot=0, priority=0, speed=100, move_id=2),
        ]

        # Run sorting multiple times with same seed
        results = []
        for _ in range(5):
            state = BattleState(seed=12345)
            sorted_actions = sort_actions(actions.copy(), state)
            results.append(sorted_actions[0].move_id)

        # All results should be the same (deterministic)
        assert all(r == results[0] for r in results)

    def test_negative_priority(self, basic_state):
        """Negative priority moves should go last."""
        actions = [
            Action(ActionType.MOVE, side=0, slot=0, priority=-6, speed=100),  # Counter
            Action(ActionType.MOVE, side=1, slot=0, priority=0, speed=50),
        ]
        sorted_actions = sort_actions(actions, basic_state)

        assert sorted_actions[0].priority == 0
        assert sorted_actions[1].priority == -6


# =============================================================================
# Target Resolution Tests
# =============================================================================

class TestTargetResolution:
    """Tests for move target resolution."""

    def test_self_target(self, basic_state):
        """SELF target should only include user."""
        move = MoveData(
            id=1, name="Recover", type=Type.NORMAL, category=MoveCategory.STATUS,
            base_power=0, accuracy=None, pp=10, target=MoveTarget.SELF,
        )
        action = Action(ActionType.MOVE, side=0, slot=0, move_id=1)
        targets = resolve_targets(basic_state, action, move)

        assert len(targets) == 1
        assert targets[0] == (0, 0)

    def test_single_target(self, basic_state, basic_move):
        """NORMAL target should resolve to specified target."""
        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=85,
            target_side=1, target_slot=0,
        )
        targets = resolve_targets(basic_state, action, basic_move)

        assert len(targets) == 1
        assert targets[0] == (1, 0)

    def test_all_adjacent_foes(self, basic_state):
        """ALL_ADJACENT_FOES should hit all active foes."""
        move = MoveData(
            id=89, name="Earthquake", type=Type.GROUND, category=MoveCategory.PHYSICAL,
            base_power=100, accuracy=100, pp=10, target=MoveTarget.ALL_ADJACENT_FOES,
        )
        action = Action(ActionType.MOVE, side=0, slot=0, move_id=89)
        targets = resolve_targets(basic_state, action, move)

        # Should target both active opponents
        assert len(targets) == 2
        assert (1, 0) in targets
        assert (1, 1) in targets

    def test_ally_side_target(self, basic_state):
        """ALLY_SIDE target should return side indicator."""
        move = MoveData(
            id=100, name="Reflect", type=Type.PSYCHIC, category=MoveCategory.STATUS,
            base_power=0, accuracy=None, pp=20, target=MoveTarget.ALLY_SIDE,
        )
        action = Action(ActionType.MOVE, side=0, slot=0, move_id=100)
        targets = resolve_targets(basic_state, action, move)

        assert len(targets) == 1
        assert targets[0] == (0, -1)  # Side target

    def test_foe_side_target(self, basic_state):
        """FOE_SIDE target should return opponent side indicator."""
        move = MoveData(
            id=101, name="Stealth Rock", type=Type.ROCK, category=MoveCategory.STATUS,
            base_power=0, accuracy=None, pp=20, target=MoveTarget.FOE_SIDE,
        )
        action = Action(ActionType.MOVE, side=0, slot=0, move_id=101)
        targets = resolve_targets(basic_state, action, move)

        assert len(targets) == 1
        assert targets[0] == (1, -1)  # Opponent side target


# =============================================================================
# Move Execution Tests
# =============================================================================

class TestMoveExecution:
    """Tests for move execution."""

    def test_damage_applied(self, engine, basic_move):
        """Damage should be correctly applied to target."""
        engine._move_registry[85] = basic_move
        initial_hp = engine.state.pokemons[1, 0, P_CURRENT_HP]

        # Create move action
        engine.state.pokemons[0, 0, P_MOVE1] = 85
        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=85,
            priority=0, speed=100, target_side=1, target_slot=0,
        )

        engine.execute_move(action)

        final_hp = engine.state.pokemons[1, 0, P_CURRENT_HP]
        assert final_hp < initial_hp

    def test_pp_deducted(self, engine, basic_move):
        """PP should be deducted when using a move."""
        engine._move_registry[85] = basic_move
        initial_pp = engine.state.pokemons[0, 0, P_PP1]

        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=85,
            priority=0, speed=100, target_side=1, target_slot=0,
        )

        engine.execute_move(action)

        final_pp = engine.state.pokemons[0, 0, P_PP1]
        assert final_pp == initial_pp - 1

    def test_flinch_prevents_move(self, engine, basic_move):
        """Flinched Pokemon should not be able to move."""
        engine._move_registry[85] = basic_move
        engine.state.pokemons[0, 0, P_VOL_FLINCH] = 1
        initial_hp = engine.state.pokemons[1, 0, P_CURRENT_HP]

        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=85,
            priority=0, speed=100, target_side=1, target_slot=0,
        )

        result = engine.execute_move(action)

        assert result == False
        assert engine.state.pokemons[1, 0, P_CURRENT_HP] == initial_hp

    def test_sleep_prevents_move(self, engine, basic_move):
        """Sleeping Pokemon should not be able to move."""
        engine._move_registry[85] = basic_move
        engine.state.pokemons[0, 0, P_STATUS] = STATUS_SLEEP
        engine.state.pokemons[0, 0, P_STATUS_COUNTER] = 2
        initial_hp = engine.state.pokemons[1, 0, P_CURRENT_HP]

        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=85,
            priority=0, speed=100, target_side=1, target_slot=0,
        )

        result = engine.execute_move(action)

        assert result == False
        assert engine.state.pokemons[1, 0, P_CURRENT_HP] == initial_hp
        # Sleep counter should decrease
        assert engine.state.pokemons[0, 0, P_STATUS_COUNTER] == 1


# =============================================================================
# Protection Tests
# =============================================================================

class TestProtection:
    """Tests for protection mechanics."""

    def test_protect_blocks_move(self, engine, basic_move):
        """Protect should block moves with PROTECT flag."""
        engine._move_registry[85] = basic_move
        engine.state.pokemons[1, 0, P_VOL_PROTECT] = 1
        initial_hp = engine.state.pokemons[1, 0, P_CURRENT_HP]

        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=85,
            priority=0, speed=100, target_side=1, target_slot=0,
        )

        engine.execute_move(action)

        # HP should be unchanged
        assert engine.state.pokemons[1, 0, P_CURRENT_HP] == initial_hp

    def test_wide_guard_blocks_spread(self, engine, spread_move):
        """Wide Guard should block spread moves."""
        engine._move_registry[89] = spread_move
        engine.state.side_conditions[1, SC_WIDE_GUARD] = 1
        initial_hp_0 = engine.state.pokemons[1, 0, P_CURRENT_HP]
        initial_hp_1 = engine.state.pokemons[1, 1, P_CURRENT_HP]

        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=89,
            priority=0, speed=100,
        )

        engine.execute_move(action)

        # Both should be protected
        assert engine.state.pokemons[1, 0, P_CURRENT_HP] == initial_hp_0
        assert engine.state.pokemons[1, 1, P_CURRENT_HP] == initial_hp_1

    def test_quick_guard_blocks_priority(self, engine, priority_move):
        """Quick Guard should block priority moves."""
        engine._move_registry[98] = priority_move
        engine.state.side_conditions[1, SC_QUICK_GUARD] = 1
        initial_hp = engine.state.pokemons[1, 0, P_CURRENT_HP]

        action = Action(
            ActionType.MOVE, side=0, slot=0, move_id=98,
            priority=1, speed=100, target_side=1, target_slot=0,
        )

        engine.execute_move(action)

        # Should be protected
        assert engine.state.pokemons[1, 0, P_CURRENT_HP] == initial_hp


# =============================================================================
# Switch Tests
# =============================================================================

class TestSwitching:
    """Tests for switching mechanics."""

    def test_switch_changes_active(self, engine):
        """Switch should change the active Pokemon."""
        # Set up a third Pokemon on team 0
        engine.state.pokemons[0, 2, P_SPECIES] = 26
        engine.state.pokemons[0, 2, P_LEVEL] = 50
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_STAT_SPE] = 100

        action = Action(
            ActionType.SWITCH, side=0, slot=0,
            priority=0, speed=90, target_slot=2,  # Switch to slot 2
        )

        result = engine.execute_switch(action)

        assert result == True
        assert engine.state.active[0, 0] == 2

    def test_switch_clears_volatiles(self, engine):
        """Switching should clear volatile statuses."""
        # Set some volatiles
        engine.state.pokemons[0, 0, P_VOL_CONFUSION] = 3
        engine.state.pokemons[0, 0, P_VOL_LEECH_SEED] = 1

        # Set up target
        engine.state.pokemons[0, 2, P_SPECIES] = 26
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_STAT_HP] = 100

        action = Action(
            ActionType.SWITCH, side=0, slot=0, target_slot=2,
        )

        engine.execute_switch(action)

        # Original Pokemon's volatiles should be cleared
        assert engine.state.pokemons[0, 0, P_VOL_CONFUSION] == 0
        assert engine.state.pokemons[0, 0, P_VOL_LEECH_SEED] == 0

    def test_switch_resets_stat_stages(self, engine):
        """Switching should reset stat stages."""
        engine.state.pokemons[0, 0, P_STAGE_ATK] = 2
        engine.state.pokemons[0, 0, P_STAGE_SPE] = -1

        # Set up target
        engine.state.pokemons[0, 2, P_SPECIES] = 26
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_STAT_HP] = 100

        action = Action(
            ActionType.SWITCH, side=0, slot=0, target_slot=2,
        )

        engine.execute_switch(action)

        # Original Pokemon's stat stages should be reset
        assert engine.state.pokemons[0, 0, P_STAGE_ATK] == 0
        assert engine.state.pokemons[0, 0, P_STAGE_SPE] == 0


# =============================================================================
# Entry Hazard Tests
# =============================================================================

class TestEntryHazards:
    """Tests for entry hazards."""

    def test_stealth_rock_damage(self, engine):
        """Stealth Rock should deal damage on switch-in."""
        # Set up Stealth Rock
        engine.state.side_conditions[0, SC_STEALTH_ROCK] = 1

        # Set up a Fire-type to switch in (weak to Rock)
        engine.state.pokemons[0, 2, P_SPECIES] = 6
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_TYPE1] = Type.FIRE.value
        engine.state.pokemons[0, 2, P_TYPE2] = Type.FLYING.value

        action = Action(ActionType.SWITCH, side=0, slot=0, target_slot=2)
        engine.execute_switch(action)

        # Fire/Flying takes 4x (50%) from Stealth Rock
        # HP should be reduced
        assert engine.state.pokemons[0, 2, P_CURRENT_HP] < 100

    def test_spikes_damage(self, engine):
        """Spikes should deal damage to grounded Pokemon."""
        # Set up 2 layers of Spikes
        engine.state.side_conditions[0, SC_SPIKES] = 2

        # Set up a ground-based Pokemon
        engine.state.pokemons[0, 2, P_SPECIES] = 26
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_TYPE1] = Type.ELECTRIC.value
        engine.state.pokemons[0, 2, P_TYPE2] = -1

        action = Action(ActionType.SWITCH, side=0, slot=0, target_slot=2)
        engine.execute_switch(action)

        # Should take ~16% damage (2 layers = 1/6 HP)
        assert engine.state.pokemons[0, 2, P_CURRENT_HP] < 100

    def test_spikes_not_affect_flying(self, engine):
        """Spikes should not affect Flying-type Pokemon."""
        engine.state.side_conditions[0, SC_SPIKES] = 3

        # Set up a Flying-type
        engine.state.pokemons[0, 2, P_SPECIES] = 6
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_TYPE1] = Type.NORMAL.value
        engine.state.pokemons[0, 2, P_TYPE2] = Type.FLYING.value

        action = Action(ActionType.SWITCH, side=0, slot=0, target_slot=2)
        engine.execute_switch(action)

        # Flying type should not take Spikes damage
        assert engine.state.pokemons[0, 2, P_CURRENT_HP] == 100

    def test_toxic_spikes_poison(self, engine):
        """Toxic Spikes should poison grounded Pokemon."""
        engine.state.side_conditions[0, SC_TOXIC_SPIKES] = 1

        engine.state.pokemons[0, 2, P_SPECIES] = 26
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_TYPE1] = Type.ELECTRIC.value
        engine.state.pokemons[0, 2, P_TYPE2] = -1
        engine.state.pokemons[0, 2, P_STATUS] = STATUS_NONE

        action = Action(ActionType.SWITCH, side=0, slot=0, target_slot=2)
        engine.execute_switch(action)

        # Should be poisoned (1 layer = regular poison)
        assert engine.state.pokemons[0, 2, P_STATUS] == STATUS_POISON

    def test_toxic_spikes_badly_poison(self, engine):
        """Two layers of Toxic Spikes should badly poison."""
        engine.state.side_conditions[0, SC_TOXIC_SPIKES] = 2

        engine.state.pokemons[0, 2, P_SPECIES] = 26
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_TYPE1] = Type.ELECTRIC.value
        engine.state.pokemons[0, 2, P_TYPE2] = -1
        engine.state.pokemons[0, 2, P_STATUS] = STATUS_NONE

        action = Action(ActionType.SWITCH, side=0, slot=0, target_slot=2)
        engine.execute_switch(action)

        # Should be badly poisoned (2 layers)
        assert engine.state.pokemons[0, 2, P_STATUS] == STATUS_BADLY_POISONED

    def test_poison_type_absorbs_toxic_spikes(self, engine):
        """Poison-type Pokemon should absorb Toxic Spikes."""
        engine.state.side_conditions[0, SC_TOXIC_SPIKES] = 2

        engine.state.pokemons[0, 2, P_SPECIES] = 34  # Nidoking (Poison type)
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100
        engine.state.pokemons[0, 2, P_TYPE1] = Type.POISON.value
        engine.state.pokemons[0, 2, P_TYPE2] = Type.GROUND.value
        engine.state.pokemons[0, 2, P_STATUS] = STATUS_NONE

        action = Action(ActionType.SWITCH, side=0, slot=0, target_slot=2)
        engine.execute_switch(action)

        # Toxic Spikes should be removed
        assert engine.state.side_conditions[0, SC_TOXIC_SPIKES] == 0
        # Pokemon should not be poisoned
        assert engine.state.pokemons[0, 2, P_STATUS] == STATUS_NONE


# =============================================================================
# Residual Effect Tests
# =============================================================================

class TestResiduals:
    """Tests for end-of-turn residual effects."""

    def test_sandstorm_damage(self, engine):
        """Sandstorm should damage non-Rock/Ground/Steel types."""
        engine.state.field[FIELD_WEATHER] = WEATHER_SAND
        engine.state.field[FIELD_WEATHER_TURNS] = 5

        initial_hp = engine.state.pokemons[0, 0, P_CURRENT_HP]

        engine.run_residuals()

        # Electric type should take sand damage
        final_hp = engine.state.pokemons[0, 0, P_CURRENT_HP]
        assert final_hp < initial_hp
        assert final_hp == initial_hp - (initial_hp // 16)

    def test_sandstorm_no_damage_rock(self, engine):
        """Rock types should not take Sandstorm damage."""
        engine.state.field[FIELD_WEATHER] = WEATHER_SAND
        engine.state.field[FIELD_WEATHER_TURNS] = 5

        # Make Pokemon Rock type
        engine.state.pokemons[0, 0, P_TYPE1] = Type.ROCK.value
        initial_hp = engine.state.pokemons[0, 0, P_CURRENT_HP]

        engine.run_residuals()

        # Should not take damage
        assert engine.state.pokemons[0, 0, P_CURRENT_HP] == initial_hp

    def test_burn_damage(self, engine):
        """Burn should deal 1/16 max HP damage."""
        engine.state.pokemons[0, 0, P_STATUS] = STATUS_BURN
        initial_hp = engine.state.pokemons[0, 0, P_CURRENT_HP]
        max_hp = engine.state.pokemons[0, 0, P_STAT_HP]

        engine.run_residuals()

        expected_damage = max(1, max_hp // 16)
        assert engine.state.pokemons[0, 0, P_CURRENT_HP] == initial_hp - expected_damage

    def test_poison_damage(self, engine):
        """Poison should deal 1/8 max HP damage."""
        engine.state.pokemons[0, 0, P_STATUS] = STATUS_POISON
        initial_hp = engine.state.pokemons[0, 0, P_CURRENT_HP]
        max_hp = engine.state.pokemons[0, 0, P_STAT_HP]

        engine.run_residuals()

        expected_damage = max(1, max_hp // 8)
        assert engine.state.pokemons[0, 0, P_CURRENT_HP] == initial_hp - expected_damage

    def test_toxic_damage_increases(self, engine):
        """Toxic damage should increase each turn."""
        engine.state.pokemons[0, 0, P_STATUS] = STATUS_BADLY_POISONED
        engine.state.pokemons[0, 0, P_STATUS_COUNTER] = 0
        max_hp = engine.state.pokemons[0, 0, P_STAT_HP]

        # Turn 1
        initial_hp = engine.state.pokemons[0, 0, P_CURRENT_HP]
        engine.run_residuals()
        damage_1 = initial_hp - engine.state.pokemons[0, 0, P_CURRENT_HP]
        counter_1 = engine.state.pokemons[0, 0, P_STATUS_COUNTER]

        # Turn 2
        hp_after_1 = engine.state.pokemons[0, 0, P_CURRENT_HP]
        engine.run_residuals()
        damage_2 = hp_after_1 - engine.state.pokemons[0, 0, P_CURRENT_HP]
        counter_2 = engine.state.pokemons[0, 0, P_STATUS_COUNTER]

        assert counter_1 == 1
        assert counter_2 == 2
        assert damage_2 > damage_1

    def test_leech_seed_drain(self, engine):
        """Leech Seed should drain HP and heal opponent."""
        engine.state.pokemons[0, 0, P_VOL_LEECH_SEED] = 1
        initial_hp_target = engine.state.pokemons[0, 0, P_CURRENT_HP]
        max_hp_target = engine.state.pokemons[0, 0, P_STAT_HP]

        # Damage opponent first
        engine.state.pokemons[1, 0, P_CURRENT_HP] = 50

        engine.run_residuals()

        # Target should lose HP
        expected_drain = max(1, max_hp_target // 8)
        assert engine.state.pokemons[0, 0, P_CURRENT_HP] == initial_hp_target - expected_drain

        # Opponent should gain HP
        assert engine.state.pokemons[1, 0, P_CURRENT_HP] > 50

    def test_grassy_terrain_healing(self, engine):
        """Grassy Terrain should heal grounded Pokemon."""
        engine.state.field[FIELD_TERRAIN] = TERRAIN_GRASSY
        engine.state.field[FIELD_TERRAIN_TURNS] = 5

        # Damage Pokemon first
        engine.state.pokemons[0, 0, P_CURRENT_HP] = 50
        max_hp = engine.state.pokemons[0, 0, P_STAT_HP]

        engine.run_residuals()

        expected_heal = max(1, max_hp // 16)
        assert engine.state.pokemons[0, 0, P_CURRENT_HP] == 50 + expected_heal

    def test_field_counter_decrement(self, engine):
        """Field condition counters should decrement each turn."""
        engine.state.field[FIELD_WEATHER] = WEATHER_SAND
        engine.state.field[FIELD_WEATHER_TURNS] = 3
        engine.state.field[FIELD_TRICK_ROOM] = 2

        engine._decrement_field_counters()

        assert engine.state.field[FIELD_WEATHER_TURNS] == 2
        assert engine.state.field[FIELD_TRICK_ROOM] == 1

    def test_weather_expires(self, engine):
        """Weather should expire when counter reaches 0."""
        engine.state.field[FIELD_WEATHER] = WEATHER_SAND
        engine.state.field[FIELD_WEATHER_TURNS] = 1

        engine._decrement_field_counters()

        assert engine.state.field[FIELD_WEATHER] == WEATHER_NONE
        assert engine.state.field[FIELD_WEATHER_TURNS] == 0


# =============================================================================
# Victory Condition Tests
# =============================================================================

class TestVictory:
    """Tests for victory detection."""

    def test_all_fainted_loses(self, engine):
        """Side with all fainted Pokemon should lose."""
        # Faint all of side 1's Pokemon
        for slot in range(engine.state.team_size):
            engine.state.pokemons[1, slot, P_CURRENT_HP] = 0

        winner = engine.check_victory()

        assert winner == 0  # Side 0 wins

    def test_battle_continues_if_pokemon_remaining(self, engine):
        """Battle should continue if both sides have Pokemon."""
        winner = engine.check_victory()

        assert winner is None

    def test_victory_check_ignores_empty_slots(self, engine):
        """Victory check should ignore Pokemon with species_id=0."""
        # Clear all but one Pokemon on each side
        for slot in range(2, engine.state.team_size):
            engine.state.pokemons[0, slot, P_SPECIES] = 0
            engine.state.pokemons[1, slot, P_SPECIES] = 0

        winner = engine.check_victory()

        assert winner is None  # Both sides still have active Pokemon


# =============================================================================
# Full Integration Tests
# =============================================================================

class TestFullBattle:
    """Full battle integration tests."""

    def test_simple_turn(self, engine, basic_move):
        """Execute a simple one-turn battle."""
        engine._move_registry[85] = basic_move

        choices = {
            0: [Choice('move', slot=0, move_slot=0, target=1)],
            1: [Choice('move', slot=0, move_slot=0, target=1)],
        }

        continues = engine.step(choices)

        assert continues == True
        assert engine.turn == 1

    def test_battle_determinism(self, move_registry):
        """Same seed + choices should produce identical outcomes."""
        def run_battle(seed):
            state = BattleState(seed=seed)

            # Set up teams identically
            for side in range(2):
                for slot in range(2):
                    state.pokemons[side, slot, P_SPECIES] = 25
                    state.pokemons[side, slot, P_LEVEL] = 50
                    state.pokemons[side, slot, P_STAT_HP] = 100
                    state.pokemons[side, slot, P_CURRENT_HP] = 100
                    state.pokemons[side, slot, P_STAT_SPE] = 90
                    state.pokemons[side, slot, P_TYPE1] = Type.ELECTRIC.value
                    state.pokemons[side, slot, P_MOVE1] = 85
                    state.pokemons[side, slot, P_PP1] = 15
                    state.active[side, slot] = slot

            engine = BattleEngine(state, move_registry)

            choices = {
                0: [Choice('move', slot=0, move_slot=0, target=1)],
                1: [Choice('move', slot=0, move_slot=0, target=1)],
            }

            engine.step(choices)
            return (
                state.pokemons[0, 0, P_CURRENT_HP],
                state.pokemons[1, 0, P_CURRENT_HP],
            )

        # Run twice with same seed
        result1 = run_battle(seed=99999)
        result2 = run_battle(seed=99999)

        assert result1 == result2

    def test_faint_triggers_forced_switch(self, engine, basic_move):
        """Fainting should require a forced switch."""
        engine._move_registry[85] = basic_move

        # Set target to 1 HP so it will faint
        engine.state.pokemons[1, 0, P_CURRENT_HP] = 1

        choices = {
            0: [Choice('move', slot=0, move_slot=0, target=1)],
            1: [Choice('pass', slot=0)],
        }

        engine.step(choices)

        # Check if side 1 needs a forced switch
        pending = engine.get_forced_switches()
        # Should have a pending switch for side 1
        assert any(side == 1 for side, _ in pending)


class TestChoiceResolution:
    """Tests for choice to action conversion."""

    def test_move_choice_creates_action(self, engine, basic_move):
        """Move choice should create proper action."""
        engine._move_registry[85] = basic_move

        choices = {
            0: [Choice('move', slot=0, move_slot=0, target=1)],
        }

        actions = engine.resolve_choices(choices)

        assert len(actions) == 1
        assert actions[0].action_type == ActionType.MOVE
        assert actions[0].side == 0
        assert actions[0].move_id == 85

    def test_switch_choice_creates_action(self, engine):
        """Switch choice should create proper action."""
        # Set up a third Pokemon to switch to
        engine.state.pokemons[0, 2, P_SPECIES] = 26
        engine.state.pokemons[0, 2, P_STAT_HP] = 100
        engine.state.pokemons[0, 2, P_CURRENT_HP] = 100

        choices = {
            0: [Choice('switch', slot=0, switch_to=2)],
        }

        actions = engine.resolve_choices(choices)

        assert len(actions) == 1
        assert actions[0].action_type == ActionType.SWITCH
        assert actions[0].target_slot == 2

    def test_pass_choice_no_action(self, engine):
        """Pass choice should not create an action."""
        choices = {
            0: [Choice('pass', slot=0)],
        }

        actions = engine.resolve_choices(choices)

        assert len(actions) == 0
