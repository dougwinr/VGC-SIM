"""Unit tests for core/battle_state.py - BattleState and BattlePRNG."""
import numpy as np
import pytest

from core.battle_state import (
    BattleState,
    BattlePRNG,
    # Side conditions
    SC_REFLECT,
    SC_LIGHT_SCREEN,
    SC_AURORA_VEIL,
    SC_SAFEGUARD,
    SC_MIST,
    SC_TAILWIND,
    SC_LUCKY_CHANT,
    SC_SPIKES,
    SC_TOXIC_SPIKES,
    SC_STEALTH_ROCK,
    SC_STICKY_WEB,
    SC_WIDE_GUARD,
    SC_QUICK_GUARD,
    SC_MAT_BLOCK,
    SC_CRAFTY_SHIELD,
    SC_WISH,
    SC_WISH_AMOUNT,
    SC_HEALING_WISH,
    SC_LUNAR_DANCE,
    SIDE_CONDITION_SIZE,
    # Slot conditions
    SLOT_FUTURE_SIGHT,
    SLOT_FUTURE_SIGHT_DMG,
    SLOT_FUTURE_SIGHT_USER,
    SLOT_DOOM_DESIRE,
    SLOT_DOOM_DESIRE_DMG,
    SLOT_DOOM_DESIRE_USER,
    SLOT_CONDITION_SIZE,
    # Pseudo-weather
    PW_TRICK_ROOM,
    PW_GRAVITY,
    PW_MAGIC_ROOM,
    PW_WONDER_ROOM,
    PW_FAIRY_LOCK,
    PW_MUD_SPORT,
    PW_WATER_SPORT,
    PW_ION_DELUGE,
    PSEUDO_WEATHER_SIZE,
    # Field conditions
    FIELD_WEATHER,
    FIELD_WEATHER_TURNS,
    FIELD_TERRAIN,
    FIELD_TERRAIN_TURNS,
    FIELD_TRICK_ROOM,
    FIELD_GRAVITY,
    FIELD_MAGIC_ROOM,
    FIELD_WONDER_ROOM,
    FIELD_MUD_SPORT,
    FIELD_WATER_SPORT,
    FIELD_ION_DELUGE,
    FIELD_FAIRY_LOCK,
    FIELD_STATE_SIZE,
    # Weather
    WEATHER_NONE,
    WEATHER_SUN,
    WEATHER_RAIN,
    WEATHER_SAND,
    WEATHER_HAIL,
    WEATHER_SNOW,
    WEATHER_HARSH_SUN,
    WEATHER_HEAVY_RAIN,
    WEATHER_STRONG_WINDS,
    WEATHER_NAMES,
    # Terrain
    TERRAIN_NONE,
    TERRAIN_ELECTRIC,
    TERRAIN_GRASSY,
    TERRAIN_MISTY,
    TERRAIN_PSYCHIC,
    TERRAIN_NAMES,
)
from core.layout import (
    POKEMON_ARRAY_SIZE,
    P_SPECIES, P_LEVEL, P_CURRENT_HP, P_STAT_HP,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
)


# =============================================================================
# BattlePRNG Tests
# =============================================================================

class TestBattlePRNG:
    """Tests for the battle PRNG."""

    def test_initialization_with_int_seed(self):
        """Test PRNG initialization with integer seed."""
        prng = BattlePRNG(12345)
        assert prng.get_initial_seed() == 12345
        assert prng.get_seed() == 12345

    def test_initialization_with_tuple_seed(self):
        """Test PRNG initialization with tuple seed."""
        seed = (0x1234, 0x5678, 0x9ABC, 0xDEF0)
        prng = BattlePRNG(seed)
        assert prng.get_initial_seed() == seed

    def test_initialization_with_none_seed(self):
        """Test PRNG initialization with None (auto-generate)."""
        prng = BattlePRNG(None)
        assert prng.get_seed() is not None

    def test_next_returns_bounded_value(self):
        """Test that next() returns values within bounds."""
        prng = BattlePRNG(42)
        for _ in range(100):
            value = prng.next(100)
            assert 0 <= value < 100

    def test_next_default_bound(self):
        """Test next() with default 65536 bound."""
        prng = BattlePRNG(42)
        for _ in range(100):
            value = prng.next()
            assert 0 <= value < 65536

    def test_deterministic_sequence(self):
        """Test that same seed produces same sequence."""
        prng1 = BattlePRNG(12345)
        prng2 = BattlePRNG(12345)

        seq1 = [prng1.next(1000) for _ in range(100)]
        seq2 = [prng2.next(1000) for _ in range(100)]

        assert seq1 == seq2

    def test_different_seeds_different_sequences(self):
        """Test that different seeds produce different sequences."""
        prng1 = BattlePRNG(12345)
        prng2 = BattlePRNG(54321)

        seq1 = [prng1.next(1000) for _ in range(10)]
        seq2 = [prng2.next(1000) for _ in range(10)]

        assert seq1 != seq2

    def test_random_chance(self):
        """Test random_chance probability."""
        prng = BattlePRNG(42)

        # 100% chance should always succeed
        for _ in range(100):
            assert prng.random_chance(1, 1) is True

        # 0% chance should always fail (well, almost - need 0/X)
        prng2 = BattlePRNG(42)
        successes = sum(prng2.random_chance(0, 100) for _ in range(100))
        assert successes == 0

    def test_random_range(self):
        """Test random() returns values in range [min, max]."""
        prng = BattlePRNG(42)
        for _ in range(100):
            value = prng.random(10, 20)
            assert 10 <= value <= 20

    def test_random_single_value(self):
        """Test random() with min == max."""
        prng = BattlePRNG(42)
        for _ in range(10):
            assert prng.random(5, 5) == 5

    def test_sample(self):
        """Test sample returns correct number of items."""
        prng = BattlePRNG(42)
        population = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        sample = prng.sample(population, 3)
        assert len(sample) == 3
        assert all(x in population for x in sample)

    def test_sample_unique_items(self):
        """Test sample returns unique items."""
        prng = BattlePRNG(42)
        population = [1, 2, 3, 4, 5]

        sample = prng.sample(population, 4)
        assert len(sample) == len(set(sample))  # All unique

    def test_sample_more_than_population(self):
        """Test sample with k > population size."""
        prng = BattlePRNG(42)
        population = [1, 2, 3]

        sample = prng.sample(population, 10)
        assert len(sample) == 3  # Can only return population size

    def test_shuffle(self):
        """Test shuffle modifies list in place."""
        prng = BattlePRNG(42)
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        original = items.copy()

        prng.shuffle(items)

        # Should have same elements
        assert sorted(items) == sorted(original)
        # Should be shuffled (very unlikely to be same order)
        # Note: There's a 1/10! chance this fails
        assert items != original

    def test_shuffle_deterministic(self):
        """Test shuffle is deterministic with same seed."""
        prng1 = BattlePRNG(42)
        prng2 = BattlePRNG(42)

        items1 = [1, 2, 3, 4, 5]
        items2 = [1, 2, 3, 4, 5]

        prng1.shuffle(items1)
        prng2.shuffle(items2)

        assert items1 == items2

    def test_clone(self):
        """Test clone creates independent copy with same state."""
        prng1 = BattlePRNG(42)
        prng1.next()  # Advance state
        prng1.next()

        prng2 = prng1.clone()

        # Should have same state
        assert prng1.get_seed() == prng2.get_seed()

        # Should produce same sequence
        seq1 = [prng1.next(100) for _ in range(10)]
        seq2 = [prng2.next(100) for _ in range(10)]
        assert seq1 == seq2

    def test_clone_independence(self):
        """Test that cloned PRNG is independent."""
        prng1 = BattlePRNG(42)
        prng2 = prng1.clone()

        # Advance only prng1
        prng1.next()
        prng1.next()
        prng1.next()

        # prng2 should still be at original state
        assert prng1.get_seed() != prng2.get_seed()


