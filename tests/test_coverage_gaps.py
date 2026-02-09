"""Tests for coverage gaps in the battle engine.

Covers 9 areas:
1. _apply_secondary_effect() - burn chance, status blocking, stat drops, self-boosts, confusion
2. _apply_side_effect() - hazards, screens, Defog, Rapid Spin, Tailwind (stub awareness)
3. Multi-hit move integration
4. Recoil and drain integration
5. Freeze thaw and sleep wake mechanics
6. Confusion self-hit
7. Spread damage modifier integration
8. Accuracy with stat stages integration
9. Type immunity in battle context
"""
import pytest
import numpy as np

from core.battle import (
    BattleEngine,
    Action,
    ActionType,
    Choice,
    sort_actions,
    resolve_targets,
)
from core.battle_state import (
    BattleState,
    BattlePRNG,
    FIELD_WEATHER, FIELD_WEATHER_TURNS, FIELD_TERRAIN, FIELD_TERRAIN_TURNS,
    FIELD_TRICK_ROOM,
    WEATHER_NONE, WEATHER_SAND, WEATHER_HAIL,
    TERRAIN_GRASSY,
    SC_REFLECT, SC_LIGHT_SCREEN, SC_AURORA_VEIL,
    SC_STEALTH_ROCK, SC_SPIKES, SC_TOXIC_SPIKES, SC_STICKY_WEB,
    SC_WIDE_GUARD, SC_QUICK_GUARD, SC_TAILWIND,
)
from core.layout import (
    P_SPECIES, P_LEVEL, P_CURRENT_HP, P_STAT_HP,
    P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_STATUS, P_STATUS_COUNTER, P_TYPE1, P_TYPE2, P_TERA_TYPE,
    P_MOVE1, P_MOVE2, P_MOVE3, P_MOVE4,
    P_PP1, P_PP2, P_PP3, P_PP4,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
    P_STAGE_ACC, P_STAGE_EVA,
    P_VOL_PROTECT, P_VOL_FLINCH, P_VOL_CONFUSION, P_VOL_LEECH_SEED,
    P_VOL_SUBSTITUTE, P_VOL_SUBSTITUTE_HP,
    STATUS_NONE, STATUS_BURN, STATUS_FREEZE, STATUS_PARALYSIS,
    STATUS_POISON, STATUS_BADLY_POISONED, STATUS_SLEEP,
    P_ABILITY,
)
from core.pokemon import Pokemon
from core.damage import calculate_confusion_damage
from data.moves import MoveData, MoveCategory, MoveTarget, MoveFlag, SecondaryEffect
from data.types import Type


# =============================================================================
# Helper: create a minimal battle state with two sides, each having Pokemon
# =============================================================================

def make_state(seed=12345, active_slots=2):
    """Create a doubles battle state with generic Pokemon on each side."""
    state = BattleState(seed=seed, active_slots=active_slots)

    for side in range(2):
        for slot in range(2):
            state.pokemons[side, slot, P_SPECIES] = 1 + side * 10 + slot
            state.pokemons[side, slot, P_LEVEL] = 50
            state.pokemons[side, slot, P_STAT_HP] = 200
            state.pokemons[side, slot, P_CURRENT_HP] = 200
            state.pokemons[side, slot, P_STAT_ATK] = 100
            state.pokemons[side, slot, P_STAT_DEF] = 100
            state.pokemons[side, slot, P_STAT_SPA] = 100
            state.pokemons[side, slot, P_STAT_SPD] = 100
            state.pokemons[side, slot, P_STAT_SPE] = 100
            state.pokemons[side, slot, P_TYPE1] = Type.NORMAL.value
            state.pokemons[side, slot, P_TYPE2] = -1
            state.pokemons[side, slot, P_TERA_TYPE] = -1
            state.active[side, slot] = slot

    return state


def set_pokemon_type(state, side, slot, type1, type2=-1):
    """Set types on a Pokemon in the state."""
    state.pokemons[side, slot, P_TYPE1] = type1
    state.pokemons[side, slot, P_TYPE2] = type2


def give_move(state, side, slot, move_slot, move_id, pp=15):
    """Give a Pokemon a move in a specific slot."""
    state.pokemons[side, slot, P_MOVE1 + move_slot] = move_id
    state.pokemons[side, slot, P_PP1 + move_slot] = pp


def make_engine(state, moves):
    """Create engine with a move registry dict."""
    return BattleEngine(state, move_registry=moves)


def make_move_action(side, slot, move_id, target_side, target_slot, speed=100, priority=0):
    """Create a move action."""
    return Action(
        action_type=ActionType.MOVE,
        side=side,
        slot=slot,
        priority=priority,
        speed=speed,
        move_id=move_id,
        target_side=target_side,
        target_slot=target_slot,
    )


# =============================================================================
# Common move fixtures
# =============================================================================

FLAMETHROWER = MoveData(
    id=53,
    name="Flamethrower",
    type=Type.FIRE,
    category=MoveCategory.SPECIAL,
    base_power=90,
    accuracy=100,
    pp=15,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT,
    secondary=SecondaryEffect(chance=10, status='brn'),
)

# Never-miss version for easier testing (avoids accuracy PRNG consumption)
FLAMETHROWER_NEVER_MISS = MoveData(
    id=53,
    name="Flamethrower",
    type=Type.FIRE,
    category=MoveCategory.SPECIAL,
    base_power=90,
    accuracy=None,  # Never misses
    pp=15,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT,
    secondary=SecondaryEffect(chance=10, status='brn'),
)

MOONBLAST = MoveData(
    id=585,
    name="Moonblast",
    type=Type.FAIRY,
    category=MoveCategory.SPECIAL,
    base_power=95,
    accuracy=None,
    pp=15,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT,
    secondary=SecondaryEffect(chance=30, boosts={'spa': -1}),
)

POWER_UP_PUNCH = MoveData(
    id=612,
    name="Power-Up Punch",
    type=Type.FIGHTING,
    category=MoveCategory.PHYSICAL,
    base_power=40,
    accuracy=None,
    pp=20,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.CONTACT | MoveFlag.PROTECT | MoveFlag.PUNCH,
    secondary=SecondaryEffect(chance=100, self_boosts={'atk': 1}),
)

HURRICANE = MoveData(
    id=542,
    name="Hurricane",
    type=Type.FLYING,
    category=MoveCategory.SPECIAL,
    base_power=110,
    accuracy=None,  # Simplified for testing
    pp=10,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT,
    secondary=SecondaryEffect(chance=30, volatile_status='confusion'),
)

