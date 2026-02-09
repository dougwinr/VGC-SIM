"""Battle state representation using flat NumPy arrays.

This module provides the BattleState class which stores all battle data
in dense NumPy arrays for cache efficiency and fast simulation.

The state is designed for:
- Deterministic simulation (via seeded PRNG)
- Efficient vectorized operations
- Easy serialization/deserialization for RL environments
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
import numpy as np

from .layout import (
    POKEMON_ARRAY_SIZE,
    P_CURRENT_HP, P_STATUS, P_STATUS_COUNTER,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
    P_STAGE_ACC, P_STAGE_EVA,
    P_MOVE1, P_PP1,
    STATUS_NONE,
)
from .pokemon import Pokemon


# =============================================================================
# Side Condition Indices
# =============================================================================

# Side conditions array layout
SC_REFLECT = 0          # Reflect turns remaining
SC_LIGHT_SCREEN = 1     # Light Screen turns remaining
SC_AURORA_VEIL = 2      # Aurora Veil turns remaining
SC_SAFEGUARD = 3        # Safeguard turns remaining
SC_MIST = 4             # Mist turns remaining
SC_TAILWIND = 5         # Tailwind turns remaining
SC_LUCKY_CHANT = 6      # Lucky Chant turns remaining
SC_SPIKES = 7           # Spikes layers (0-3)
SC_TOXIC_SPIKES = 8     # Toxic Spikes layers (0-2)
SC_STEALTH_ROCK = 9     # Stealth Rock active (0/1)
SC_STICKY_WEB = 10      # Sticky Web active (0/1)
SC_WIDE_GUARD = 11      # Wide Guard active this turn
SC_QUICK_GUARD = 12     # Quick Guard active this turn
SC_MAT_BLOCK = 13       # Mat Block active this turn
SC_CRAFTY_SHIELD = 14   # Crafty Shield active this turn
SC_WISH = 15            # Wish turns remaining
SC_WISH_AMOUNT = 16     # Wish heal amount
SC_HEALING_WISH = 17    # Healing Wish pending for this side
SC_LUNAR_DANCE = 18     # Lunar Dance pending for this side

SIDE_CONDITION_SIZE = 19


# =============================================================================
# Slot Condition Indices (per-position conditions)
# =============================================================================

# Slot conditions array layout (per active slot)
SLOT_FUTURE_SIGHT = 0      # Future Sight turns remaining
SLOT_FUTURE_SIGHT_DMG = 1  # Future Sight damage amount
SLOT_FUTURE_SIGHT_USER = 2 # Future Sight user (encoded side*team_size + slot)
SLOT_DOOM_DESIRE = 3       # Doom Desire turns remaining
SLOT_DOOM_DESIRE_DMG = 4   # Doom Desire damage amount
SLOT_DOOM_DESIRE_USER = 5  # Doom Desire user
SLOT_HEALING_WISH = 6      # Healing Wish pending for slot
SLOT_LUNAR_DANCE = 7       # Lunar Dance pending for slot

SLOT_CONDITION_SIZE = 8


# =============================================================================
# Pseudo-Weather Indices (field conditions that aren't weather)
# =============================================================================

PW_TRICK_ROOM = 0       # Trick Room turns remaining
PW_GRAVITY = 1          # Gravity turns remaining
PW_MAGIC_ROOM = 2       # Magic Room turns remaining
PW_WONDER_ROOM = 3      # Wonder Room turns remaining
PW_FAIRY_LOCK = 4       # Fairy Lock turns remaining
PW_MUD_SPORT = 5        # Mud Sport active
PW_WATER_SPORT = 6      # Water Sport active
PW_ION_DELUGE = 7       # Ion Deluge active this turn

PSEUDO_WEATHER_SIZE = 8


# =============================================================================
# Field Condition Indices
# =============================================================================

# Field state array layout
FIELD_WEATHER = 0       # Weather ID (0=none, 1=sun, 2=rain, 3=sand, 4=hail, 5=snow)
FIELD_WEATHER_TURNS = 1 # Weather turns remaining (-1 = permanent)
FIELD_TERRAIN = 2       # Terrain ID (0=none, 1=electric, 2=grassy, 3=misty, 4=psychic)
FIELD_TERRAIN_TURNS = 3 # Terrain turns remaining
FIELD_TRICK_ROOM = 4    # Trick Room turns remaining
FIELD_GRAVITY = 5       # Gravity turns remaining
FIELD_MAGIC_ROOM = 6    # Magic Room turns remaining
FIELD_WONDER_ROOM = 7   # Wonder Room turns remaining
FIELD_MUD_SPORT = 8     # Mud Sport active
FIELD_WATER_SPORT = 9   # Water Sport active
FIELD_ION_DELUGE = 10   # Ion Deluge active this turn
FIELD_FAIRY_LOCK = 11   # Fairy Lock turns remaining

FIELD_STATE_SIZE = 12


# =============================================================================
# Weather Constants
# =============================================================================

WEATHER_NONE = 0
WEATHER_SUN = 1
WEATHER_RAIN = 2
WEATHER_SAND = 3
WEATHER_HAIL = 4
WEATHER_SNOW = 5
WEATHER_HARSH_SUN = 6
WEATHER_HEAVY_RAIN = 7
WEATHER_STRONG_WINDS = 8

WEATHER_NAMES = {
    WEATHER_NONE: "none",
    WEATHER_SUN: "sun",
    WEATHER_RAIN: "rain",
    WEATHER_SAND: "sand",
    WEATHER_HAIL: "hail",
    WEATHER_SNOW: "snow",
    WEATHER_HARSH_SUN: "harshsun",
    WEATHER_HEAVY_RAIN: "heavyrain",
    WEATHER_STRONG_WINDS: "strongwinds",
}


# =============================================================================
# Terrain Constants
# =============================================================================

TERRAIN_NONE = 0
TERRAIN_ELECTRIC = 1
TERRAIN_GRASSY = 2
TERRAIN_MISTY = 3
TERRAIN_PSYCHIC = 4

TERRAIN_NAMES = {
    TERRAIN_NONE: "none",
    TERRAIN_ELECTRIC: "electric",
    TERRAIN_GRASSY: "grassy",
    TERRAIN_MISTY: "misty",
    TERRAIN_PSYCHIC: "psychic",
}


# =============================================================================
# PRNG Implementation
# =============================================================================

class BattlePRNG:
    """Deterministic pseudo-random number generator for battles.

    Uses the same PRNG algorithm as Pokemon Showdown for replay compatibility.
    Based on a linear congruential generator with 32-bit state.
    """

    __slots__ = ('_seed', '_state')

    # LCG constants (same as Pokemon Showdown)
    MULTIPLIER = 0x41C64E6D
    INCREMENT = 0x6073
    MODULUS = 0x100000000  # 2^32

    def __init__(self, seed: Optional[Union[int, Tuple[int, int, int, int]]] = None):
        """Initialize the PRNG with a seed.

        Args:
            seed: Integer seed or tuple of 4 16-bit values, or None for random
        """
        if seed is None:
            import time
            seed = int(time.time() * 1000) & 0xFFFFFFFF

        if isinstance(seed, tuple):
            # Convert 4 16-bit values to 32-bit state
            self._seed = seed
            self._state = (seed[0] << 16) | seed[1]
        else:
            self._seed = seed
            self._state = seed & 0xFFFFFFFF

    def _next(self) -> int:
        """Advance the PRNG and return the next 32-bit value."""
        self._state = (self._state * self.MULTIPLIER + self.INCREMENT) % self.MODULUS
        return self._state

    def next(self, max_value: int = 0x10000) -> int:
        """Get the next random value in range [0, max_value).

        Args:
            max_value: Upper bound (exclusive), default 65536

        Returns:
            Random integer in [0, max_value)
        """
        return (self._next() >> 16) % max_value

    def random_chance(self, numerator: int, denominator: int) -> bool:
        """Return True with probability numerator/denominator.

        Args:
            numerator: Numerator of probability
            denominator: Denominator of probability

        Returns:
            True with probability numerator/denominator
        """
        return self.next(denominator) < numerator

    def random(self, min_val: int, max_val: int) -> int:
        """Get a random integer in range [min_val, max_val].

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Returns:
            Random integer in [min_val, max_val]
        """
        return min_val + self.next(max_val - min_val + 1)

    def sample(self, population: list, k: int = 1) -> list:
        """Random sample without replacement.

        Args:
            population: List to sample from
            k: Number of items to sample

        Returns:
            List of k randomly selected items
        """
        if k > len(population):
            k = len(population)

        pool = list(population)
        result = []
        for _ in range(k):
            idx = self.next(len(pool))
            result.append(pool[idx])
            pool[idx] = pool[-1]
            pool.pop()
        return result

    def shuffle(self, items: list) -> None:
        """Shuffle a list in place using Fisher-Yates.

        Args:
            items: List to shuffle in place
        """
        for i in range(len(items) - 1, 0, -1):
            j = self.next(i + 1)
            items[i], items[j] = items[j], items[i]

    def get_seed(self) -> int:
        """Get the current PRNG state."""
        return self._state

    def get_initial_seed(self) -> Union[int, Tuple[int, int, int, int]]:
        """Get the initial seed used to create this PRNG."""
        return self._seed

    def clone(self) -> 'BattlePRNG':
        """Create a copy of this PRNG with the same state."""
        prng = BattlePRNG(0)
        prng._state = self._state
        prng._seed = self._seed
        return prng


# =============================================================================
# Battle State
# =============================================================================

class BattleState:
    """Complete battle state stored in flat NumPy arrays.

    This class represents the entire state of a Pokemon battle in a format
    optimized for:
    - Fast simulation (dense array access)
    - Deterministic replay (seeded PRNG)
    - RL environments (easy observation extraction)

    Attributes:
        num_sides: Number of sides in battle (typically 2)
        team_size: Maximum team size per side (typically 6)
        active_slots: Number of active Pokemon per side (1 for singles, 2 for doubles)
        pokemons: All Pokemon data [num_sides, team_size, POKEMON_ARRAY_SIZE]
        active: Indices of active Pokemon [num_sides, active_slots]
        side_conditions: Side conditions [num_sides, SIDE_CONDITION_SIZE]
        field: Field state [FIELD_STATE_SIZE]
        prng: Battle PRNG for deterministic randomness
        turn: Current turn number
        ended: Whether battle has ended
        winner: Index of winning side (-1 if not ended or draw)
    """

    __slots__ = (
        'num_sides', 'team_size', 'active_slots', 'gen', 'game_type',
        'pokemons', 'active', 'side_conditions', 'slot_conditions', 'field',
        'pseudo_weather', 'prng', 'turn', 'started', 'ended', 'winner',
        'last_move', 'last_damage', 'request_state',
        'mid_turn', 'active_move', 'active_pokemon', 'active_target',
        'last_successful_move_this_turn', 'quick_claw_roll',
        'effect_order', 'speed_order',
        '_action_log', '_message_log', '_faint_queue',
    )

    def __init__(
        self,
        num_sides: int = 2,
        team_size: int = 6,
        active_slots: int = 2,
        seed: Optional[Union[int, Tuple[int, int, int, int]]] = None,
        gen: int = 9,
        game_type: str = 'doubles',
    ):
        """Initialize a new battle state.

        Args:
            num_sides: Number of sides (2 for standard battle)
            team_size: Team size per side (6 for standard)
            active_slots: Active Pokemon per side (1=singles, 2=doubles)
            seed: PRNG seed for deterministic battles
            gen: Generation (affects damage formulas, 1-9)
            game_type: Game type ('singles', 'doubles', 'triples')
        """
        self.num_sides = num_sides
        self.team_size = team_size
        self.active_slots = active_slots
        self.gen = gen
        self.game_type = game_type

        # Initialize Pokemon arrays
        self.pokemons = np.zeros(
            (num_sides, team_size, POKEMON_ARRAY_SIZE),
            dtype=np.int32
        )

        # Initialize active indices (-1 = empty slot)
        self.active = np.full(
            (num_sides, active_slots),
            -1,
            dtype=np.int32
        )

        # Initialize side conditions
        self.side_conditions = np.zeros(
            (num_sides, SIDE_CONDITION_SIZE),
            dtype=np.int32
        )

        # Initialize slot conditions (per-position effects like Future Sight)
        self.slot_conditions = np.zeros(
            (num_sides, active_slots, SLOT_CONDITION_SIZE),
            dtype=np.int32
        )

        # Initialize field state
        self.field = np.zeros(FIELD_STATE_SIZE, dtype=np.int32)

        # Initialize pseudo-weather (Trick Room, Gravity, etc.)
        self.pseudo_weather = np.zeros(PSEUDO_WEATHER_SIZE, dtype=np.int32)

        # Initialize PRNG
        self.prng = BattlePRNG(seed)

        # Battle state
        self.turn = 0
        self.started = False    # Whether the battle has started
        self.ended = False
        self.winner = -1
        self.last_move = 0      # ID of last move used
        self.last_damage = 0    # Last damage dealt (for Counter/Mirror Coat)
        self.request_state = '' # Current request state ('', 'move', 'switch', 'teampreview')

        # Turn execution state
        self.mid_turn = False               # Whether we're in the middle of turn execution
        self.active_move = 0                # ID of currently executing move
        self.active_pokemon: Tuple[int, int] = (-1, -1)  # (side, slot) of Pokemon using move
        self.active_target: Tuple[int, int] = (-1, -1)   # (side, slot) of target Pokemon
        self.last_successful_move_this_turn = 0  # ID of last successful move this turn
        self.quick_claw_roll = False        # Whether Quick Claw activated this turn
        self.effect_order = 0               # Counter for effect ordering
        self.speed_order: List[int] = list(range(num_sides * active_slots))  # Speed-sorted order

        # Faint queue - list of (side, slot) tuples for Pokemon that fainted
        self._faint_queue: List[Tuple[int, int]] = []

        # Logs for replay
        self._action_log: List[str] = []
        self._message_log: List[str] = []

    # -------------------------------------------------------------------------
    # Pokemon Access
    # -------------------------------------------------------------------------

    def get_pokemon(self, side: int, slot: int) -> Pokemon:
        """Get a Pokemon wrapper for the given side and slot.

        Args:
            side: Side index (0 or 1)
            slot: Team slot index (0-5)

        Returns:
            Pokemon wrapper for the data at that position
        """
        return Pokemon(self.pokemons[side, slot])

    def set_pokemon(self, side: int, slot: int, pokemon: Pokemon) -> None:
        """Set Pokemon data at the given position.

        Args:
            side: Side index
            slot: Team slot index
            pokemon: Pokemon to copy data from
        """
        self.pokemons[side, slot] = pokemon.data.copy()

    def get_active_pokemon(self, side: int, active_slot: int) -> Optional[Pokemon]:
        """Get the active Pokemon in the given active slot.

        Args:
            side: Side index
            active_slot: Active slot index (0 for singles, 0-1 for doubles)

        Returns:
            Pokemon if slot is occupied, None otherwise
        """
        team_slot = self.active[side, active_slot]
        if team_slot < 0:
            return None
        return self.get_pokemon(side, team_slot)

    def get_team(self, side: int) -> List[Pokemon]:
        """Get all Pokemon on a side as a list.

        Args:
            side: Side index

        Returns:
            List of Pokemon on that side
        """
        return [self.get_pokemon(side, i) for i in range(self.team_size)]

    def get_active_indices(self, side: int) -> List[int]:
        """Get indices of active Pokemon for a side.

        Args:
            side: Side index

        Returns:
            List of team slot indices for active Pokemon
        """
        return [int(i) for i in self.active[side] if i >= 0]

    def is_pokemon_active(self, side: int, slot: int) -> bool:
        """Check if a Pokemon is currently active.

        Args:
            side: Side index
            slot: Team slot index

        Returns:
            True if the Pokemon is in an active slot
        """
        return slot in self.active[side]

    # -------------------------------------------------------------------------
    # Side Condition Access
    # -------------------------------------------------------------------------

    def get_side_condition(self, side: int, condition: int) -> int:
        """Get the value of a side condition.

        Args:
            side: Side index
            condition: Side condition index (SC_*)

        Returns:
            Condition value (turns remaining or layer count)
        """
        return int(self.side_conditions[side, condition])

    def set_side_condition(self, side: int, condition: int, value: int) -> None:
        """Set a side condition value.

        Args:
            side: Side index
            condition: Side condition index
            value: Value to set
        """
        self.side_conditions[side, condition] = value

    def has_reflect(self, side: int) -> bool:
        """Check if Reflect is active on a side."""
        return self.side_conditions[side, SC_REFLECT] > 0

    def has_light_screen(self, side: int) -> bool:
        """Check if Light Screen is active on a side."""
        return self.side_conditions[side, SC_LIGHT_SCREEN] > 0

    def has_aurora_veil(self, side: int) -> bool:
        """Check if Aurora Veil is active on a side."""
        return self.side_conditions[side, SC_AURORA_VEIL] > 0

    def get_spikes_layers(self, side: int) -> int:
        """Get number of Spikes layers on a side."""
        return int(self.side_conditions[side, SC_SPIKES])

    def has_stealth_rock(self, side: int) -> bool:
        """Check if Stealth Rock is on a side."""
        return self.side_conditions[side, SC_STEALTH_ROCK] > 0

    def has_toxic_spikes(self, side: int) -> bool:
        """Check if Toxic Spikes are on a side."""
        return self.side_conditions[side, SC_TOXIC_SPIKES] > 0

    def get_toxic_spikes_layers(self, side: int) -> int:
        """Get number of Toxic Spikes layers."""
        return int(self.side_conditions[side, SC_TOXIC_SPIKES])

    def has_sticky_web(self, side: int) -> bool:
        """Check if Sticky Web is on a side."""
        return self.side_conditions[side, SC_STICKY_WEB] > 0

    def has_tailwind(self, side: int) -> bool:
        """Check if Tailwind is active on a side."""
        return self.side_conditions[side, SC_TAILWIND] > 0

    def has_safeguard(self, side: int) -> bool:
        """Check if Safeguard is active on a side."""
        return self.side_conditions[side, SC_SAFEGUARD] > 0

    # -------------------------------------------------------------------------
    # Slot Condition Access (per-position effects)
    # -------------------------------------------------------------------------

    def get_slot_condition(self, side: int, slot: int, condition: int) -> int:
        """Get a slot condition value.

        Args:
            side: Side index
            slot: Active slot index
            condition: Slot condition index (SLOT_*)

        Returns:
            Condition value
        """
        return int(self.slot_conditions[side, slot, condition])

    def set_slot_condition(self, side: int, slot: int, condition: int, value: int) -> None:
        """Set a slot condition value.

        Args:
            side: Side index
            slot: Active slot index
            condition: Slot condition index
            value: Value to set
        """
        self.slot_conditions[side, slot, condition] = value

    def has_future_sight(self, side: int, slot: int) -> bool:
        """Check if Future Sight is targeting this slot."""
        return self.slot_conditions[side, slot, SLOT_FUTURE_SIGHT] > 0

    def set_future_sight(
        self,
        target_side: int,
        target_slot: int,
        turns: int,
        damage: int,
        user_side: int,
        user_slot: int,
    ) -> None:
        """Set up Future Sight targeting a slot.

        Args:
            target_side: Side being targeted
            target_slot: Slot being targeted
            turns: Turns until it hits
            damage: Damage amount
            user_side: Side of the user
            user_slot: Team slot of the user
        """
        self.slot_conditions[target_side, target_slot, SLOT_FUTURE_SIGHT] = turns
        self.slot_conditions[target_side, target_slot, SLOT_FUTURE_SIGHT_DMG] = damage
        # Encode user as side * team_size + slot
        self.slot_conditions[target_side, target_slot, SLOT_FUTURE_SIGHT_USER] = (
            user_side * self.team_size + user_slot
        )

    def clear_slot_conditions(self, side: int, slot: int) -> None:
        """Clear all slot conditions for a slot.

        Args:
            side: Side index
            slot: Active slot index
        """
        self.slot_conditions[side, slot, :] = 0

    def has_doom_desire(self, side: int, slot: int) -> bool:
        """Check if Doom Desire is targeting this slot."""
        return self.slot_conditions[side, slot, SLOT_DOOM_DESIRE] > 0

    def set_doom_desire(
        self,
        target_side: int,
        target_slot: int,
        turns: int,
        damage: int,
        user_side: int,
        user_slot: int,
    ) -> None:
        """Set up Doom Desire targeting a slot.

        Args:
            target_side: Side being targeted
            target_slot: Slot being targeted
            turns: Turns until it hits
            damage: Damage amount
            user_side: Side of the user
            user_slot: Team slot of the user
        """
        self.slot_conditions[target_side, target_slot, SLOT_DOOM_DESIRE] = turns
        self.slot_conditions[target_side, target_slot, SLOT_DOOM_DESIRE_DMG] = damage
        self.slot_conditions[target_side, target_slot, SLOT_DOOM_DESIRE_USER] = (
            user_side * self.team_size + user_slot
        )

    def get_future_sight_damage(self, side: int, slot: int) -> int:
        """Get Future Sight damage for a slot."""
        return int(self.slot_conditions[side, slot, SLOT_FUTURE_SIGHT_DMG])

    def get_doom_desire_damage(self, side: int, slot: int) -> int:
        """Get Doom Desire damage for a slot."""
        return int(self.slot_conditions[side, slot, SLOT_DOOM_DESIRE_DMG])

    # -------------------------------------------------------------------------
    # Pseudo-Weather Access (field effects that aren't weather)
    # -------------------------------------------------------------------------

    def get_pseudo_weather(self, condition: int) -> int:
        """Get a pseudo-weather condition value.

        Args:
            condition: Pseudo-weather index (PW_*)

        Returns:
            Turns remaining or active status
        """
        return int(self.pseudo_weather[condition])

    def set_pseudo_weather(self, condition: int, value: int) -> None:
        """Set a pseudo-weather condition.

        Args:
            condition: Pseudo-weather index
            value: Turns remaining or active status
        """
        self.pseudo_weather[condition] = value

    def has_magic_room(self) -> bool:
        """Check if Magic Room is active."""
        return self.field[FIELD_MAGIC_ROOM] > 0

    def set_magic_room(self, turns: int = 5) -> None:
        """Activate Magic Room."""
        self.field[FIELD_MAGIC_ROOM] = turns

    def has_wonder_room(self) -> bool:
        """Check if Wonder Room is active."""
        return self.field[FIELD_WONDER_ROOM] > 0

    def set_wonder_room(self, turns: int = 5) -> None:
        """Activate Wonder Room."""
        self.field[FIELD_WONDER_ROOM] = turns

    def has_fairy_lock(self) -> bool:
        """Check if Fairy Lock is active."""
        return self.field[FIELD_FAIRY_LOCK] > 0

    def set_fairy_lock(self, turns: int = 2) -> None:
        """Activate Fairy Lock."""
        self.field[FIELD_FAIRY_LOCK] = turns

    def has_mud_sport(self) -> bool:
        """Check if Mud Sport is active."""
        return self.field[FIELD_MUD_SPORT] > 0

    def set_mud_sport(self, active: bool = True) -> None:
        """Set Mud Sport status."""
        self.field[FIELD_MUD_SPORT] = 1 if active else 0

    def has_water_sport(self) -> bool:
        """Check if Water Sport is active."""
        return self.field[FIELD_WATER_SPORT] > 0

    def set_water_sport(self, active: bool = True) -> None:
        """Set Water Sport status."""
        self.field[FIELD_WATER_SPORT] = 1 if active else 0

    def has_ion_deluge(self) -> bool:
        """Check if Ion Deluge is active this turn."""
        return self.field[FIELD_ION_DELUGE] > 0

    def set_ion_deluge(self, active: bool = True) -> None:
        """Set Ion Deluge status for this turn."""
        self.field[FIELD_ION_DELUGE] = 1 if active else 0

    # -------------------------------------------------------------------------
    # Field Condition Access
    # -------------------------------------------------------------------------

    @property
    def weather(self) -> int:
        """Get current weather ID."""
        return int(self.field[FIELD_WEATHER])

    @weather.setter
    def weather(self, value: int) -> None:
        """Set current weather ID."""
        self.field[FIELD_WEATHER] = value

    @property
    def weather_turns(self) -> int:
        """Get weather turns remaining."""
        return int(self.field[FIELD_WEATHER_TURNS])

    @weather_turns.setter
    def weather_turns(self, value: int) -> None:
        """Set weather turns remaining."""
        self.field[FIELD_WEATHER_TURNS] = value

    @property
    def terrain(self) -> int:
        """Get current terrain ID."""
        return int(self.field[FIELD_TERRAIN])

    @terrain.setter
    def terrain(self, value: int) -> None:
        """Set current terrain ID."""
        self.field[FIELD_TERRAIN] = value

    @property
    def terrain_turns(self) -> int:
        """Get terrain turns remaining."""
        return int(self.field[FIELD_TERRAIN_TURNS])

    @terrain_turns.setter
    def terrain_turns(self, value: int) -> None:
        """Set terrain turns remaining."""
        self.field[FIELD_TERRAIN_TURNS] = value

    @property
    def trick_room(self) -> bool:
        """Check if Trick Room is active."""
        return self.field[FIELD_TRICK_ROOM] > 0

    @property
    def trick_room_turns(self) -> int:
        """Get Trick Room turns remaining."""
        return int(self.field[FIELD_TRICK_ROOM])

    @property
    def gravity(self) -> bool:
        """Check if Gravity is active."""
        return self.field[FIELD_GRAVITY] > 0

    @property
    def gravity_turns(self) -> int:
        """Get Gravity turns remaining."""
        return int(self.field[FIELD_GRAVITY])

    def set_weather(self, weather_id: int, turns: int = 5) -> None:
        """Set weather with duration.

        Args:
            weather_id: Weather ID constant
            turns: Duration in turns (-1 for permanent)
        """
        self.field[FIELD_WEATHER] = weather_id
        self.field[FIELD_WEATHER_TURNS] = turns

    def clear_weather(self) -> None:
        """Clear current weather."""
        self.field[FIELD_WEATHER] = WEATHER_NONE
        self.field[FIELD_WEATHER_TURNS] = 0

    def set_terrain(self, terrain_id: int, turns: int = 5) -> None:
        """Set terrain with duration.

        Args:
            terrain_id: Terrain ID constant
            turns: Duration in turns
        """
        self.field[FIELD_TERRAIN] = terrain_id
        self.field[FIELD_TERRAIN_TURNS] = turns

    def clear_terrain(self) -> None:
        """Clear current terrain."""
        self.field[FIELD_TERRAIN] = TERRAIN_NONE
        self.field[FIELD_TERRAIN_TURNS] = 0

    def set_trick_room(self, turns: int = 5) -> None:
        """Activate Trick Room.

        Args:
            turns: Duration in turns
        """
        self.field[FIELD_TRICK_ROOM] = turns

    def set_gravity(self, turns: int = 5) -> None:
        """Activate Gravity.

        Args:
            turns: Duration in turns
        """
        self.field[FIELD_GRAVITY] = turns

    # -------------------------------------------------------------------------
    # Battle Flow
    # -------------------------------------------------------------------------

    def start_battle(self) -> None:
        """Initialize battle start state.

        Sets turn to 1 and sends out initial Pokemon.
        """
        self.turn = 1
        self.started = True
        self.ended = False
        self.winner = -1

        # Send out first Pokemon for each side
        for side in range(self.num_sides):
            for slot in range(self.active_slots):
                if slot < self.team_size:
                    pokemon = self.get_pokemon(side, slot)
                    if pokemon.max_hp > 0:  # Valid Pokemon
                        self.active[side, slot] = slot

    def advance_turn(self) -> None:
        """Advance to the next turn.

        Decrements turn counters for field conditions, side conditions, and slot conditions.
        """
        self.turn += 1

        # Decrement weather turns
        if self.field[FIELD_WEATHER_TURNS] > 0:
            self.field[FIELD_WEATHER_TURNS] -= 1
            if self.field[FIELD_WEATHER_TURNS] == 0:
                self.field[FIELD_WEATHER] = WEATHER_NONE

        # Decrement terrain turns
        if self.field[FIELD_TERRAIN_TURNS] > 0:
            self.field[FIELD_TERRAIN_TURNS] -= 1
            if self.field[FIELD_TERRAIN_TURNS] == 0:
                self.field[FIELD_TERRAIN] = TERRAIN_NONE

        # Decrement other field conditions
        for idx in [FIELD_TRICK_ROOM, FIELD_GRAVITY, FIELD_MAGIC_ROOM,
                    FIELD_WONDER_ROOM, FIELD_FAIRY_LOCK]:
            if self.field[idx] > 0:
                self.field[idx] -= 1

        # Reset turn-only conditions
        self.field[FIELD_ION_DELUGE] = 0

        # Decrement side conditions
        for side in range(self.num_sides):
            for idx in [SC_REFLECT, SC_LIGHT_SCREEN, SC_AURORA_VEIL, SC_SAFEGUARD,
                       SC_MIST, SC_TAILWIND, SC_LUCKY_CHANT]:
                if self.side_conditions[side, idx] > 0:
                    self.side_conditions[side, idx] -= 1

            # Reset turn-only protections
            for idx in [SC_WIDE_GUARD, SC_QUICK_GUARD, SC_MAT_BLOCK, SC_CRAFTY_SHIELD]:
                self.side_conditions[side, idx] = 0

        # Decrement slot conditions (Future Sight, Doom Desire)
        for side in range(self.num_sides):
            for slot in range(self.active_slots):
                # Future Sight countdown
                if self.slot_conditions[side, slot, SLOT_FUTURE_SIGHT] > 0:
                    self.slot_conditions[side, slot, SLOT_FUTURE_SIGHT] -= 1
                # Doom Desire countdown
                if self.slot_conditions[side, slot, SLOT_DOOM_DESIRE] > 0:
                    self.slot_conditions[side, slot, SLOT_DOOM_DESIRE] -= 1

    def check_win_condition(self) -> Optional[int]:
        """Check if any side has won.

        Returns:
            Winning side index, -1 for draw, or None if battle continues
        """
        alive_sides = []

        for side in range(self.num_sides):
            has_alive = False
            for slot in range(self.team_size):
                pokemon = self.get_pokemon(side, slot)
                if pokemon.current_hp > 0:
                    has_alive = True
                    break
            if has_alive:
                alive_sides.append(side)

        if len(alive_sides) == 0:
            # Draw - all sides eliminated
            self.ended = True
            self.winner = -1
            return -1
        elif len(alive_sides) == 1:
            # One side wins
            self.ended = True
            self.winner = alive_sides[0]
            return alive_sides[0]

        return None  # Battle continues

    def get_fainted_actives(self, side: int) -> List[int]:
        """Get active slots with fainted Pokemon.

        Args:
            side: Side index

        Returns:
            List of active slot indices with fainted Pokemon
        """
        fainted = []
        for active_slot in range(self.active_slots):
            team_slot = self.active[side, active_slot]
            if team_slot >= 0:
                pokemon = self.get_pokemon(side, team_slot)
                if pokemon.is_fainted:
                    fainted.append(active_slot)
        return fainted

    def get_available_switches(self, side: int) -> List[int]:
        """Get team slots available for switching in.

        Args:
            side: Side index

        Returns:
            List of team slot indices with alive, non-active Pokemon
        """
        available = []
        active_slots = set(self.active[side])

        for slot in range(self.team_size):
            if slot not in active_slots:
                pokemon = self.get_pokemon(side, slot)
                if pokemon.current_hp > 0:
                    available.append(slot)

        return available

    def switch_pokemon(self, side: int, active_slot: int, team_slot: int) -> bool:
        """Switch a Pokemon into an active slot.

        Args:
            side: Side index
            active_slot: Active slot to switch into
            team_slot: Team slot of Pokemon to switch in

        Returns:
            True if switch was successful
        """
        if active_slot < 0 or active_slot >= self.active_slots:
            return False
        if team_slot < 0 or team_slot >= self.team_size:
            return False

        # Check if target is already active
        if team_slot in self.active[side]:
            return False

        # Check if target has HP
        pokemon = self.get_pokemon(side, team_slot)
        if pokemon.current_hp <= 0:
            return False

        # Reset stat stages of outgoing Pokemon
        old_slot = self.active[side, active_slot]
        if old_slot >= 0:
            old_pokemon = self.get_pokemon(side, old_slot)
            old_pokemon.reset_stages()

        # Perform switch
        self.active[side, active_slot] = team_slot

        # Reset stat stages of incoming Pokemon
        pokemon.reset_stages()

        return True

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def copy(self) -> 'BattleState':
        """Create a deep copy of this battle state."""
        new_state = BattleState(
            num_sides=self.num_sides,
            team_size=self.team_size,
            active_slots=self.active_slots,
            seed=0,  # Placeholder
            gen=self.gen,
            game_type=self.game_type,
        )

        # Copy arrays
        new_state.pokemons = self.pokemons.copy()
        new_state.active = self.active.copy()
        new_state.side_conditions = self.side_conditions.copy()
        new_state.slot_conditions = self.slot_conditions.copy()
        new_state.field = self.field.copy()
        new_state.pseudo_weather = self.pseudo_weather.copy()

        # Copy PRNG state
        new_state.prng = self.prng.clone()

        # Copy battle state
        new_state.turn = self.turn
        new_state.started = self.started
        new_state.ended = self.ended
        new_state.winner = self.winner
        new_state.last_move = self.last_move
        new_state.last_damage = self.last_damage
        new_state.request_state = self.request_state

        # Copy turn execution state
        new_state.mid_turn = self.mid_turn
        new_state.active_move = self.active_move
        new_state.active_pokemon = self.active_pokemon
        new_state.active_target = self.active_target
        new_state.last_successful_move_this_turn = self.last_successful_move_this_turn
        new_state.quick_claw_roll = self.quick_claw_roll
        new_state.effect_order = self.effect_order
        new_state.speed_order = self.speed_order.copy()

        # Copy logs and queues
        new_state._faint_queue = self._faint_queue.copy()
        new_state._action_log = self._action_log.copy()
        new_state._message_log = self._message_log.copy()

        return new_state

    def log_action(self, action: str) -> None:
        """Log an action for replay.

        Args:
            action: Action string to log
        """
        self._action_log.append(action)

    def log_message(self, message: str) -> None:
        """Log a battle message.

        Args:
            message: Message to log
        """
        self._message_log.append(message)

    @property
    def action_log(self) -> List[str]:
        """Get the action log."""
        return self._action_log

    @property
    def message_log(self) -> List[str]:
        """Get the message log."""
        return self._message_log

    @property
    def faint_queue(self) -> List[Tuple[int, int]]:
        """Get the faint queue."""
        return self._faint_queue

    def queue_faint(self, side: int, slot: int) -> None:
        """Add a Pokemon to the faint queue.

        Args:
            side: Side index
            slot: Team slot index
        """
        self._faint_queue.append((side, slot))

    def process_faint_queue(self) -> List[Tuple[int, int]]:
        """Process and clear the faint queue.

        Returns:
            List of (side, slot) tuples that fainted
        """
        fainted = self._faint_queue.copy()
        self._faint_queue.clear()
        return fainted

    def clear_turn_state(self) -> None:
        """Clear turn-specific state at the start of each turn."""
        self.active_move = 0
        self.active_pokemon = (-1, -1)
        self.active_target = (-1, -1)
        self.last_successful_move_this_turn = 0
        self.quick_claw_roll = False
        self.mid_turn = False

    def get_observation(self, side: int) -> np.ndarray:
        """Get a flattened observation array for a side.

        This is useful for RL environments that need a flat observation space.

        Args:
            side: Side index (0 or 1) - the observing side

        Returns:
            Flattened numpy array containing visible state
        """
        # For now, return full state (partial observability can be added later)
        obs_parts = [
            self.pokemons[side].flatten(),  # Own team
            self.pokemons[1 - side].flatten(),  # Opponent team
            self.active.flatten(),
            self.side_conditions.flatten(),
            self.field,
            np.array([self.turn, self.ended, self.winner]),
        ]
        return np.concatenate(obs_parts)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"BattleState(turn={self.turn}, ended={self.ended}, "
            f"weather={WEATHER_NAMES.get(self.weather, 'unknown')}, "
            f"terrain={TERRAIN_NAMES.get(self.terrain, 'unknown')})"
        )