# =============================================================================
# BattleState Initialization Tests
# =============================================================================

class TestBattleStateInit:
    """Tests for BattleState initialization."""

    def test_default_initialization(self):
        """Test default battle state initialization."""
        state = BattleState()

        assert state.num_sides == 2
        assert state.team_size == 6
        assert state.active_slots == 2
        assert state.turn == 0
        assert state.ended is False
        assert state.winner == -1

    def test_custom_initialization(self):
        """Test battle state with custom parameters."""
        state = BattleState(
            num_sides=2,
            team_size=4,
            active_slots=1,
            seed=12345,
        )

        assert state.team_size == 4
        assert state.active_slots == 1
        assert state.prng.get_initial_seed() == 12345

    def test_pokemon_array_shape(self):
        """Test Pokemon array has correct shape."""
        state = BattleState(num_sides=2, team_size=6, active_slots=2)

        assert state.pokemons.shape == (2, 6, POKEMON_ARRAY_SIZE)
        assert state.pokemons.dtype == np.int32

    def test_active_array_shape(self):
        """Test active array has correct shape."""
        state = BattleState(num_sides=2, team_size=6, active_slots=2)

        assert state.active.shape == (2, 2)
        assert np.all(state.active == -1)  # Initially empty

    def test_side_conditions_shape(self):
        """Test side conditions array has correct shape."""
        state = BattleState()

        assert state.side_conditions.shape == (2, SIDE_CONDITION_SIZE)
        assert np.all(state.side_conditions == 0)

    def test_field_shape(self):
        """Test field array has correct shape."""
        state = BattleState()

        assert state.field.shape == (FIELD_STATE_SIZE,)
        assert np.all(state.field == 0)


# =============================================================================
# BattleState Pokemon Access Tests
# =============================================================================

class TestBattleStatePokemonAccess:
    """Tests for Pokemon access methods."""

    def test_get_pokemon(self):
        """Test getting Pokemon wrapper."""
        state = BattleState()
        state.pokemons[0, 0, P_SPECIES] = 25  # Pikachu
        state.pokemons[0, 0, P_LEVEL] = 50

        pokemon = state.get_pokemon(0, 0)
        assert pokemon.species_id == 25
        assert pokemon.level == 50

    def test_get_pokemon_returns_view(self):
        """Test that get_pokemon returns a view into the array."""
        state = BattleState()
        pokemon = state.get_pokemon(0, 0)

        # Modify through Pokemon
        pokemon.data[P_LEVEL] = 75

        # Should be reflected in state
        assert state.pokemons[0, 0, P_LEVEL] == 75

    def test_set_pokemon(self):
        """Test setting Pokemon data."""
        state = BattleState()

        from core.pokemon import Pokemon
        pokemon = Pokemon()
        pokemon.data[P_SPECIES] = 1  # Bulbasaur
        pokemon.data[P_LEVEL] = 100

        state.set_pokemon(0, 1, pokemon)

        assert state.pokemons[0, 1, P_SPECIES] == 1
        assert state.pokemons[0, 1, P_LEVEL] == 100

    def test_set_pokemon_copies_data(self):
        """Test that set_pokemon copies data (not references)."""
        state = BattleState()

        from core.pokemon import Pokemon
        pokemon = Pokemon()
        pokemon.data[P_LEVEL] = 50

        state.set_pokemon(0, 0, pokemon)

        # Modify original
        pokemon.data[P_LEVEL] = 100

        # State should still have original value
        assert state.pokemons[0, 0, P_LEVEL] == 50

    def test_get_active_pokemon(self):
        """Test getting active Pokemon."""
        state = BattleState()
        state.pokemons[0, 0, P_SPECIES] = 25
        state.pokemons[0, 0, P_STAT_HP] = 100
        state.pokemons[0, 0, P_CURRENT_HP] = 100
        state.active[0, 0] = 0  # Slot 0 is active

        active = state.get_active_pokemon(0, 0)
        assert active is not None
        assert active.species_id == 25

    def test_get_active_pokemon_empty_slot(self):
        """Test getting active Pokemon from empty slot."""
        state = BattleState()

        active = state.get_active_pokemon(0, 0)
        assert active is None

    def test_get_team(self):
        """Test getting full team."""
        state = BattleState()
        for i in range(6):
            state.pokemons[0, i, P_SPECIES] = i + 1

        team = state.get_team(0)
        assert len(team) == 6
        for i, pokemon in enumerate(team):
            assert pokemon.species_id == i + 1

    def test_get_active_indices(self):
        """Test getting active Pokemon indices."""
        state = BattleState()
        state.active[0, 0] = 0
        state.active[0, 1] = 2

        indices = state.get_active_indices(0)
        assert indices == [0, 2]

    def test_is_pokemon_active(self):
        """Test checking if Pokemon is active."""
        state = BattleState()
        state.active[0, 0] = 1

        assert state.is_pokemon_active(0, 1) is True
        assert state.is_pokemon_active(0, 0) is False
        assert state.is_pokemon_active(0, 2) is False


# =============================================================================
# BattleState Side Condition Tests
# =============================================================================

class TestBattleStateSideConditions:
    """Tests for side condition methods."""

    def test_get_set_side_condition(self):
        """Test getting and setting side conditions."""
        state = BattleState()

        state.set_side_condition(0, SC_REFLECT, 5)
        assert state.get_side_condition(0, SC_REFLECT) == 5

    def test_has_reflect(self):
        """Test Reflect check."""
        state = BattleState()
        assert state.has_reflect(0) == False

        state.set_side_condition(0, SC_REFLECT, 3)
        assert state.has_reflect(0) == True

    def test_has_light_screen(self):
        """Test Light Screen check."""
        state = BattleState()
        assert state.has_light_screen(0) == False

        state.set_side_condition(0, SC_LIGHT_SCREEN, 5)
        assert state.has_light_screen(0) == True

    def test_has_aurora_veil(self):
        """Test Aurora Veil check."""
        state = BattleState()
        assert state.has_aurora_veil(1) == False

        state.set_side_condition(1, SC_AURORA_VEIL, 5)
        assert state.has_aurora_veil(1) == True

    def test_get_spikes_layers(self):
        """Test Spikes layer count."""
        state = BattleState()
        assert state.get_spikes_layers(0) == 0

        state.set_side_condition(0, SC_SPIKES, 2)
        assert state.get_spikes_layers(0) == 2

    def test_has_stealth_rock(self):
        """Test Stealth Rock check."""
        state = BattleState()
        assert state.has_stealth_rock(0) == False

        state.set_side_condition(0, SC_STEALTH_ROCK, 1)
        assert state.has_stealth_rock(0) == True


# =============================================================================
# BattleState Field Condition Tests
# =============================================================================