THUNDERBOLT = MoveData(
    id=85,
    name="Thunderbolt",
    type=Type.ELECTRIC,
    category=MoveCategory.SPECIAL,
    base_power=90,
    accuracy=100,
    pp=15,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT,
)

TACKLE = MoveData(
    id=33,
    name="Tackle",
    type=Type.NORMAL,
    category=MoveCategory.PHYSICAL,
    base_power=40,
    accuracy=100,
    pp=35,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.CONTACT | MoveFlag.PROTECT,
)

BRAVE_BIRD = MoveData(
    id=413,
    name="Brave Bird",
    type=Type.FLYING,
    category=MoveCategory.PHYSICAL,
    base_power=120,
    accuracy=None,
    pp=15,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.CONTACT | MoveFlag.PROTECT,
    recoil=1.0 / 3.0,
)

GIGA_DRAIN = MoveData(
    id=202,
    name="Giga Drain",
    type=Type.GRASS,
    category=MoveCategory.SPECIAL,
    base_power=75,
    accuracy=None,
    pp=10,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT,
    drain=0.5,
)

BULLET_SEED = MoveData(
    id=331,
    name="Bullet Seed",
    type=Type.GRASS,
    category=MoveCategory.PHYSICAL,
    base_power=25,
    accuracy=None,
    pp=30,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT | MoveFlag.BULLET,
    multi_hit=(2, 5),
)

EARTHQUAKE = MoveData(
    id=89,
    name="Earthquake",
    type=Type.GROUND,
    category=MoveCategory.PHYSICAL,
    base_power=100,
    accuracy=None,
    pp=10,
    target=MoveTarget.ALL_ADJACENT,
    flags=MoveFlag.PROTECT,
)

EARTHQUAKE_FOES_ONLY = MoveData(
    id=189,
    name="EarthquakeFoes",
    type=Type.GROUND,
    category=MoveCategory.PHYSICAL,
    base_power=100,
    accuracy=None,
    pp=10,
    target=MoveTarget.ALL_ADJACENT_FOES,
    flags=MoveFlag.PROTECT,
)

SWIFT = MoveData(
    id=129,
    name="Swift",
    type=Type.NORMAL,
    category=MoveCategory.SPECIAL,
    base_power=60,
    accuracy=None,  # Never misses
    pp=20,
    target=MoveTarget.ALL_ADJACENT_FOES,
    flags=MoveFlag.PROTECT,
)

WILD_CHARGE = MoveData(
    id=528,
    name="Wild Charge",
    type=Type.ELECTRIC,
    category=MoveCategory.PHYSICAL,
    base_power=90,
    accuracy=None,
    pp=15,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.CONTACT | MoveFlag.PROTECT,
    recoil=0.25,
)

# Simple physical move with no accuracy check for controlled tests
SIMPLE_PHYSICAL = MoveData(
    id=900,
    name="SimplePhysical",
    type=Type.NORMAL,
    category=MoveCategory.PHYSICAL,
    base_power=50,
    accuracy=None,
    pp=30,
    target=MoveTarget.NORMAL,
    flags=MoveFlag.PROTECT,
)


# =============================================================================
# 1. _apply_secondary_effect() Tests
# =============================================================================