class TestBattleStateFieldConditions:
    """Tests for field condition methods."""

    def test_weather_property(self):
        """Test weather property getter/setter."""
        state = BattleState()
        assert state.weather == WEATHER_NONE

        state.weather = WEATHER_SUN
        assert state.weather == WEATHER_SUN

    def test_set_weather(self):
        """Test set_weather with duration."""
        state = BattleState()

        state.set_weather(WEATHER_RAIN, 5)

        assert state.weather == WEATHER_RAIN
        assert state.weather_turns == 5

    def test_set_weather_permanent(self):
        """Test permanent weather."""
        state = BattleState()

        state.set_weather(WEATHER_SAND, -1)

        assert state.weather == WEATHER_SAND
        assert state.weather_turns == -1

    def test_clear_weather(self):
        """Test clearing weather."""
        state = BattleState()
        state.set_weather(WEATHER_HAIL, 5)

        state.clear_weather()

        assert state.weather == WEATHER_NONE
        assert state.weather_turns == 0

    def test_terrain_property(self):
        """Test terrain property getter/setter."""
        state = BattleState()
        assert state.terrain == TERRAIN_NONE

        state.terrain = TERRAIN_ELECTRIC
        assert state.terrain == TERRAIN_ELECTRIC

    def test_weather_turns_setter(self):
        """Test weather_turns property setter."""
        state = BattleState()
        state.weather = WEATHER_RAIN
        state.weather_turns = 8

        assert state.weather_turns == 8

    def test_terrain_turns_setter(self):
        """Test terrain_turns property setter."""
        state = BattleState()
        state.terrain = TERRAIN_GRASSY
        state.terrain_turns = 7

        assert state.terrain_turns == 7

    def test_set_terrain(self):
        """Test set_terrain with duration."""
        state = BattleState()

        state.set_terrain(TERRAIN_GRASSY, 5)

        assert state.terrain == TERRAIN_GRASSY
        assert state.terrain_turns == 5

    def test_clear_terrain(self):
        """Test clearing terrain."""
        state = BattleState()
        state.set_terrain(TERRAIN_MISTY, 3)

        state.clear_terrain()

        assert state.terrain == TERRAIN_NONE
        assert state.terrain_turns == 0

    def test_trick_room(self):
        """Test Trick Room methods."""
        state = BattleState()
        assert state.trick_room == False

        state.set_trick_room(5)
        assert state.trick_room == True
        assert state.trick_room_turns == 5

    def test_gravity(self):
        """Test Gravity methods."""
        state = BattleState()
        assert state.gravity == False

        state.set_gravity(5)
        assert state.gravity == True
        assert state.gravity_turns == 5


# =============================================================================
# BattleState Battle Flow Tests
# =============================================================================

class TestBattleStateBattleFlow:
    """Tests for battle flow methods."""

    def test_start_battle(self):
        """Test battle start initialization."""
        state = BattleState()
        # Set up valid Pokemon
        for side in range(2):
            for slot in range(2):
                state.pokemons[side, slot, P_STAT_HP] = 100
                state.pokemons[side, slot, P_CURRENT_HP] = 100

        state.start_battle()

        assert state.turn == 1
        assert state.ended is False
        # Active slots should be filled
        assert state.active[0, 0] == 0
        assert state.active[1, 0] == 0

    def test_advance_turn(self):
        """Test turn advancement."""
        state = BattleState()
        state.turn = 1

        state.advance_turn()

        assert state.turn == 2

    def test_advance_turn_decrements_weather(self):
        """Test that turn advancement decrements weather."""
        state = BattleState()
        state.turn = 1
        state.set_weather(WEATHER_SUN, 2)

        state.advance_turn()

        assert state.weather == WEATHER_SUN
        assert state.weather_turns == 1

        state.advance_turn()

        assert state.weather == WEATHER_NONE
        assert state.weather_turns == 0

    def test_advance_turn_decrements_terrain(self):
        """Test that turn advancement decrements terrain."""
        state = BattleState()
        state.turn = 1
        state.set_terrain(TERRAIN_ELECTRIC, 1)

        state.advance_turn()

        assert state.terrain == TERRAIN_NONE

    def test_advance_turn_decrements_screens(self):
        """Test that turn advancement decrements screens."""
        state = BattleState()
        state.turn = 1
        state.set_side_condition(0, SC_REFLECT, 2)
        state.set_side_condition(0, SC_LIGHT_SCREEN, 1)

        state.advance_turn()

        assert state.get_side_condition(0, SC_REFLECT) == 1
        assert state.get_side_condition(0, SC_LIGHT_SCREEN) == 0

    def test_advance_turn_resets_protection_moves(self):
        """Test that turn advancement resets protection moves."""
        state = BattleState()
        state.set_side_condition(0, SC_WIDE_GUARD, 1)
        state.set_side_condition(0, SC_QUICK_GUARD, 1)

        state.advance_turn()

        assert state.get_side_condition(0, SC_WIDE_GUARD) == 0
        assert state.get_side_condition(0, SC_QUICK_GUARD) == 0

    def test_check_win_condition_no_winner(self):
        """Test win condition when battle continues."""
        state = BattleState()
        # Both sides have alive Pokemon
        state.pokemons[0, 0, P_CURRENT_HP] = 100
        state.pokemons[1, 0, P_CURRENT_HP] = 100

        result = state.check_win_condition()

        assert result is None
        assert state.ended is False

    def test_check_win_condition_side0_wins(self):
        """Test win condition when side 0 wins."""
        state = BattleState()
        state.pokemons[0, 0, P_CURRENT_HP] = 100
        # Side 1 all fainted
        for i in range(6):
            state.pokemons[1, i, P_CURRENT_HP] = 0

        result = state.check_win_condition()

        assert result == 0
        assert state.ended is True
        assert state.winner == 0

    def test_check_win_condition_side1_wins(self):
        """Test win condition when side 1 wins."""
        state = BattleState()
        state.pokemons[1, 0, P_CURRENT_HP] = 100
        # Side 0 all fainted
        for i in range(6):
            state.pokemons[0, i, P_CURRENT_HP] = 0

        result = state.check_win_condition()

        assert result == 1
        assert state.ended is True
        assert state.winner == 1

    def test_check_win_condition_draw(self):
        """Test win condition for draw (both sides eliminated)."""
        state = BattleState()
        # Both sides all fainted
        for side in range(2):
            for slot in range(6):
                state.pokemons[side, slot, P_CURRENT_HP] = 0

        result = state.check_win_condition()

        assert result == -1
        assert state.ended is True
        assert state.winner == -1


# =============================================================================
# BattleState Switch Tests
# =============================================================================

class TestBattleStateSwitch:
    """Tests for Pokemon switching methods."""

    def test_get_fainted_actives(self):
        """Test getting fainted active Pokemon."""
        state = BattleState()
        state.active[0, 0] = 0
        state.active[0, 1] = 1
        state.pokemons[0, 0, P_CURRENT_HP] = 0  # Fainted
        state.pokemons[0, 1, P_CURRENT_HP] = 50  # Alive

        fainted = state.get_fainted_actives(0)

        assert fainted == [0]

    def test_get_available_switches(self):
        """Test getting available Pokemon to switch in."""
        state = BattleState()
        state.active[0, 0] = 0
        state.active[0, 1] = 1
        # Slots 0, 1 are active; slots 2, 3 have HP; slots 4, 5 fainted
        state.pokemons[0, 2, P_CURRENT_HP] = 100
        state.pokemons[0, 3, P_CURRENT_HP] = 100
        state.pokemons[0, 4, P_CURRENT_HP] = 0
        state.pokemons[0, 5, P_CURRENT_HP] = 0

        available = state.get_available_switches(0)

        assert available == [2, 3]

    def test_switch_pokemon_success(self):
        """Test successful Pokemon switch."""
        state = BattleState()
        state.active[0, 0] = 0
        state.pokemons[0, 0, P_CURRENT_HP] = 50
        state.pokemons[0, 2, P_CURRENT_HP] = 100

        result = state.switch_pokemon(0, 0, 2)

        assert result is True
        assert state.active[0, 0] == 2

    def test_switch_pokemon_resets_stages(self):
        """Test that switching resets stat stages."""
        state = BattleState()
        state.active[0, 0] = 0
        state.pokemons[0, 0, P_CURRENT_HP] = 50
        state.pokemons[0, 0, P_STAGE_ATK] = 2
        state.pokemons[0, 2, P_CURRENT_HP] = 100

        state.switch_pokemon(0, 0, 2)

        # Old Pokemon's stages should be reset
        assert state.pokemons[0, 0, P_STAGE_ATK] == 0

    def test_switch_pokemon_invalid_target(self):
        """Test switching to invalid slot."""
        state = BattleState()

        result = state.switch_pokemon(0, 0, 10)  # Invalid slot

        assert result is False

    def test_switch_pokemon_invalid_active_slot(self):
        """Test switching with invalid active slot."""
        state = BattleState()

        # Test negative active slot
        result = state.switch_pokemon(0, -1, 2)
        assert result is False

        # Test active slot >= active_slots
        result = state.switch_pokemon(0, 10, 2)
        assert result is False

    def test_switch_pokemon_fainted_target(self):
        """Test switching to fainted Pokemon."""
        state = BattleState()
        state.active[0, 0] = 0
        state.pokemons[0, 0, P_CURRENT_HP] = 50
        state.pokemons[0, 2, P_CURRENT_HP] = 0  # Fainted

        result = state.switch_pokemon(0, 0, 2)

        assert result is False
        assert state.active[0, 0] == 0  # Unchanged

    def test_switch_pokemon_already_active(self):
        """Test switching to already active Pokemon."""
        state = BattleState()
        state.active[0, 0] = 0
        state.active[0, 1] = 1
        state.pokemons[0, 0, P_CURRENT_HP] = 50
        state.pokemons[0, 1, P_CURRENT_HP] = 100

        result = state.switch_pokemon(0, 0, 1)  # Already active in slot 1

        assert result is False


# =============================================================================
# BattleState Utility Tests
# =============================================================================

class TestBattleStateUtility:
    """Tests for utility methods."""

    def test_copy_creates_independent_state(self):
        """Test that copy creates an independent copy."""
        state = BattleState(seed=42)
        state.turn = 5
        state.pokemons[0, 0, P_SPECIES] = 25
        state.set_weather(WEATHER_SUN, 3)

        copied = state.copy()

        # Modify original
        state.turn = 10
        state.pokemons[0, 0, P_SPECIES] = 1
        state.set_weather(WEATHER_RAIN, 5)

        # Copy should be unchanged
        assert copied.turn == 5
        assert copied.pokemons[0, 0, P_SPECIES] == 25
        assert copied.weather == WEATHER_SUN

    def test_copy_prng_independent(self):
        """Test that copied PRNG is independent."""
        state = BattleState(seed=42)
        copied = state.copy()

        # Advance original PRNG
        state.prng.next()
        state.prng.next()
        state.prng.next()

        # Copy's PRNG should be at original position
        assert state.prng.get_seed() != copied.prng.get_seed()

    def test_log_action(self):
        """Test action logging."""
        state = BattleState()

        state.log_action("move 1 thunderbolt")
        state.log_action("switch 2 3")

        assert len(state.action_log) == 2
        assert state.action_log[0] == "move 1 thunderbolt"

    def test_log_message(self):
        """Test message logging."""
        state = BattleState()

        state.log_message("Pikachu used Thunderbolt!")
        state.log_message("It's super effective!")

        assert len(state.message_log) == 2

    def test_get_observation(self):
        """Test observation extraction."""
        state = BattleState()

        obs = state.get_observation(0)

        # Should be a flat array
        assert isinstance(obs, np.ndarray)
        assert obs.ndim == 1

    def test_repr(self):
        """Test string representation."""
        state = BattleState()
        state.turn = 5
        state.set_weather(WEATHER_RAIN, 3)

        repr_str = repr(state)

        assert "turn=5" in repr_str
        assert "rain" in repr_str


# =============================================================================
# Weather and Terrain Constants Tests
# =============================================================================

class TestWeatherTerrainConstants:
    """Tests for weather and terrain constants."""

    def test_weather_names_complete(self):
        """Test that all weather types have names."""
        for weather_id in range(6):  # 0-5 for standard weather
            assert weather_id in WEATHER_NAMES

    def test_terrain_names_complete(self):
        """Test that all terrain types have names."""
        for terrain_id in range(5):  # 0-4 for terrains
            assert terrain_id in TERRAIN_NAMES

    def test_weather_constants(self):
        """Test weather constant values."""
        assert WEATHER_NONE == 0
        assert WEATHER_SUN == 1
        assert WEATHER_RAIN == 2
        assert WEATHER_SAND == 3
        assert WEATHER_HAIL == 4
        assert WEATHER_SNOW == 5

    def test_terrain_constants(self):
        """Test terrain constant values."""
        assert TERRAIN_NONE == 0
        assert TERRAIN_ELECTRIC == 1
        assert TERRAIN_GRASSY == 2
        assert TERRAIN_MISTY == 3
        assert TERRAIN_PSYCHIC == 4


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================

class TestBattleStateEdgeCases:
    """Edge case and integration tests."""

    def test_singles_battle_config(self):
        """Test singles battle configuration."""
        state = BattleState(num_sides=2, team_size=6, active_slots=1)

        assert state.active_slots == 1
        assert state.active.shape == (2, 1)

    def test_ffa_battle_config(self):
        """Test free-for-all configuration."""
        state = BattleState(num_sides=4, team_size=3, active_slots=1)

        assert state.num_sides == 4
        assert state.pokemons.shape == (4, 3, POKEMON_ARRAY_SIZE)

    def test_full_battle_simulation_setup(self):
        """Test setting up a complete battle."""
        state = BattleState(seed=12345)

        # Set up teams
        for side in range(2):
            for slot in range(6):
                state.pokemons[side, slot, P_SPECIES] = side * 6 + slot + 1
                state.pokemons[side, slot, P_LEVEL] = 50
                state.pokemons[side, slot, P_STAT_HP] = 100
                state.pokemons[side, slot, P_CURRENT_HP] = 100

        # Start battle
        state.start_battle()

        # Set up field
        state.set_weather(WEATHER_SUN, 5)
        state.set_terrain(TERRAIN_GRASSY, 5)
        state.set_side_condition(0, SC_REFLECT, 5)

        # Verify
        assert state.turn == 1
        assert state.weather == WEATHER_SUN
        assert state.terrain == TERRAIN_GRASSY
        assert state.has_reflect(0)

    def test_replay_determinism(self):
        """Test that same seed produces same random sequence."""
        state1 = BattleState(seed=42)
        state2 = BattleState(seed=42)

        # Perform identical operations
        for s in [state1, state2]:
            for _ in range(10):
                s.prng.next(100)

        assert state1.prng.get_seed() == state2.prng.get_seed()


# =============================================================================
# Slot Condition Tests
# =============================================================================