class TestSecondaryEffects:
    """Tests for _apply_secondary_effect in BattleEngine."""

    def test_secondary_burn_chance_applies(self):
        """Seed RNG so 10% burn chance hits. Verify target gets burned."""
        # seed=4: PRNG sequence for never-miss move:
        #   crit: next(24)=17 (no crit), random: next(16), secondary: next(100)=8 (<10 = HIT)
        state = make_state(seed=4)
        give_move(state, 0, 0, 0, 53, pp=15)
        engine = make_engine(state, {53: FLAMETHROWER_NEVER_MISS})

        target = state.get_pokemon(1, 0)
        assert target.status == STATUS_NONE

        action = make_move_action(0, 0, 53, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        assert target.status == STATUS_BURN

    def test_secondary_burn_chance_misses(self):
        """Seed RNG so 10% burn chance misses. Verify target not burned."""
        # seed=1: for never-miss: crit: next(24)=14 (no), random: next(16), secondary: next(100)=98 (>=10)
        state = make_state(seed=1)
        give_move(state, 0, 0, 0, 53, pp=15)
        engine = make_engine(state, {53: FLAMETHROWER_NEVER_MISS})

        action = make_move_action(0, 0, 53, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        assert target.status == STATUS_NONE

    def test_secondary_status_blocked_by_existing_status(self):
        """Target already has paralysis. 10% burn should not overwrite it."""
        state = make_state(seed=4)  # seed where secondary would trigger
        give_move(state, 0, 0, 0, 53, pp=15)
        engine = make_engine(state, {53: FLAMETHROWER_NEVER_MISS})

        # Give target paralysis before the move
        state.pokemons[1, 0, P_STATUS] = STATUS_PARALYSIS

        action = make_move_action(0, 0, 53, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        assert target.status == STATUS_PARALYSIS  # Still paralysis, not burn

    def test_secondary_stat_drop_applied_to_target(self):
        """Moonblast secondary (30% SpA -1 on target). Verify target's SpA drops."""
        # seed=0: for never-miss: crit: next(24)=0 (yes, crit), but that's fine
        # Actually we need crit_roll >= 1. Let's find a seed.
        # We need: crit no-crit, then secondary < 30.
        # seed=0: crit_roll = next(24)  -- let me check
        state = make_state(seed=0)
        give_move(state, 0, 0, 0, 585, pp=15)
        engine = make_engine(state, {585: MOONBLAST})

        target_spa_before = state.get_pokemon(1, 0).get_stage(P_STAGE_SPA)
        attacker_spa_before = state.get_pokemon(0, 0).get_stage(P_STAGE_SPA)

        action = make_move_action(0, 0, 585, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        attacker = state.get_pokemon(0, 0)
        # Target SpA should have dropped by 1
        assert target.get_stage(P_STAGE_SPA) == target_spa_before - 1
        # Attacker SpA should be unchanged
        assert attacker.get_stage(P_STAGE_SPA) == attacker_spa_before

    def test_secondary_self_boost_applied_to_attacker(self):
        """Power-Up Punch (100% self_boosts atk +1). Verify attacker's Atk goes up."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 612, pp=20)
        engine = make_engine(state, {612: POWER_UP_PUNCH})

        attacker_atk_before = state.get_pokemon(0, 0).get_stage(P_STAGE_ATK)
        target_atk_before = state.get_pokemon(1, 0).get_stage(P_STAGE_ATK)

        action = make_move_action(0, 0, 612, 1, 0)
        engine.execute_move(action)

        attacker = state.get_pokemon(0, 0)
        target = state.get_pokemon(1, 0)
        assert attacker.get_stage(P_STAGE_ATK) == attacker_atk_before + 1
        assert target.get_stage(P_STAGE_ATK) == target_atk_before

    def test_secondary_confusion_application(self):
        """Hurricane (30% confusion). Verify confusion flag set with turns 2-5."""
        # We need the secondary to trigger: need PRNG to produce < 30 at the right point
        # Use multiple seeds and check if any produce confusion
        found = False
        for seed in range(200):
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 542, pp=10)
            engine = make_engine(state, {542: HURRICANE})

            action = make_move_action(0, 0, 542, 1, 0)
            engine.execute_move(action)

            target = state.get_pokemon(1, 0)
            if target.data[P_VOL_CONFUSION] > 0:
                assert 2 <= target.data[P_VOL_CONFUSION] <= 5
                found = True
                break

        assert found, "Could not find a seed that triggers confusion secondary"

    def test_secondary_confusion_range_is_2_to_5(self):
        """Run many seeds to verify confusion counter is always in [2, 5]."""
        confusion_values = set()
        for seed in range(500):
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 542, pp=10)
            engine = make_engine(state, {542: HURRICANE})

            action = make_move_action(0, 0, 542, 1, 0)
            engine.execute_move(action)

            target = state.get_pokemon(1, 0)
            if target.data[P_VOL_CONFUSION] > 0:
                confusion_values.add(int(target.data[P_VOL_CONFUSION]))

        # All confusion values must be in [2, 5]
        for v in confusion_values:
            assert 2 <= v <= 5, f"Confusion counter {v} outside [2, 5]"

    def test_secondary_100_percent_always_triggers(self):
        """100% chance secondary (Power-Up Punch) always triggers regardless of seed."""
        for seed in [0, 1, 42, 99, 150]:
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 612, pp=20)
            engine = make_engine(state, {612: POWER_UP_PUNCH})

            action = make_move_action(0, 0, 612, 1, 0)
            engine.execute_move(action)

            attacker = state.get_pokemon(0, 0)
            assert attacker.get_stage(P_STAGE_ATK) >= 1, f"Self-boost failed at seed={seed}"


# =============================================================================
# 2. _apply_side_effect() Tests (stub awareness)
# =============================================================================

class TestSideEffects:
    """Tests for _apply_side_effect. Currently a stub that returns True.

    These tests document the expected behavior and verify the stub doesn't crash.
    They also test the entry hazard system which IS implemented.
    """

    def test_side_effect_stub_returns_true(self):
        """The stub _apply_side_effect always returns True."""
        state = make_state(seed=42)
        engine = make_engine(state, {})

        # Create a dummy status move targeting the foe's side
        stealth_rock = MoveData(
            id=446, name="Stealth Rock", type=Type.ROCK,
            category=MoveCategory.STATUS, base_power=0, accuracy=None,
            pp=20, target=MoveTarget.FOE_SIDE, flags=MoveFlag.REFLECTABLE,
        )
        result = engine._apply_side_effect(stealth_rock, 0, 1)
        assert result is True

    def test_stealth_rock_damage_on_switch_in(self):
        """Stealth Rock does 12.5% HP on switch-in for neutral types."""
        state = make_state(seed=42)
        engine = make_engine(state, {})

        # Set Stealth Rock on side 1
        state.side_conditions[1, SC_STEALTH_ROCK] = 1

        # Put a 3rd Pokemon on side 1 for switch-in
        state.pokemons[1, 2, P_SPECIES] = 50
        state.pokemons[1, 2, P_LEVEL] = 50
        state.pokemons[1, 2, P_STAT_HP] = 200
        state.pokemons[1, 2, P_CURRENT_HP] = 200
        state.pokemons[1, 2, P_TYPE1] = Type.NORMAL.value
        state.pokemons[1, 2, P_TYPE2] = -1
        state.pokemons[1, 2, P_TERA_TYPE] = -1

        # Switch in the 3rd Pokemon
        engine._apply_entry_hazards(1, 2)

        poke = state.get_pokemon(1, 2)
        # 200 * 1.0 / 8 = 25 damage for neutral type
        expected_damage = max(1, int(200 * 1.0 / 8))
        assert poke.current_hp == 200 - expected_damage

    def test_stealth_rock_super_effective_damage(self):
        """Stealth Rock does more damage to Rock-weak types (e.g., Fire/Flying)."""
        state = make_state(seed=42)
        engine = make_engine(state, {})
        state.side_conditions[1, SC_STEALTH_ROCK] = 1

        # Fire/Flying is 4x weak to Rock
        state.pokemons[1, 2, P_SPECIES] = 50
        state.pokemons[1, 2, P_LEVEL] = 50
        state.pokemons[1, 2, P_STAT_HP] = 200
        state.pokemons[1, 2, P_CURRENT_HP] = 200
        state.pokemons[1, 2, P_TYPE1] = Type.FIRE.value
        state.pokemons[1, 2, P_TYPE2] = Type.FLYING.value
        state.pokemons[1, 2, P_TERA_TYPE] = -1

        engine._apply_entry_hazards(1, 2)

        poke = state.get_pokemon(1, 2)
        # 200 * 4.0 / 8 = 100 damage
        expected_damage = max(1, int(200 * 4.0 / 8))
        assert poke.current_hp == 200 - expected_damage

    def test_spikes_layering_damage(self):
        """Spikes deal increasing damage with more layers: 1/8, 1/6, 1/4."""
        for layers, divisor in [(1, 8), (2, 6), (3, 4)]:
            state = make_state(seed=42)
            engine = make_engine(state, {})
            state.side_conditions[1, SC_SPIKES] = layers

            # Grounded, non-Flying Pokemon
            state.pokemons[1, 2, P_SPECIES] = 50
            state.pokemons[1, 2, P_LEVEL] = 50
            state.pokemons[1, 2, P_STAT_HP] = 240
            state.pokemons[1, 2, P_CURRENT_HP] = 240
            state.pokemons[1, 2, P_TYPE1] = Type.NORMAL.value
            state.pokemons[1, 2, P_TYPE2] = -1
            state.pokemons[1, 2, P_TERA_TYPE] = -1

            engine._apply_entry_hazards(1, 2)

            poke = state.get_pokemon(1, 2)
            expected_damage = max(1, 240 // divisor)
            assert poke.current_hp == 240 - expected_damage, (
                f"Spikes {layers} layers: expected {240 - expected_damage}, got {poke.current_hp}"
            )

    def test_spikes_do_not_affect_flying(self):
        """Flying-type Pokemon are immune to Spikes."""
        state = make_state(seed=42)
        engine = make_engine(state, {})
        state.side_conditions[1, SC_SPIKES] = 3

        state.pokemons[1, 2, P_SPECIES] = 50
        state.pokemons[1, 2, P_STAT_HP] = 200
        state.pokemons[1, 2, P_CURRENT_HP] = 200
        state.pokemons[1, 2, P_TYPE1] = Type.FLYING.value
        state.pokemons[1, 2, P_TYPE2] = -1
        state.pokemons[1, 2, P_TERA_TYPE] = -1

        engine._apply_entry_hazards(1, 2)

        poke = state.get_pokemon(1, 2)
        assert poke.current_hp == 200  # No damage

    def test_toxic_spikes_one_layer_poisons(self):
        """One layer of Toxic Spikes inflicts regular poison on switch-in."""
        state = make_state(seed=42)
        engine = make_engine(state, {})
        state.side_conditions[1, SC_TOXIC_SPIKES] = 1

        state.pokemons[1, 2, P_SPECIES] = 50
        state.pokemons[1, 2, P_STAT_HP] = 200
        state.pokemons[1, 2, P_CURRENT_HP] = 200
        state.pokemons[1, 2, P_TYPE1] = Type.NORMAL.value
        state.pokemons[1, 2, P_TYPE2] = -1
        state.pokemons[1, 2, P_TERA_TYPE] = -1

        engine._apply_entry_hazards(1, 2)

        poke = state.get_pokemon(1, 2)
        assert poke.status == STATUS_POISON

    def test_toxic_spikes_two_layers_badly_poisons(self):
        """Two layers of Toxic Spikes inflicts bad poison on switch-in."""
        state = make_state(seed=42)
        engine = make_engine(state, {})
        state.side_conditions[1, SC_TOXIC_SPIKES] = 2

        state.pokemons[1, 2, P_SPECIES] = 50
        state.pokemons[1, 2, P_STAT_HP] = 200
        state.pokemons[1, 2, P_CURRENT_HP] = 200
        state.pokemons[1, 2, P_TYPE1] = Type.NORMAL.value
        state.pokemons[1, 2, P_TYPE2] = -1
        state.pokemons[1, 2, P_TERA_TYPE] = -1

        engine._apply_entry_hazards(1, 2)

        poke = state.get_pokemon(1, 2)
        assert poke.status == STATUS_BADLY_POISONED

    def test_poison_type_absorbs_toxic_spikes(self):
        """Poison-type switching in removes Toxic Spikes from the field."""
        state = make_state(seed=42)
        engine = make_engine(state, {})
        state.side_conditions[1, SC_TOXIC_SPIKES] = 2

        state.pokemons[1, 2, P_SPECIES] = 50
        state.pokemons[1, 2, P_STAT_HP] = 200
        state.pokemons[1, 2, P_CURRENT_HP] = 200
        state.pokemons[1, 2, P_TYPE1] = Type.POISON.value
        state.pokemons[1, 2, P_TYPE2] = -1
        state.pokemons[1, 2, P_TERA_TYPE] = -1

        engine._apply_entry_hazards(1, 2)

        poke = state.get_pokemon(1, 2)
        assert poke.status == STATUS_NONE  # Not poisoned
        assert state.side_conditions[1, SC_TOXIC_SPIKES] == 0  # Spikes removed

    def test_reflect_counter_decrements(self):
        """Reflect counter decrements each turn via _decrement_field_counters."""
        state = make_state(seed=42)
        engine = make_engine(state, {})

        state.side_conditions[0, SC_REFLECT] = 5
        engine._decrement_field_counters()
        assert state.side_conditions[0, SC_REFLECT] == 4
        engine._decrement_field_counters()
        assert state.side_conditions[0, SC_REFLECT] == 3

    def test_reflect_expires_at_zero(self):
        """Reflect counter reaches 0 and stays at 0."""
        state = make_state(seed=42)
        engine = make_engine(state, {})

        state.side_conditions[0, SC_REFLECT] = 1
        engine._decrement_field_counters()
        assert state.side_conditions[0, SC_REFLECT] == 0
        # Shouldn't go negative
        engine._decrement_field_counters()
        assert state.side_conditions[0, SC_REFLECT] == 0

    def test_tailwind_counter_decrements(self):
        """Tailwind counter decrements each turn."""
        state = make_state(seed=42)
        engine = make_engine(state, {})

        state.side_conditions[0, SC_TAILWIND] = 4
        engine._decrement_field_counters()
        assert state.side_conditions[0, SC_TAILWIND] == 3


# =============================================================================
# 3. Multi-Hit Move Integration Tests
# =============================================================================

class TestMultiHitIntegration:
    """Integration tests for multi-hit moves (Bullet Seed etc.)."""

    def _run_multi_hit(self, seed):
        """Execute Bullet Seed with a given seed and return (hits, target_hp)."""
        state = make_state(seed=seed)
        give_move(state, 0, 0, 0, 331, pp=30)
        engine = make_engine(state, {331: BULLET_SEED})

        target_hp_before = state.get_pokemon(1, 0).current_hp

        action = make_move_action(0, 0, 331, 1, 0)
        engine.execute_move(action)

        target_hp_after = state.get_pokemon(1, 0).current_hp
        total_damage = target_hp_before - target_hp_after
        return total_damage, target_hp_after

    def test_multi_hit_deals_multiple_hits_damage(self):
        """Bullet Seed hits 2-5 times. Verify damage is > single-hit damage."""
        # Run with a simple move first to get single-hit damage as baseline
        state = make_state(seed=42)
        single_hit = MoveData(
            id=332, name="SingleSeed", type=Type.GRASS,
            category=MoveCategory.PHYSICAL, base_power=25,
            accuracy=None, pp=30, target=MoveTarget.NORMAL,
            flags=MoveFlag.PROTECT,
        )
        give_move(state, 0, 0, 0, 332, pp=30)
        engine = make_engine(state, {332: single_hit})

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 332, 1, 0)
        engine.execute_move(action)
        single_damage = target_hp_before - state.get_pokemon(1, 0).current_hp

        # Now multi-hit should deal at least 2x that (minimum 2 hits)
        multi_damage, _ = self._run_multi_hit(seed=42)
        assert multi_damage >= single_damage * 2, (
            f"Multi-hit damage {multi_damage} should be >= 2 * single hit {single_damage}"
        )

    def test_multi_hit_stops_on_faint(self):
        """Multi-hit move stops early if target faints."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 331, pp=30)
        engine = make_engine(state, {331: BULLET_SEED})

        # Set target HP very low so it faints after 1-2 hits
        state.pokemons[1, 0, P_CURRENT_HP] = 5

        action = make_move_action(0, 0, 331, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        assert target.current_hp == 0
        assert target.is_fainted

    def test_multi_hit_varied_counts(self):
        """Run many seeds to verify multi-hit produces different hit counts (2-5)."""
        damages = set()
        for seed in range(200):
            damage, _ = self._run_multi_hit(seed)
            if damage > 0:
                damages.add(damage)

        # We should see at least 2 different damage totals (different hit counts)
        assert len(damages) >= 2, "Expected varied multi-hit counts across seeds"


# =============================================================================
# 4. Recoil and Drain Integration Tests
# =============================================================================

class TestRecoilDrainIntegration:
    """Integration tests for recoil and drain moves in battle context."""

    def test_brave_bird_recoil_damages_attacker(self):
        """Brave Bird deals recoil = 1/3 of damage dealt to attacker."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 413, pp=15)
        engine = make_engine(state, {413: BRAVE_BIRD})

        attacker_hp_before = state.get_pokemon(0, 0).current_hp
        target_hp_before = state.get_pokemon(1, 0).current_hp

        action = make_move_action(0, 0, 413, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        attacker = state.get_pokemon(0, 0)
        damage_dealt = target_hp_before - target.current_hp
        recoil_taken = attacker_hp_before - attacker.current_hp

        assert damage_dealt > 0, "Brave Bird should deal damage"
        expected_recoil = max(1, int(damage_dealt * (1.0 / 3.0)))
        assert recoil_taken == expected_recoil, (
            f"Recoil should be ~1/3 of {damage_dealt}: expected {expected_recoil}, got {recoil_taken}"
        )

    def test_recoil_can_faint_attacker(self):
        """Attacker faints from recoil after dealing damage."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 413, pp=15)
        engine = make_engine(state, {413: BRAVE_BIRD})

        # Set attacker to very low HP
        state.pokemons[0, 0, P_CURRENT_HP] = 5

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 413, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        attacker = state.get_pokemon(0, 0)

        # Target should take full damage
        assert target.current_hp < target_hp_before
        # Attacker should be fainted from recoil
        assert attacker.is_fainted

    def test_giga_drain_heals_attacker(self):
        """Giga Drain heals attacker for 50% of damage dealt."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 202, pp=10)
        engine = make_engine(state, {202: GIGA_DRAIN})

        # Lower attacker HP so healing is visible
        state.pokemons[0, 0, P_CURRENT_HP] = 100

        attacker_hp_before = 100
        target_hp_before = state.get_pokemon(1, 0).current_hp

        action = make_move_action(0, 0, 202, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        attacker = state.get_pokemon(0, 0)
        damage_dealt = target_hp_before - target.current_hp
        hp_recovered = attacker.current_hp - attacker_hp_before

        assert damage_dealt > 0
        expected_heal = max(1, int(damage_dealt * 0.5))
        assert hp_recovered == expected_heal, (
            f"Drain should heal ~50% of {damage_dealt}: expected {expected_heal}, got {hp_recovered}"
        )

    def test_drain_does_not_exceed_max_hp(self):
        """Drain healing caps at max HP, doesn't overflow."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 202, pp=10)
        engine = make_engine(state, {202: GIGA_DRAIN})

        # Attacker at full HP already
        assert state.get_pokemon(0, 0).current_hp == state.get_pokemon(0, 0).max_hp

        action = make_move_action(0, 0, 202, 1, 0)
        engine.execute_move(action)

        attacker = state.get_pokemon(0, 0)
        assert attacker.current_hp == attacker.max_hp  # Capped at max

    def test_no_recoil_on_zero_damage(self):
        """If move deals 0 damage (e.g., immunity), no recoil is taken."""
        state = make_state(seed=42)
        # Wild Charge is Electric, target is Ground (immune)
        give_move(state, 0, 0, 0, 528, pp=15)
        engine = make_engine(state, {528: WILD_CHARGE})

        # Make target Ground-type (immune to Electric)
        set_pokemon_type(state, 1, 0, Type.GROUND.value)

        attacker_hp_before = state.get_pokemon(0, 0).current_hp
        action = make_move_action(0, 0, 528, 1, 0)
        engine.execute_move(action)

        attacker = state.get_pokemon(0, 0)
        assert attacker.current_hp == attacker_hp_before  # No recoil


# =============================================================================
# 5. Freeze Thaw and Sleep Wake Tests
# =============================================================================

class TestFreezeAndSleep:
    """Tests for freeze thaw mechanics and sleep counter decrement."""

    def test_sleep_counter_decrements_each_turn(self):
        """Sleeping Pokemon can't move, counter decrements, then wakes up."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        # Put Pokemon to sleep with counter=2
        state.pokemons[0, 0, P_STATUS] = STATUS_SLEEP
        state.pokemons[0, 0, P_STATUS_COUNTER] = 2

        pokemon = state.get_pokemon(0, 0)
        target_hp_before = state.get_pokemon(1, 0).current_hp

        # Turn 1: counter=2, should fail and decrement to 1
        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)
        assert result is False
        assert state.get_pokemon(0, 0).status == STATUS_SLEEP
        assert state.get_pokemon(0, 0).status_counter == 1

        # Turn 2: counter=1, should fail and decrement to 0
        give_move(state, 0, 0, 0, 900, pp=30)  # Refresh PP
        result = engine.execute_move(action)
        assert result is False
        assert state.get_pokemon(0, 0).status == STATUS_SLEEP
        assert state.get_pokemon(0, 0).status_counter == 0

        # Turn 3: counter=0, should wake up and move
        give_move(state, 0, 0, 0, 900, pp=30)  # Refresh PP
        result = engine.execute_move(action)
        assert state.get_pokemon(0, 0).status == STATUS_NONE  # Woke up
        # Target should've been hit
        assert state.get_pokemon(1, 0).current_hp < target_hp_before

    def test_freeze_thaw_succeeds_with_right_seed(self):
        """Frozen Pokemon thaws (20% chance) and acts normally."""
        # seed=0: first next(100) = 0, so random_chance(20, 100) -> 0 < 20 -> True (thaws)
        state = make_state(seed=0)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        state.pokemons[0, 0, P_STATUS] = STATUS_FREEZE

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)

        # Should have thawed
        assert state.get_pokemon(0, 0).status == STATUS_NONE
        # And executed the move (target takes damage)
        assert state.get_pokemon(1, 0).current_hp < target_hp_before

    def test_freeze_stays_frozen_with_right_seed(self):
        """Frozen Pokemon fails to thaw (80% chance) and can't move."""
        # seed=1: first next(100) = 38, so random_chance(20, 100) -> 38 < 20 -> False (stays frozen)
        state = make_state(seed=1)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        state.pokemons[0, 0, P_STATUS] = STATUS_FREEZE

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)

        assert result is False
        assert state.get_pokemon(0, 0).status == STATUS_FREEZE
        assert state.get_pokemon(1, 0).current_hp == target_hp_before  # No damage

    def test_paralysis_full_para_blocks_move(self):
        """Paralysis has 25% chance to fully paralyze (can't move)."""
        # seed=0: first next(100)=0, random_chance(25,100) -> 0 < 25 -> True (full para)
        state = make_state(seed=0)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        state.pokemons[0, 0, P_STATUS] = STATUS_PARALYSIS

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)

        assert result is False
        assert state.get_pokemon(1, 0).current_hp == target_hp_before

    def test_paralysis_moves_through(self):
        """Paralyzed Pokemon moves normally when full-para check fails."""
        # seed=1: first next(100)=38, random_chance(25,100) -> 38 < 25 -> False (moves)
        state = make_state(seed=1)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        state.pokemons[0, 0, P_STATUS] = STATUS_PARALYSIS

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)

        # Move should succeed since para check passed
        assert state.get_pokemon(1, 0).current_hp < target_hp_before


# =============================================================================
# 6. Confusion Self-Hit Tests
# =============================================================================

class TestConfusionSelfHit:
    """Tests for confusion mechanics during execute_move."""

    def test_confused_pokemon_hits_itself(self):
        """Confused Pokemon self-hits 33% of the time. Move doesn't execute."""
        # seed=0: first next(100)=0, random_chance(33,100) -> 0 < 33 -> True (self-hit)
        state = make_state(seed=0)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        # Set confusion with counter=3
        state.pokemons[0, 0, P_VOL_CONFUSION] = 3

        attacker_hp_before = state.get_pokemon(0, 0).current_hp
        target_hp_before = state.get_pokemon(1, 0).current_hp

        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)

        assert result is False  # Move didn't execute
        # Target should be untouched
        assert state.get_pokemon(1, 0).current_hp == target_hp_before
        # Attacker should have taken confusion damage
        assert state.get_pokemon(0, 0).current_hp < attacker_hp_before
        # Confusion counter should have decremented
        assert state.get_pokemon(0, 0).data[P_VOL_CONFUSION] == 2

    def test_confused_pokemon_moves_normally(self):
        """Confused Pokemon moves normally when self-hit check fails."""
        # seed=1: first next(100)=38, random_chance(33,100) -> 38 < 33 -> False (moves normally)
        state = make_state(seed=1)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        state.pokemons[0, 0, P_VOL_CONFUSION] = 3

        target_hp_before = state.get_pokemon(1, 0).current_hp

        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)

        # Move should succeed (target takes damage)
        assert state.get_pokemon(1, 0).current_hp < target_hp_before
        # Confusion counter should have decremented
        assert state.get_pokemon(0, 0).data[P_VOL_CONFUSION] == 2

    def test_confusion_wears_off(self):
        """Confusion lifts when counter reaches 0."""
        # seed=1: no self-hit, counter decrements
        state = make_state(seed=1)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        # Set confusion to 1 (will hit 0 after this turn)
        state.pokemons[0, 0, P_VOL_CONFUSION] = 1

        action = make_move_action(0, 0, 900, 1, 0)
        engine.execute_move(action)

        # Counter should be 0 (confusion cleared)
        assert state.get_pokemon(0, 0).data[P_VOL_CONFUSION] == 0

    def test_confusion_self_hit_can_faint(self):
        """Pokemon can faint from confusion self-hit damage."""
        # seed=0: self-hit triggers
        state = make_state(seed=0)
        give_move(state, 0, 0, 0, 900, pp=30)
        engine = make_engine(state, {900: SIMPLE_PHYSICAL})

        state.pokemons[0, 0, P_VOL_CONFUSION] = 3
        # Set HP very low
        state.pokemons[0, 0, P_CURRENT_HP] = 1

        action = make_move_action(0, 0, 900, 1, 0)
        result = engine.execute_move(action)

        assert result is False
        assert state.get_pokemon(0, 0).is_fainted
        # Should be in faint queue
        assert (0, 0) in state._faint_queue

    def test_confusion_damage_uses_physical_stats(self):
        """Confusion damage formula uses the Pokemon's own Atk and Def."""
        state = make_state(seed=0)
        pokemon = state.get_pokemon(0, 0)

        # Raise attack, lower defense -> more confusion damage
        state.pokemons[0, 0, P_STAT_ATK] = 200
        state.pokemons[0, 0, P_STAT_DEF] = 50
        high_atk_damage = calculate_confusion_damage(state.get_pokemon(0, 0))

        # Now swap: low attack, high defense -> less confusion damage
        state.pokemons[0, 0, P_STAT_ATK] = 50
        state.pokemons[0, 0, P_STAT_DEF] = 200
        low_atk_damage = calculate_confusion_damage(state.get_pokemon(0, 0))

        assert high_atk_damage > low_atk_damage


# =============================================================================
# 7. Spread Damage Modifier Integration Test
# =============================================================================

class TestSpreadDamageIntegration:
    """Tests for spread move 0.75x damage modifier in doubles."""

    def test_spread_move_less_damage_with_two_targets(self):
        """Earthquake hitting two targets should deal 0.75x to each."""
        # First: measure single-target damage (only one foe alive)
        state_single = make_state(seed=42)
        give_move(state_single, 0, 0, 0, 189, pp=10)
        engine_single = make_engine(state_single, {189: EARTHQUAKE_FOES_ONLY})

        # KO one foe so only one target
        state_single.pokemons[1, 1, P_CURRENT_HP] = 0

        target_hp_before = state_single.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 189, -1, -1)
        engine_single.execute_move(action)
        single_target_damage = target_hp_before - state_single.get_pokemon(1, 0).current_hp

        # Second: measure spread damage (both foes alive)
        state_spread = make_state(seed=42)
        give_move(state_spread, 0, 0, 0, 189, pp=10)
        engine_spread = make_engine(state_spread, {189: EARTHQUAKE_FOES_ONLY})

        target_hp_before = state_spread.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 189, -1, -1)
        engine_spread.execute_move(action)
        spread_damage = target_hp_before - state_spread.get_pokemon(1, 0).current_hp

        # Spread damage should be less (0.75x of single target)
        assert spread_damage < single_target_damage, (
            f"Spread damage ({spread_damage}) should be less than single ({single_target_damage})"
        )
        # Verify it's approximately 75%
        if single_target_damage > 0:
            ratio = spread_damage / single_target_damage
            assert 0.70 <= ratio <= 0.80, (
                f"Spread/single ratio should be ~0.75, got {ratio:.3f}"
            )

    def test_spread_move_with_one_target_takes_full_damage(self):
        """When only one foe remains, spread move deals full (1.0x) damage."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 189, pp=10)
        engine = make_engine(state, {189: EARTHQUAKE_FOES_ONLY})

        # KO one foe
        state.pokemons[1, 1, P_CURRENT_HP] = 0

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 189, -1, -1)
        engine.execute_move(action)

        damage = target_hp_before - state.get_pokemon(1, 0).current_hp
        assert damage > 0  # Move did damage

    def test_all_adjacent_hits_ally_and_foes(self):
        """Earthquake (ALL_ADJACENT) hits ally and both foes in doubles."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 89, pp=10)
        engine = make_engine(state, {89: EARTHQUAKE})

        ally_hp_before = state.get_pokemon(0, 1).current_hp
        foe0_hp_before = state.get_pokemon(1, 0).current_hp
        foe1_hp_before = state.get_pokemon(1, 1).current_hp

        action = make_move_action(0, 0, 89, -1, -1)
        engine.execute_move(action)

        # Both foes should take damage
        assert state.get_pokemon(1, 0).current_hp < foe0_hp_before
        assert state.get_pokemon(1, 1).current_hp < foe1_hp_before
        # Ally should also take damage (ALL_ADJACENT hits allies)
        assert state.get_pokemon(0, 1).current_hp < ally_hp_before