class TestBattleStateSlotConditions:
    """Tests for slot condition methods (Future Sight, Doom Desire, etc.)."""

    def test_slot_conditions_array_shape(self):
        """Test slot conditions array has correct shape."""
        state = BattleState()

        assert state.slot_conditions.shape == (2, 2, SLOT_CONDITION_SIZE)
        assert np.all(state.slot_conditions == 0)

    def test_get_set_slot_condition(self):
        """Test getting and setting slot conditions."""
        state = BattleState()

        state.set_slot_condition(0, 0, SLOT_FUTURE_SIGHT, 3)
        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 3

    def test_has_future_sight(self):
        """Test Future Sight check."""
        state = BattleState()
        assert state.has_future_sight(0, 0) == False

        state.set_slot_condition(0, 0, SLOT_FUTURE_SIGHT, 2)
        assert state.has_future_sight(0, 0) == True

    def test_set_future_sight(self):
        """Test setting up Future Sight."""
        state = BattleState()

        state.set_future_sight(
            target_side=0, target_slot=0,
            turns=3, damage=150,
            user_side=1, user_slot=2
        )

        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 3
        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT_DMG) == 150
        # User encoded as side * team_size + slot = 1 * 6 + 2 = 8
        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT_USER) == 8

    def test_get_future_sight_damage(self):
        """Test getting Future Sight damage."""
        state = BattleState()
        state.set_future_sight(0, 0, 2, 200, 1, 0)

        assert state.get_future_sight_damage(0, 0) == 200

    def test_has_doom_desire(self):
        """Test Doom Desire check."""
        state = BattleState()
        assert state.has_doom_desire(0, 1) == False

        state.set_slot_condition(0, 1, SLOT_DOOM_DESIRE, 2)
        assert state.has_doom_desire(0, 1) == True

    def test_set_doom_desire(self):
        """Test setting up Doom Desire."""
        state = BattleState()

        state.set_doom_desire(
            target_side=1, target_slot=0,
            turns=2, damage=180,
            user_side=0, user_slot=0
        )

        assert state.get_slot_condition(1, 0, SLOT_DOOM_DESIRE) == 2
        assert state.get_doom_desire_damage(1, 0) == 180
        # User encoded as 0 * 6 + 0 = 0
        assert state.get_slot_condition(1, 0, SLOT_DOOM_DESIRE_USER) == 0

    def test_clear_slot_conditions(self):
        """Test clearing slot conditions."""
        state = BattleState()
        state.set_future_sight(0, 0, 3, 150, 1, 0)
        state.set_slot_condition(0, 0, SLOT_DOOM_DESIRE, 2)

        state.clear_slot_conditions(0, 0)

        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 0
        assert state.get_slot_condition(0, 0, SLOT_DOOM_DESIRE) == 0

    def test_advance_turn_decrements_future_sight(self):
        """Test that turn advancement decrements Future Sight."""
        state = BattleState()
        state.set_future_sight(0, 0, 3, 150, 1, 0)

        state.advance_turn()

        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 2

    def test_advance_turn_decrements_doom_desire(self):
        """Test that turn advancement decrements Doom Desire."""
        state = BattleState()
        state.set_doom_desire(1, 0, 2, 180, 0, 0)

        state.advance_turn()

        assert state.get_slot_condition(1, 0, SLOT_DOOM_DESIRE) == 1

        state.advance_turn()

        assert state.get_slot_condition(1, 0, SLOT_DOOM_DESIRE) == 0

    def test_future_sight_and_doom_desire_both_active(self):
        """Test having both Future Sight and Doom Desire on same slot."""
        state = BattleState()
        state.set_future_sight(0, 0, 3, 150, 1, 0)
        state.set_doom_desire(0, 0, 2, 180, 1, 1)

        assert state.has_future_sight(0, 0)
        assert state.has_doom_desire(0, 0)

    def test_slot_conditions_independent_per_slot(self):
        """Test slot conditions are independent between slots."""
        state = BattleState()
        state.set_future_sight(0, 0, 3, 100, 1, 0)
        state.set_future_sight(0, 1, 2, 200, 1, 1)

        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 3
        assert state.get_slot_condition(0, 1, SLOT_FUTURE_SIGHT) == 2
        assert state.get_future_sight_damage(0, 0) == 100
        assert state.get_future_sight_damage(0, 1) == 200


# =============================================================================
# Pseudo-Weather and Field Effect Tests
# =============================================================================

class TestBattleStatePseudoWeather:
    """Tests for pseudo-weather and additional field conditions."""

    def test_pseudo_weather_array_shape(self):
        """Test pseudo-weather array has correct shape."""
        state = BattleState()

        assert state.pseudo_weather.shape == (PSEUDO_WEATHER_SIZE,)
        assert np.all(state.pseudo_weather == 0)

    def test_get_set_pseudo_weather(self):
        """Test getting and setting pseudo-weather."""
        state = BattleState()

        state.set_pseudo_weather(PW_TRICK_ROOM, 5)
        assert state.get_pseudo_weather(PW_TRICK_ROOM) == 5

    def test_magic_room(self):
        """Test Magic Room methods."""
        state = BattleState()
        assert state.has_magic_room() == False

        state.set_magic_room(5)
        assert state.has_magic_room() == True
        assert state.field[FIELD_MAGIC_ROOM] == 5

    def test_wonder_room(self):
        """Test Wonder Room methods."""
        state = BattleState()
        assert state.has_wonder_room() == False

        state.set_wonder_room(5)
        assert state.has_wonder_room() == True
        assert state.field[FIELD_WONDER_ROOM] == 5

    def test_fairy_lock(self):
        """Test Fairy Lock methods."""
        state = BattleState()
        assert state.has_fairy_lock() == False

        state.set_fairy_lock(2)
        assert state.has_fairy_lock() == True
        assert state.field[FIELD_FAIRY_LOCK] == 2

    def test_mud_sport(self):
        """Test Mud Sport methods."""
        state = BattleState()
        assert state.has_mud_sport() == False

        state.set_mud_sport(True)
        assert state.has_mud_sport() == True

        state.set_mud_sport(False)
        assert state.has_mud_sport() == False

    def test_water_sport(self):
        """Test Water Sport methods."""
        state = BattleState()
        assert state.has_water_sport() == False

        state.set_water_sport(True)
        assert state.has_water_sport() == True

        state.set_water_sport(False)
        assert state.has_water_sport() == False

    def test_ion_deluge(self):
        """Test Ion Deluge methods."""
        state = BattleState()
        assert state.has_ion_deluge() == False

        state.set_ion_deluge(True)
        assert state.has_ion_deluge() == True

        state.set_ion_deluge(False)
        assert state.has_ion_deluge() == False

    def test_advance_turn_decrements_magic_room(self):
        """Test that turn advancement decrements Magic Room."""
        state = BattleState()
        state.set_magic_room(2)

        state.advance_turn()
        assert state.field[FIELD_MAGIC_ROOM] == 1

        state.advance_turn()
        assert state.field[FIELD_MAGIC_ROOM] == 0
        assert state.has_magic_room() == False

    def test_advance_turn_decrements_wonder_room(self):
        """Test that turn advancement decrements Wonder Room."""
        state = BattleState()
        state.set_wonder_room(1)

        state.advance_turn()
        assert state.has_wonder_room() == False

    def test_advance_turn_decrements_fairy_lock(self):
        """Test that turn advancement decrements Fairy Lock."""
        state = BattleState()
        state.set_fairy_lock(2)

        state.advance_turn()
        assert state.field[FIELD_FAIRY_LOCK] == 1

    def test_advance_turn_resets_ion_deluge(self):
        """Test that turn advancement resets Ion Deluge."""
        state = BattleState()
        state.set_ion_deluge(True)

        assert state.has_ion_deluge() == True

        state.advance_turn()
        assert state.has_ion_deluge() == False


# =============================================================================
# Additional Side Condition Tests
# =============================================================================