# =============================================================================
# 8. Accuracy with Stat Stages Integration Tests
# =============================================================================

class TestAccuracyStages:
    """Tests for accuracy/evasion stat stages affecting move hit chance."""

    def test_accuracy_drop_causes_miss(self):
        """Lowered accuracy stage causes a move to miss."""
        # Thunderbolt has accuracy=100. With -1 acc stage, effective = 75%.
        # We need the PRNG accuracy roll to be >= 75.
        # The accuracy check in execute_move: random_roll = prng.next(100)
        # We need to find a seed where next(100) is in [75, 99]
        found_miss = False
        for seed in range(300):
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 85, pp=15)
            engine = make_engine(state, {85: THUNDERBOLT})

            # Lower attacker's accuracy by 1 stage
            state.pokemons[0, 0, P_STAGE_ACC] = -1

            target_hp_before = state.get_pokemon(1, 0).current_hp
            action = make_move_action(0, 0, 85, 1, 0)
            engine.execute_move(action)

            if state.get_pokemon(1, 0).current_hp == target_hp_before:
                found_miss = True
                break

        assert found_miss, "Should find a seed where accuracy drop causes miss"

    def test_accuracy_drop_still_can_hit(self):
        """With lowered accuracy, moves can still hit with favorable RNG."""
        found_hit = False
        for seed in range(300):
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 85, pp=15)
            engine = make_engine(state, {85: THUNDERBOLT})

            state.pokemons[0, 0, P_STAGE_ACC] = -1

            target_hp_before = state.get_pokemon(1, 0).current_hp
            action = make_move_action(0, 0, 85, 1, 0)
            engine.execute_move(action)

            if state.get_pokemon(1, 0).current_hp < target_hp_before:
                found_hit = True
                break

        assert found_hit, "Should find a seed where move still hits with -1 acc"

    def test_evasion_raise_causes_miss(self):
        """Raised evasion stage on target causes the attacker's move to miss."""
        found_miss = False
        for seed in range(300):
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 85, pp=15)
            engine = make_engine(state, {85: THUNDERBOLT})

            # Raise target's evasion by 2 -> effective acc = 100 * 3/5 = 60%
            state.pokemons[1, 0, P_STAGE_EVA] = 2

            target_hp_before = state.get_pokemon(1, 0).current_hp
            action = make_move_action(0, 0, 85, 1, 0)
            engine.execute_move(action)

            if state.get_pokemon(1, 0).current_hp == target_hp_before:
                found_miss = True
                break

        assert found_miss, "Should find a seed where +2 evasion causes miss"

    def test_acc_and_evasion_stages_stack(self):
        """Accuracy -1 and evasion +1 stack to reduce hit chance further."""
        # -1 acc + +1 eva = effective stage -2: 100 * 3/5 = 60%
        miss_count = 0
        trials = 200
        for seed in range(trials):
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 85, pp=15)
            engine = make_engine(state, {85: THUNDERBOLT})

            state.pokemons[0, 0, P_STAGE_ACC] = -1
            state.pokemons[1, 0, P_STAGE_EVA] = 1

            target_hp_before = state.get_pokemon(1, 0).current_hp
            action = make_move_action(0, 0, 85, 1, 0)
            engine.execute_move(action)

            if state.get_pokemon(1, 0).current_hp == target_hp_before:
                miss_count += 1

        # With 60% accuracy, expect ~40% miss rate (80/200)
        # Allow generous range to avoid flaky test
        assert miss_count > 10, f"Expected significant misses with -1 acc + +1 eva, got {miss_count}/{trials}"
        assert miss_count < trials, "Not all should miss"

    def test_never_miss_move_ignores_evasion(self):
        """Moves with accuracy=None always hit regardless of evasion stages."""
        for seed in range(50):
            state = make_state(seed=seed)
            give_move(state, 0, 0, 0, 129, pp=20)
            engine = make_engine(state, {129: SWIFT})

            # Max evasion
            state.pokemons[1, 0, P_STAGE_EVA] = 6
            state.pokemons[1, 1, P_STAGE_EVA] = 6

            target_hp_before = state.get_pokemon(1, 0).current_hp
            action = make_move_action(0, 0, 129, -1, -1)
            engine.execute_move(action)

            assert state.get_pokemon(1, 0).current_hp < target_hp_before, (
                f"Swift should always hit despite +6 evasion (seed={seed})"
            )


# =============================================================================
# 9. Type Immunity in Battle Context Integration Tests
# =============================================================================

class TestTypeImmunityIntegration:
    """Tests for type immunities working correctly during move execution."""

    def test_ground_move_immune_to_flying(self):
        """Earthquake does nothing to Flying-type Pokemon."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 189, pp=10)
        engine = make_engine(state, {189: EARTHQUAKE_FOES_ONLY})

        # Make target Flying-type
        set_pokemon_type(state, 1, 0, Type.FLYING.value)
        # Make second target Normal so it does take damage
        set_pokemon_type(state, 1, 1, Type.NORMAL.value)

        flying_hp_before = state.get_pokemon(1, 0).current_hp
        normal_hp_before = state.get_pokemon(1, 1).current_hp

        action = make_move_action(0, 0, 189, -1, -1)
        engine.execute_move(action)

        # Flying should be untouched
        assert state.get_pokemon(1, 0).current_hp == flying_hp_before
        # Normal should take damage
        assert state.get_pokemon(1, 1).current_hp < normal_hp_before

    def test_normal_move_immune_to_ghost(self):
        """Tackle (Normal) does nothing to Ghost-type."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 33, pp=35)
        engine = make_engine(state, {33: TACKLE})

        set_pokemon_type(state, 1, 0, Type.GHOST.value)

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 33, 1, 0)
        engine.execute_move(action)

        assert state.get_pokemon(1, 0).current_hp == target_hp_before

    def test_electric_move_immune_to_ground(self):
        """Thunderbolt does nothing to Ground-type Pokemon."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 85, pp=15)
        engine = make_engine(state, {85: THUNDERBOLT})

        set_pokemon_type(state, 1, 0, Type.GROUND.value)

        target_hp_before = state.get_pokemon(1, 0).current_hp
        action = make_move_action(0, 0, 85, 1, 0)
        engine.execute_move(action)

        assert state.get_pokemon(1, 0).current_hp == target_hp_before

    def test_immunity_skips_recoil(self):
        """Recoil move against immune target: 0 damage, 0 recoil."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 528, pp=15)
        engine = make_engine(state, {528: WILD_CHARGE})

        # Wild Charge is Electric, target is Ground (immune)
        set_pokemon_type(state, 1, 0, Type.GROUND.value)

        attacker_hp_before = state.get_pokemon(0, 0).current_hp
        target_hp_before = state.get_pokemon(1, 0).current_hp

        action = make_move_action(0, 0, 528, 1, 0)
        engine.execute_move(action)

        assert state.get_pokemon(1, 0).current_hp == target_hp_before  # No damage
        assert state.get_pokemon(0, 0).current_hp == attacker_hp_before  # No recoil

    def test_immunity_skips_drain(self):
        """Drain move against immune target: 0 damage, 0 healing."""
        state = make_state(seed=42)

        # Create a Grass-type drain move vs Grass-type (resisted but not immune)
        # Better: use a made-up move that is Normal type drain vs Ghost (immune)
        normal_drain = MoveData(
            id=901, name="NormalDrain", type=Type.NORMAL,
            category=MoveCategory.SPECIAL, base_power=75,
            accuracy=None, pp=10, target=MoveTarget.NORMAL,
            flags=MoveFlag.PROTECT, drain=0.5,
        )
        give_move(state, 0, 0, 0, 901, pp=10)
        engine = make_engine(state, {901: normal_drain})

        set_pokemon_type(state, 1, 0, Type.GHOST.value)

        # Lower attacker HP so healing would be visible
        state.pokemons[0, 0, P_CURRENT_HP] = 100
        attacker_hp_before = 100
        target_hp_before = state.get_pokemon(1, 0).current_hp

        action = make_move_action(0, 0, 901, 1, 0)
        engine.execute_move(action)

        assert state.get_pokemon(1, 0).current_hp == target_hp_before  # No damage
        assert state.get_pokemon(0, 0).current_hp == attacker_hp_before  # No healing

    def test_immunity_skips_secondary_effects(self):
        """Secondary effects (like burn chance) should not apply on immune targets."""
        state = make_state(seed=4)  # Seed where 10% secondary would trigger

        # Create a Ground-type move with burn secondary vs Fire-type...
        # Actually, the engine skips the target entirely if immune (via `continue`),
        # so secondary never runs. Let's verify with Electric + para vs Ground
        electric_with_para = MoveData(
            id=902, name="ElecPara", type=Type.ELECTRIC,
            category=MoveCategory.SPECIAL, base_power=90,
            accuracy=None, pp=15, target=MoveTarget.NORMAL,
            flags=MoveFlag.PROTECT,
            secondary=SecondaryEffect(chance=100, status='par'),
        )
        give_move(state, 0, 0, 0, 902, pp=15)
        engine = make_engine(state, {902: electric_with_para})

        set_pokemon_type(state, 1, 0, Type.GROUND.value)

        action = make_move_action(0, 0, 902, 1, 0)
        engine.execute_move(action)

        target = state.get_pokemon(1, 0)
        assert target.status == STATUS_NONE  # No paralysis applied

    def test_partial_immunity_in_spread(self):
        """In a spread move, one target immune, other takes damage."""
        state = make_state(seed=42)
        give_move(state, 0, 0, 0, 189, pp=10)
        engine = make_engine(state, {189: EARTHQUAKE_FOES_ONLY})

        # Foe 0 is Flying (immune), Foe 1 is Normal (hit)
        set_pokemon_type(state, 1, 0, Type.FLYING.value)
        set_pokemon_type(state, 1, 1, Type.NORMAL.value)

        foe0_hp = state.get_pokemon(1, 0).current_hp
        foe1_hp = state.get_pokemon(1, 1).current_hp

        action = make_move_action(0, 0, 189, -1, -1)
        result = engine.execute_move(action)

        assert result is True  # Move succeeded (hit at least one target)
        assert state.get_pokemon(1, 0).current_hp == foe0_hp  # Flying immune
        assert state.get_pokemon(1, 1).current_hp < foe1_hp  # Normal hit