class TestBattleStateAdditionalSideConditions:
    """Tests for additional side condition methods."""

    def test_has_toxic_spikes(self):
        """Test Toxic Spikes check."""
        state = BattleState()
        assert state.has_toxic_spikes(0) == False

        state.set_side_condition(0, SC_TOXIC_SPIKES, 1)
        assert state.has_toxic_spikes(0) == True

    def test_get_toxic_spikes_layers(self):
        """Test getting Toxic Spikes layers."""
        state = BattleState()
        assert state.get_toxic_spikes_layers(0) == 0

        state.set_side_condition(0, SC_TOXIC_SPIKES, 2)
        assert state.get_toxic_spikes_layers(0) == 2

    def test_has_sticky_web(self):
        """Test Sticky Web check."""
        state = BattleState()
        assert state.has_sticky_web(1) == False

        state.set_side_condition(1, SC_STICKY_WEB, 1)
        assert state.has_sticky_web(1) == True

    def test_has_tailwind(self):
        """Test Tailwind check."""
        state = BattleState()
        assert state.has_tailwind(0) == False

        state.set_side_condition(0, SC_TAILWIND, 4)
        assert state.has_tailwind(0) == True

    def test_has_safeguard(self):
        """Test Safeguard check."""
        state = BattleState()
        assert state.has_safeguard(0) == False

        state.set_side_condition(0, SC_SAFEGUARD, 5)
        assert state.has_safeguard(0) == True

    def test_advance_turn_decrements_lucky_chant(self):
        """Test that turn advancement decrements Lucky Chant."""
        state = BattleState()
        state.set_side_condition(0, SC_LUCKY_CHANT, 2)

        state.advance_turn()
        assert state.get_side_condition(0, SC_LUCKY_CHANT) == 1

    def test_advance_turn_resets_mat_block(self):
        """Test that turn advancement resets Mat Block."""
        state = BattleState()
        state.set_side_condition(0, SC_MAT_BLOCK, 1)

        state.advance_turn()
        assert state.get_side_condition(0, SC_MAT_BLOCK) == 0

    def test_advance_turn_resets_crafty_shield(self):
        """Test that turn advancement resets Crafty Shield."""
        state = BattleState()
        state.set_side_condition(0, SC_CRAFTY_SHIELD, 1)

        state.advance_turn()
        assert state.get_side_condition(0, SC_CRAFTY_SHIELD) == 0

    def test_wish_amount(self):
        """Test Wish with amount."""
        state = BattleState()
        state.set_side_condition(0, SC_WISH, 2)
        state.set_side_condition(0, SC_WISH_AMOUNT, 100)

        assert state.get_side_condition(0, SC_WISH) == 2
        assert state.get_side_condition(0, SC_WISH_AMOUNT) == 100

    def test_healing_wish_pending(self):
        """Test Healing Wish pending."""
        state = BattleState()
        state.set_side_condition(0, SC_HEALING_WISH, 1)

        assert state.get_side_condition(0, SC_HEALING_WISH) == 1

    def test_lunar_dance_pending(self):
        """Test Lunar Dance pending."""
        state = BattleState()
        state.set_side_condition(1, SC_LUNAR_DANCE, 1)

        assert state.get_side_condition(1, SC_LUNAR_DANCE) == 1


# =============================================================================
# State Variables Tests
# =============================================================================

class TestBattleStateVariables:
    """Tests for additional state variables."""

    def test_last_move_initialized(self):
        """Test last_move is initialized to 0."""
        state = BattleState()
        assert state.last_move == 0

    def test_last_move_assignment(self):
        """Test last_move can be assigned."""
        state = BattleState()
        state.last_move = 100

        assert state.last_move == 100

    def test_last_damage_initialized(self):
        """Test last_damage is initialized to 0."""
        state = BattleState()
        assert state.last_damage == 0

    def test_last_damage_assignment(self):
        """Test last_damage can be assigned."""
        state = BattleState()
        state.last_damage = 150

        assert state.last_damage == 150

    def test_request_state_initialized(self):
        """Test request_state is initialized to empty string."""
        state = BattleState()
        assert state.request_state == ''

    def test_request_state_assignment(self):
        """Test request_state can be assigned."""
        state = BattleState()
        state.request_state = 'move'

        assert state.request_state == 'move'

    def test_request_state_values(self):
        """Test various request_state values."""
        state = BattleState()

        for value in ['', 'move', 'switch', 'teampreview']:
            state.request_state = value
            assert state.request_state == value


# =============================================================================
# Extended Copy Tests
# =============================================================================

class TestBattleStateCopyExtended:
    """Extended tests for copy() method with new fields."""

    def test_copy_includes_slot_conditions(self):
        """Test that copy includes slot conditions."""
        state = BattleState()
        state.set_future_sight(0, 0, 3, 150, 1, 0)

        copied = state.copy()

        assert copied.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 3
        assert copied.get_future_sight_damage(0, 0) == 150

    def test_copy_slot_conditions_independent(self):
        """Test that copied slot conditions are independent."""
        state = BattleState()
        state.set_future_sight(0, 0, 3, 150, 1, 0)

        copied = state.copy()

        # Modify original
        state.set_slot_condition(0, 0, SLOT_FUTURE_SIGHT, 1)

        # Copy should be unchanged
        assert copied.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 3

    def test_copy_includes_pseudo_weather(self):
        """Test that copy includes pseudo-weather."""
        state = BattleState()
        state.set_pseudo_weather(PW_GRAVITY, 5)

        copied = state.copy()

        assert copied.get_pseudo_weather(PW_GRAVITY) == 5

    def test_copy_pseudo_weather_independent(self):
        """Test that copied pseudo-weather is independent."""
        state = BattleState()
        state.set_pseudo_weather(PW_TRICK_ROOM, 5)

        copied = state.copy()

        # Modify original
        state.set_pseudo_weather(PW_TRICK_ROOM, 0)

        # Copy should be unchanged
        assert copied.get_pseudo_weather(PW_TRICK_ROOM) == 5

    def test_copy_includes_last_move(self):
        """Test that copy includes last_move."""
        state = BattleState()
        state.last_move = 42

        copied = state.copy()

        assert copied.last_move == 42

    def test_copy_includes_last_damage(self):
        """Test that copy includes last_damage."""
        state = BattleState()
        state.last_damage = 150

        copied = state.copy()

        assert copied.last_damage == 150

    def test_copy_includes_request_state(self):
        """Test that copy includes request_state."""
        state = BattleState()
        state.request_state = 'switch'

        copied = state.copy()

        assert copied.request_state == 'switch'

    def test_copy_state_variables_independent(self):
        """Test that copied state variables are independent."""
        state = BattleState()
        state.last_move = 10
        state.last_damage = 50
        state.request_state = 'move'

        copied = state.copy()

        # Modify original
        state.last_move = 20
        state.last_damage = 100
        state.request_state = 'switch'

        # Copy should be unchanged
        assert copied.last_move == 10
        assert copied.last_damage == 50
        assert copied.request_state == 'move'


# =============================================================================
# Primal Weather Tests
# =============================================================================

class TestPrimalWeather:
    """Tests for primal weather constants."""

    def test_harsh_sun_constant(self):
        """Test harsh sun constant."""
        assert WEATHER_HARSH_SUN == 6

    def test_heavy_rain_constant(self):
        """Test heavy rain constant."""
        assert WEATHER_HEAVY_RAIN == 7

    def test_strong_winds_constant(self):
        """Test strong winds constant."""
        assert WEATHER_STRONG_WINDS == 8

    def test_primal_weather_names(self):
        """Test primal weather names exist."""
        assert WEATHER_HARSH_SUN in WEATHER_NAMES
        assert WEATHER_HEAVY_RAIN in WEATHER_NAMES
        assert WEATHER_STRONG_WINDS in WEATHER_NAMES

    def test_set_primal_weather(self):
        """Test setting primal weather."""
        state = BattleState()

        state.set_weather(WEATHER_HARSH_SUN, -1)  # Permanent
        assert state.weather == WEATHER_HARSH_SUN
        assert state.weather_turns == -1


# =============================================================================
# Integration Tests with All Features
# =============================================================================

class TestBattleStateIntegration:
    """Integration tests using multiple battle state features."""

    def test_complex_battle_setup(self):
        """Test setting up a complex battle state."""
        state = BattleState(seed=12345)

        # Set up teams
        for side in range(2):
            for slot in range(6):
                state.pokemons[side, slot, P_SPECIES] = side * 6 + slot + 1
                state.pokemons[side, slot, P_LEVEL] = 50
                state.pokemons[side, slot, P_STAT_HP] = 100
                state.pokemons[side, slot, P_CURRENT_HP] = 100

        state.start_battle()

        # Set weather and terrain
        state.set_weather(WEATHER_RAIN, 5)
        state.set_terrain(TERRAIN_ELECTRIC, 5)

        # Set field effects
        state.set_trick_room(5)
        state.set_gravity(5)
        state.set_magic_room(5)

        # Set side conditions
        state.set_side_condition(0, SC_REFLECT, 5)
        state.set_side_condition(0, SC_LIGHT_SCREEN, 5)
        state.set_side_condition(1, SC_SPIKES, 3)
        state.set_side_condition(1, SC_STEALTH_ROCK, 1)

        # Set slot conditions
        state.set_future_sight(1, 0, 3, 150, 0, 0)
        state.set_doom_desire(0, 1, 2, 180, 1, 0)

        # Set state variables
        state.last_move = 100
        state.last_damage = 50
        state.request_state = 'move'

        # Verify everything
        assert state.weather == WEATHER_RAIN
        assert state.terrain == TERRAIN_ELECTRIC
        assert state.trick_room == True
        assert state.gravity == True
        assert state.has_magic_room() == True
        assert state.has_reflect(0) == True
        assert state.has_light_screen(0) == True
        assert state.get_spikes_layers(1) == 3
        assert state.has_stealth_rock(1) == True
        assert state.has_future_sight(1, 0) == True
        assert state.has_doom_desire(0, 1) == True

    def test_advance_multiple_turns(self):
        """Test advancing through multiple turns."""
        state = BattleState()

        # Set up conditions with different durations
        state.set_weather(WEATHER_SUN, 3)
        state.set_terrain(TERRAIN_GRASSY, 4)
        state.set_trick_room(2)
        state.set_side_condition(0, SC_REFLECT, 3)
        state.set_future_sight(0, 0, 3, 100, 1, 0)

        # Advance 2 turns
        state.advance_turn()
        state.advance_turn()

        # Check remaining durations
        assert state.weather_turns == 1
        assert state.terrain_turns == 2
        assert state.trick_room_turns == 0  # Ended
        assert state.get_side_condition(0, SC_REFLECT) == 1
        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 1

        # Advance one more turn
        state.advance_turn()

        # Weather should end
        assert state.weather == WEATHER_NONE
        assert state.terrain == TERRAIN_GRASSY
        assert state.get_side_condition(0, SC_REFLECT) == 0
        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 0

    def test_copy_and_diverge(self):
        """Test copying a state and diverging."""
        state = BattleState(seed=42)

        # Set up state
        state.set_weather(WEATHER_SUN, 5)
        state.set_future_sight(0, 0, 2, 100, 1, 0)
        state.last_move = 50

        # Copy
        branch = state.copy()

        # Diverge: advance original
        state.advance_turn()
        state.set_weather(WEATHER_RAIN, 3)
        state.last_move = 100

        # Branch should be unaffected
        assert branch.weather == WEATHER_SUN
        assert branch.weather_turns == 5
        assert branch.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 2
        assert branch.last_move == 50

        # Original should be changed
        assert state.weather == WEATHER_RAIN
        assert state.weather_turns == 3
        assert state.get_slot_condition(0, 0, SLOT_FUTURE_SIGHT) == 1
        assert state.last_move == 100


# =============================================================================
# Turn Execution State Tests
# =============================================================================

class TestBattleStateTurnExecution:
    """Tests for turn execution state tracking."""

    def test_mid_turn_initialized(self):
        """Test mid_turn is initialized to False."""
        state = BattleState()
        assert state.mid_turn == False

    def test_mid_turn_assignment(self):
        """Test mid_turn can be assigned."""
        state = BattleState()
        state.mid_turn = True
        assert state.mid_turn == True

    def test_active_move_initialized(self):
        """Test active_move is initialized to 0."""
        state = BattleState()
        assert state.active_move == 0

    def test_active_move_assignment(self):
        """Test active_move can be assigned."""
        state = BattleState()
        state.active_move = 100
        assert state.active_move == 100

    def test_active_pokemon_initialized(self):
        """Test active_pokemon is initialized to (-1, -1)."""
        state = BattleState()
        assert state.active_pokemon == (-1, -1)

    def test_active_pokemon_assignment(self):
        """Test active_pokemon can be assigned."""
        state = BattleState()
        state.active_pokemon = (0, 2)
        assert state.active_pokemon == (0, 2)

    def test_active_target_initialized(self):
        """Test active_target is initialized to (-1, -1)."""
        state = BattleState()
        assert state.active_target == (-1, -1)

    def test_active_target_assignment(self):
        """Test active_target can be assigned."""
        state = BattleState()
        state.active_target = (1, 0)
        assert state.active_target == (1, 0)

    def test_last_successful_move_this_turn_initialized(self):
        """Test last_successful_move_this_turn is initialized to 0."""
        state = BattleState()
        assert state.last_successful_move_this_turn == 0

    def test_last_successful_move_this_turn_assignment(self):
        """Test last_successful_move_this_turn can be assigned."""
        state = BattleState()
        state.last_successful_move_this_turn = 50
        assert state.last_successful_move_this_turn == 50

    def test_quick_claw_roll_initialized(self):
        """Test quick_claw_roll is initialized to False."""
        state = BattleState()
        assert state.quick_claw_roll == False

    def test_quick_claw_roll_assignment(self):
        """Test quick_claw_roll can be assigned."""
        state = BattleState()
        state.quick_claw_roll = True
        assert state.quick_claw_roll == True

    def test_clear_turn_state(self):
        """Test clearing turn state."""
        state = BattleState()
        state.mid_turn = True
        state.active_move = 100
        state.active_pokemon = (0, 1)
        state.active_target = (1, 0)
        state.last_successful_move_this_turn = 50
        state.quick_claw_roll = True

        state.clear_turn_state()

        assert state.mid_turn == False
        assert state.active_move == 0
        assert state.active_pokemon == (-1, -1)
        assert state.active_target == (-1, -1)
        assert state.last_successful_move_this_turn == 0
        assert state.quick_claw_roll == False


# =============================================================================
# Faint Queue Tests
# =============================================================================

class TestBattleStateFaintQueue:
    """Tests for faint queue functionality."""

    def test_faint_queue_initialized_empty(self):
        """Test faint queue is initialized empty."""
        state = BattleState()
        assert state.faint_queue == []

    def test_queue_faint(self):
        """Test queueing a faint."""
        state = BattleState()
        state.queue_faint(0, 1)
        state.queue_faint(1, 0)

        assert len(state.faint_queue) == 2
        assert (0, 1) in state.faint_queue
        assert (1, 0) in state.faint_queue

    def test_process_faint_queue(self):
        """Test processing the faint queue."""
        state = BattleState()
        state.queue_faint(0, 0)
        state.queue_faint(1, 2)

        fainted = state.process_faint_queue()

        assert fainted == [(0, 0), (1, 2)]
        assert state.faint_queue == []

    def test_process_empty_faint_queue(self):
        """Test processing empty faint queue."""
        state = BattleState()

        fainted = state.process_faint_queue()

        assert fainted == []


# =============================================================================
# Copy Extended Tests (Turn Execution)
# =============================================================================

class TestBattleStateCopyTurnExecution:
    """Tests for copy() with turn execution state."""

    def test_copy_includes_mid_turn(self):
        """Test that copy includes mid_turn."""
        state = BattleState()
        state.mid_turn = True

        copied = state.copy()

        assert copied.mid_turn == True

    def test_copy_includes_active_move(self):
        """Test that copy includes active_move."""
        state = BattleState()
        state.active_move = 150

        copied = state.copy()

        assert copied.active_move == 150

    def test_copy_includes_active_pokemon(self):
        """Test that copy includes active_pokemon."""
        state = BattleState()
        state.active_pokemon = (0, 2)

        copied = state.copy()

        assert copied.active_pokemon == (0, 2)

    def test_copy_includes_active_target(self):
        """Test that copy includes active_target."""
        state = BattleState()
        state.active_target = (1, 1)

        copied = state.copy()

        assert copied.active_target == (1, 1)

    def test_copy_includes_last_successful_move(self):
        """Test that copy includes last_successful_move_this_turn."""
        state = BattleState()
        state.last_successful_move_this_turn = 75

        copied = state.copy()

        assert copied.last_successful_move_this_turn == 75

    def test_copy_includes_quick_claw_roll(self):
        """Test that copy includes quick_claw_roll."""
        state = BattleState()
        state.quick_claw_roll = True

        copied = state.copy()

        assert copied.quick_claw_roll == True

    def test_copy_includes_faint_queue(self):
        """Test that copy includes faint_queue."""
        state = BattleState()
        state.queue_faint(0, 1)
        state.queue_faint(1, 0)

        copied = state.copy()

        assert copied.faint_queue == [(0, 1), (1, 0)]

    def test_copy_faint_queue_independent(self):
        """Test that copied faint_queue is independent."""
        state = BattleState()
        state.queue_faint(0, 0)

        copied = state.copy()

        # Modify original
        state.queue_faint(1, 1)

        # Copy should be unchanged
        assert copied.faint_queue == [(0, 0)]
        assert state.faint_queue == [(0, 0), (1, 1)]


# =============================================================================
# Generation and Game Type Tests
# =============================================================================

class TestBattleStateGenAndGameType:
    """Tests for generation and game type tracking."""

    def test_gen_default(self):
        """Test default gen is 9."""
        state = BattleState()
        assert state.gen == 9

    def test_gen_custom(self):
        """Test custom gen values."""
        state = BattleState(gen=8)
        assert state.gen == 8

        state = BattleState(gen=1)
        assert state.gen == 1

    def test_game_type_default(self):
        """Test default game_type is doubles."""
        state = BattleState()
        assert state.game_type == 'doubles'

    def test_game_type_singles(self):
        """Test singles game type."""
        state = BattleState(game_type='singles', active_slots=1)
        assert state.game_type == 'singles'

    def test_game_type_triples(self):
        """Test triples game type."""
        state = BattleState(game_type='triples', active_slots=3)
        assert state.game_type == 'triples'

    def test_copy_preserves_gen(self):
        """Test copy preserves gen."""
        state = BattleState(gen=7)
        copied = state.copy()
        assert copied.gen == 7

    def test_copy_preserves_game_type(self):
        """Test copy preserves game_type."""
        state = BattleState(game_type='singles')
        copied = state.copy()
        assert copied.game_type == 'singles'


# =============================================================================
# Started State Tests
# =============================================================================

class TestBattleStateStarted:
    """Tests for started state tracking."""

    def test_started_default_false(self):
        """Test started is False by default."""
        state = BattleState()
        assert state.started == False

    def test_start_battle_sets_started(self):
        """Test start_battle sets started to True."""
        state = BattleState()
        state.start_battle()
        assert state.started == True

    def test_copy_preserves_started(self):
        """Test copy preserves started state."""
        state = BattleState()
        state.start_battle()
        copied = state.copy()
        assert copied.started == True

    def test_started_false_not_started(self):
        """Test started remains False if not started."""
        state = BattleState()
        copied = state.copy()
        assert copied.started == False


# =============================================================================
# Effect Order Tests
# =============================================================================

class TestBattleStateEffectOrder:
    """Tests for effect ordering."""

    def test_effect_order_initialized_zero(self):
        """Test effect_order is initialized to 0."""
        state = BattleState()
        assert state.effect_order == 0

    def test_effect_order_assignment(self):
        """Test effect_order can be assigned."""
        state = BattleState()
        state.effect_order = 5
        assert state.effect_order == 5

    def test_effect_order_increment(self):
        """Test effect_order can be incremented."""
        state = BattleState()
        state.effect_order += 1
        assert state.effect_order == 1
        state.effect_order += 1
        assert state.effect_order == 2

    def test_copy_preserves_effect_order(self):
        """Test copy preserves effect_order."""
        state = BattleState()
        state.effect_order = 10
        copied = state.copy()
        assert copied.effect_order == 10


# =============================================================================
# Speed Order Tests
# =============================================================================

class TestBattleStateSpeedOrder:
    """Tests for speed ordering."""

    def test_speed_order_initialized(self):
        """Test speed_order is initialized based on active slots."""
        state = BattleState(num_sides=2, active_slots=2)
        # Should be [0, 1, 2, 3] for 4 active Pokemon positions
        assert state.speed_order == [0, 1, 2, 3]

    def test_speed_order_singles(self):
        """Test speed_order for singles."""
        state = BattleState(num_sides=2, active_slots=1)
        assert state.speed_order == [0, 1]

    def test_speed_order_assignment(self):
        """Test speed_order can be assigned."""
        state = BattleState()
        state.speed_order = [3, 1, 2, 0]
        assert state.speed_order == [3, 1, 2, 0]

    def test_copy_preserves_speed_order(self):
        """Test copy preserves speed_order."""
        state = BattleState()
        state.speed_order = [2, 0, 3, 1]
        copied = state.copy()
        assert copied.speed_order == [2, 0, 3, 1]

    def test_copy_speed_order_independent(self):
        """Test copied speed_order is independent."""
        state = BattleState()
        state.speed_order = [0, 1, 2, 3]
        copied = state.copy()

        # Modify original
        state.speed_order[0] = 3

        # Copy should be unchanged
        assert copied.speed_order == [0, 1, 2, 3]
        assert state.speed_order == [3, 1, 2, 3]


# =============================================================================
# Full Battle Cycle Tests
# =============================================================================

class TestBattleStateCycle:
    """Tests for complete battle lifecycle."""

    def test_full_battle_lifecycle(self):
        """Test a full battle lifecycle."""
        state = BattleState(gen=9, game_type='doubles', seed=42)

        # Initial state
        assert state.started == False
        assert state.ended == False
        assert state.turn == 0

        # Start battle
        state.start_battle()
        assert state.started == True
        assert state.turn == 1

        # Advance several turns
        state.advance_turn()
        assert state.turn == 2
        state.advance_turn()
        assert state.turn == 3

        # End battle
        state.ended = True
        state.winner = 0
        assert state.ended == True

    def test_battle_with_all_conditions(self):
        """Test battle with various conditions active."""
        state = BattleState(gen=9, game_type='doubles', seed=12345)

        # Set up teams
        for side in range(2):
            for slot in range(6):
                state.pokemons[side, slot, P_SPECIES] = side * 6 + slot + 1
                state.pokemons[side, slot, P_LEVEL] = 50
                state.pokemons[side, slot, P_STAT_HP] = 100
                state.pokemons[side, slot, P_CURRENT_HP] = 100

        state.start_battle()

        # Set various conditions
        state.set_weather(WEATHER_RAIN, 5)
        state.set_terrain(TERRAIN_ELECTRIC, 5)
        state.set_trick_room(5)
        state.set_side_condition(0, SC_REFLECT, 5)
        state.set_future_sight(0, 0, 3, 150, 1, 0)

        # Track state
        state.effect_order = 5
        state.speed_order = [3, 2, 1, 0]

        # Copy and verify
        copied = state.copy()
        assert copied.gen == 9
        assert copied.game_type == 'doubles'
        assert copied.started == True
        assert copied.effect_order == 5
        assert copied.speed_order == [3, 2, 1, 0]
        assert copied.weather == WEATHER_RAIN
        assert copied.terrain == TERRAIN_ELECTRIC
