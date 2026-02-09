"""Battle Engine - Main battle loop and action resolution.

This module provides the BattleEngine class that orchestrates Pokemon battles:
- Action queue management with priority/speed sorting
- Move execution with damage calculation
- Switch handling
- Faint processing and victory detection
- End-of-turn residual effects
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Callable, Any
from functools import cmp_to_key

from .battle_state import (
    BattleState,
    FIELD_WEATHER, FIELD_WEATHER_TURNS, FIELD_TERRAIN, FIELD_TERRAIN_TURNS,
    FIELD_TRICK_ROOM, FIELD_GRAVITY,
    WEATHER_NONE, WEATHER_SAND, WEATHER_HAIL, WEATHER_SNOW,
    TERRAIN_NONE, TERRAIN_GRASSY,
    SC_REFLECT, SC_LIGHT_SCREEN, SC_AURORA_VEIL, SC_SAFEGUARD,
    SC_MIST, SC_TAILWIND, SC_WIDE_GUARD, SC_QUICK_GUARD,
    SC_SPIKES, SC_TOXIC_SPIKES, SC_STEALTH_ROCK, SC_STICKY_WEB,
)
from .layout import (
    P_CURRENT_HP, P_STATUS, P_STATUS_COUNTER,
    P_STAT_SPE, P_TYPE1, P_TYPE2, P_TERA_TYPE,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
    P_STAGE_ACC, P_STAGE_EVA,
    P_MOVE1, P_PP1,
    P_VOL_PROTECT, P_VOL_FLINCH, P_VOL_CONFUSION, P_VOL_LEECH_SEED,
    P_VOL_SUBSTITUTE, P_VOL_SUBSTITUTE_HP,
    P_VOL_ENCORE, P_VOL_TAUNT, P_VOL_DISABLE, P_VOL_LAST_MOVE,
    STATUS_NONE, STATUS_BURN, STATUS_FREEZE, STATUS_PARALYSIS,
    STATUS_POISON, STATUS_BADLY_POISONED, STATUS_SLEEP,
    STAGE_INDICES,
)
from .pokemon import Pokemon
from .damage import (
    calculate_damage, calculate_recoil, calculate_drain,
    calculate_type_effectiveness, check_accuracy,
    get_multi_hit_count, DamageResult,
)
from data.moves import MoveData, MoveCategory, MoveTarget, MoveFlag
from data.types import Type


# =============================================================================
# Action Types and Data Structures
# =============================================================================

class ActionType(IntEnum):
    """Types of actions in the battle queue.

    Values correspond to execution order (lower = earlier).
    From battle-queue.ts: switches=103, moves=200, residual=300.
    """
    TEAM_PREVIEW = 1    # Team preview selection
    START = 2           # Battle start
    BEFORE_TURN = 4     # Before-turn hook
    SWITCH = 103        # Switch Pokemon
    MEGA_EVO = 104      # Mega evolve
    ULTRA_BURST = 105   # Ultra burst
    TERASTALLIZE = 106  # Terastallize
    MOVE = 200          # Use a move
    RESIDUAL = 300      # End-of-turn effects


@dataclass
class Action:
    """An action in the battle queue.

    Actions are sorted by:
    1. action_type (lower first)
    2. priority (higher first)
    3. speed (higher first, or lower if Trick Room)
    4. Random tie-breaker
    """
    action_type: ActionType
    side: int
    slot: int  # Team slot for the Pokemon
    priority: int = 0
    speed: int = 0
    move_id: int = 0
    target_side: int = -1
    target_slot: int = -1  # Target's team slot
    mega: bool = False
    terastallize: bool = False
    zmove: bool = False
    dynamax: bool = False

    def __hash__(self):
        return hash((self.action_type, self.side, self.slot, self.move_id))


@dataclass
class Choice:
    """A player's choice for one of their active Pokemon.

    Used to construct Actions from player input.
    """
    choice_type: str  # 'move', 'switch', 'pass'
    slot: int  # Active slot index (not team slot)
    move_slot: int = -1      # Move slot (0-3) for 'move'
    target: int = 0          # Target position for 'move'
    switch_to: int = -1      # Team slot to switch to for 'switch'
    # Special mechanics flags
    terastallize: bool = False  # Terastallize before moving
    mega: bool = False          # Mega evolve before moving
    zmove: bool = False         # Use Z-Move version of move
    dynamax: bool = False       # Dynamax before moving


# =============================================================================
# Action Sorting
# =============================================================================

def compare_actions(a: Action, b: Action, state: BattleState) -> int:
    """Compare two actions for sorting.

    Returns negative if a should go first, positive if b should go first.

    Sort order:
    1. Action type (lower value = earlier)
    2. Priority (higher = earlier)
    3. Speed (higher = earlier, inverted under Trick Room)
    """
    # 1. Order by action type (switches before moves)
    if a.action_type != b.action_type:
        return a.action_type - b.action_type

    # 2. Order by priority (higher first)
    if a.priority != b.priority:
        return b.priority - a.priority

    # 3. Order by speed (higher first, reversed in Trick Room)
    speed_a, speed_b = a.speed, b.speed
    if state.field[FIELD_TRICK_ROOM] > 0:
        # Trick Room: slower Pokemon go first
        speed_a, speed_b = -speed_a, -speed_b

    if speed_a != speed_b:
        return speed_b - speed_a

    # Equal - will be randomized
    return 0


def sort_actions(actions: List[Action], state: BattleState) -> List[Action]:
    """Sort actions by priority/speed with random tie-breaking.

    Uses selection sort (like Pokemon Showdown) to allow stable
    random tie-breaking via PRNG.
    """
    if not actions:
        return []

    result = []
    remaining = list(actions)

    while remaining:
        # Find all actions tied for first
        best = remaining[0]
        ties = [best]

        for action in remaining[1:]:
            cmp = compare_actions(action, best, state)
            if cmp < 0:
                # This action is better
                best = action
                ties = [action]
            elif cmp == 0:
                # Tied with current best
                ties.append(action)

        # Random selection among ties
        if len(ties) > 1:
            idx = state.prng.next(len(ties))
            selected = ties[idx]
        else:
            selected = ties[0]

        result.append(selected)
        remaining.remove(selected)

    return result


# =============================================================================
# Target Resolution
# =============================================================================

def resolve_targets(
    state: BattleState,
    action: Action,
    move: MoveData,
) -> List[Tuple[int, int]]:
    """Resolve target(s) for a move based on MoveTarget.

    Args:
        state: Battle state
        action: The move action
        move: Move data

    Returns:
        List of (side, team_slot) tuples for valid targets.
        For side-targeting moves, team_slot is -1.
    """
    user_side = action.side
    opp_side = 1 - user_side

    targets = []

    if move.target == MoveTarget.SELF:
        # Self only
        targets.append((user_side, action.slot))

    elif move.target == MoveTarget.ADJACENT_ALLY_OR_SELF:
        # User or adjacent ally - use specified target or self
        if action.target_side == user_side and action.target_slot >= 0:
            targets.append((action.target_side, action.target_slot))
        else:
            targets.append((user_side, action.slot))

    elif move.target == MoveTarget.ADJACENT_ALLY:
        # Adjacent ally only
        if action.target_side == user_side and action.target_slot != action.slot:
            targets.append((action.target_side, action.target_slot))
        else:
            # Find an ally
            for active_slot in range(state.active_slots):
                team_slot = state.active[user_side, active_slot]
                if team_slot >= 0 and team_slot != action.slot:
                    targets.append((user_side, team_slot))
                    break

    elif move.target == MoveTarget.ALL_ADJACENT_FOES:
        # All active foes (spread move)
        for active_slot in range(state.active_slots):
            team_slot = state.active[opp_side, active_slot]
            if team_slot >= 0:
                pokemon = state.get_pokemon(opp_side, team_slot)
                if not pokemon.is_fainted:
                    targets.append((opp_side, team_slot))

    elif move.target == MoveTarget.ALL_ADJACENT:
        # All adjacent Pokemon (allies and foes)
        # Add allies first
        for active_slot in range(state.active_slots):
            team_slot = state.active[user_side, active_slot]
            if team_slot >= 0 and team_slot != action.slot:
                pokemon = state.get_pokemon(user_side, team_slot)
                if not pokemon.is_fainted:
                    targets.append((user_side, team_slot))
        # Then foes
        for active_slot in range(state.active_slots):
            team_slot = state.active[opp_side, active_slot]
            if team_slot >= 0:
                pokemon = state.get_pokemon(opp_side, team_slot)
                if not pokemon.is_fainted:
                    targets.append((opp_side, team_slot))

    elif move.target == MoveTarget.ALL:
        # All Pokemon on field
        for side in range(state.num_sides):
            for active_slot in range(state.active_slots):
                team_slot = state.active[side, active_slot]
                if team_slot >= 0:
                    pokemon = state.get_pokemon(side, team_slot)
                    if not pokemon.is_fainted:
                        targets.append((side, team_slot))

    elif move.target == MoveTarget.ALL_ALLIES:
        # All allies (not self)
        for active_slot in range(state.active_slots):
            team_slot = state.active[user_side, active_slot]
            if team_slot >= 0 and team_slot != action.slot:
                pokemon = state.get_pokemon(user_side, team_slot)
                if not pokemon.is_fainted:
                    targets.append((user_side, team_slot))

    elif move.target == MoveTarget.ALLY_SIDE:
        # User's side (for Reflect, Light Screen, etc.)
        targets.append((user_side, -1))

    elif move.target == MoveTarget.FOE_SIDE:
        # Opponent's side (for hazards, etc.)
        targets.append((opp_side, -1))

    elif move.target == MoveTarget.ALLY_TEAM:
        # User's entire team (for Heal Bell, etc.)
        targets.append((user_side, -2))

    elif move.target == MoveTarget.RANDOM_NORMAL:
        # Random adjacent foe
        valid_foes = []
        for active_slot in range(state.active_slots):
            team_slot = state.active[opp_side, active_slot]
            if team_slot >= 0:
                pokemon = state.get_pokemon(opp_side, team_slot)
                if not pokemon.is_fainted:
                    valid_foes.append((opp_side, team_slot))
        if valid_foes:
            idx = state.prng.next(len(valid_foes))
            targets.append(valid_foes[idx])

    else:
        # NORMAL, ADJACENT_FOE, ANY, SCRIPTED - single target
        if action.target_side >= 0 and action.target_slot >= 0:
            pokemon = state.get_pokemon(action.target_side, action.target_slot)
            if not pokemon.is_fainted:
                targets.append((action.target_side, action.target_slot))
        else:
            # Default to first active foe
            for active_slot in range(state.active_slots):
                team_slot = state.active[opp_side, active_slot]
                if team_slot >= 0:
                    pokemon = state.get_pokemon(opp_side, team_slot)
                    if not pokemon.is_fainted:
                        targets.append((opp_side, team_slot))
                        break

    return targets


# =============================================================================
# Battle Engine
# =============================================================================

class BattleEngine:
    """Executes battle turns using BattleState.

    The engine manages:
    - Converting player choices to sorted action queue
    - Executing actions in priority order
    - Processing faints and forced switches
    - Running end-of-turn residual effects
    - Detecting victory conditions
    """

    __slots__ = (
        'state', 'action_queue', 'turn', 'ended', 'winner',
        '_pending_switches', '_move_registry',
    )

    def __init__(self, state: BattleState, move_registry: Optional[Dict[int, MoveData]] = None):
        """Initialize the battle engine.

        Args:
            state: The BattleState to operate on
            move_registry: Optional dict mapping move IDs to MoveData
        """
        self.state = state
        self.action_queue: List[Action] = []
        self.turn = 0
        self.ended = False
        self.winner = -1
        self._pending_switches: List[Tuple[int, int]] = []  # (side, active_slot)
        self._move_registry = move_registry or {}

    def get_move(self, move_id: int) -> Optional[MoveData]:
        """Look up a move by ID."""
        return self._move_registry.get(move_id)

    # -------------------------------------------------------------------------
    # Main Battle Loop
    # -------------------------------------------------------------------------

    def step(self, choices: Dict[int, List[Choice]]) -> bool:
        """Execute one turn of battle.

        Args:
            choices: Dict mapping side index to list of Choices

        Returns:
            True if battle continues, False if ended
        """
        if self.ended:
            return False

        self.turn += 1
        self.state.turn = self.turn
        self.state.mid_turn = True

        # Clear per-turn volatiles
        self._clear_turn_volatiles()

        # Convert choices to actions
        actions = self.resolve_choices(choices)

        # Sort actions by priority/speed
        self.action_queue = sort_actions(actions, self.state)

        # Execute actions
        for action in self.action_queue:
            if self.ended:
                break
            self.execute_action(action)

            # Process any faints after each action
            self._process_faints()

            # Check victory after faints
            winner = self.check_victory()
            if winner is not None:
                self.ended = True
                self.winner = winner
                self.state.ended = True
                self.state.winner = winner
                break

        # Run residual effects if battle continues
        if not self.ended:
            self.run_residuals()

            # Process faints from residuals
            self._process_faints()

            # Final victory check
            winner = self.check_victory()
            if winner is not None:
                self.ended = True
                self.winner = winner
                self.state.ended = True
                self.state.winner = winner

        # Decrement field counters
        self._decrement_field_counters()

        self.state.mid_turn = False
        return not self.ended

    def _clear_turn_volatiles(self) -> None:
        """Clear per-turn volatile flags."""
        for side in range(self.state.num_sides):
            for active_slot in range(self.state.active_slots):
                team_slot = self.state.active[side, active_slot]
                if team_slot >= 0:
                    pokemon = self.state.get_pokemon(side, team_slot)
                    pokemon.data[P_VOL_PROTECT] = 0
                    pokemon.data[P_VOL_FLINCH] = 0

            # Clear side turn conditions
            self.state.side_conditions[side, SC_WIDE_GUARD] = 0
            self.state.side_conditions[side, SC_QUICK_GUARD] = 0

    # -------------------------------------------------------------------------
    # Choice Resolution
    # -------------------------------------------------------------------------

    def resolve_choices(self, choices: Dict[int, List[Choice]]) -> List[Action]:
        """Convert player choices to a list of Actions.

        Args:
            choices: Dict mapping side index to list of Choices

        Returns:
            List of Action objects (unsorted)
        """
        actions = []

        for side, side_choices in choices.items():
            for choice in side_choices:
                if choice.choice_type == 'pass':
                    continue

                # Get the team slot for this active slot
                team_slot = self.state.active[side, choice.slot]
                if team_slot < 0:
                    continue

                pokemon = self.state.get_pokemon(side, team_slot)
                if pokemon.is_fainted:
                    continue

                if choice.choice_type == 'move':
                    action = self._create_move_action(side, team_slot, pokemon, choice)
                    if action:
                        actions.append(action)

                elif choice.choice_type == 'switch':
                    action = self._create_switch_action(side, team_slot, pokemon, choice)
                    if action:
                        actions.append(action)

        return actions

    def _create_move_action(
        self, side: int, team_slot: int, pokemon: Pokemon, choice: Choice
    ) -> Optional[Action]:
        """Create a move action from a choice."""
        move_id = pokemon.get_move(choice.move_slot)
        if move_id == 0:
            return None

        move = self.get_move(move_id)
        priority = move.priority if move else 0

        # Parse target from choice
        target_side, target_slot = self._parse_target(side, choice.target)

        return Action(
            action_type=ActionType.MOVE,
            side=side,
            slot=team_slot,
            priority=priority,
            speed=pokemon.speed,
            move_id=move_id,
            target_side=target_side,
            target_slot=target_slot,
        )

    def _create_switch_action(
        self, side: int, team_slot: int, pokemon: Pokemon, choice: Choice
    ) -> Optional[Action]:
        """Create a switch action from a choice."""
        switch_to = choice.switch_to
        if switch_to < 0 or switch_to >= self.state.team_size:
            return None

        # Check if target is valid (not fainted, not already active)
        target = self.state.get_pokemon(side, switch_to)
        if target.is_fainted:
            return None
        if self.state.is_pokemon_active(side, switch_to):
            return None

        return Action(
            action_type=ActionType.SWITCH,
            side=side,
            slot=team_slot,
            priority=0,
            speed=pokemon.speed,
            target_slot=switch_to,  # Slot to switch to
        )

    def _parse_target(self, user_side: int, target: int) -> Tuple[int, int]:
        """Parse a target value into (side, slot).

        Target encoding:
        - Positive: opponent's active slots (1-indexed)
        - Negative: user's active slots (absolute value, 1-indexed)
        - Zero: no specific target
        """
        if target == 0:
            return (-1, -1)

        opp_side = 1 - user_side

        if target > 0:
            # Targeting opponent
            active_slot = target - 1
            if active_slot < self.state.active_slots:
                team_slot = self.state.active[opp_side, active_slot]
                if team_slot >= 0:
                    return (opp_side, team_slot)
        else:
            # Targeting ally
            active_slot = abs(target) - 1
            if active_slot < self.state.active_slots:
                team_slot = self.state.active[user_side, active_slot]
                if team_slot >= 0:
                    return (user_side, team_slot)

        return (-1, -1)

    # -------------------------------------------------------------------------
    # Action Execution
    # -------------------------------------------------------------------------

    def execute_action(self, action: Action) -> bool:
        """Execute a single action.

        Args:
            action: The action to execute

        Returns:
            True if action succeeded
        """
        if action.action_type == ActionType.SWITCH:
            return self.execute_switch(action)
        elif action.action_type == ActionType.MOVE:
            return self.execute_move(action)

        return False

    def execute_switch(self, action: Action) -> bool:
        """Execute a switch action.

        Args:
            action: The switch action

        Returns:
            True if switch succeeded
        """
        side = action.side
        old_slot = action.slot
        new_slot = action.target_slot

        # Find which active slot the Pokemon is in
        active_slot = -1
        for i in range(self.state.active_slots):
            if self.state.active[side, i] == old_slot:
                active_slot = i
                break

        if active_slot < 0:
            return False

        # Get the old Pokemon and clear its volatiles
        old_pokemon = self.state.get_pokemon(side, old_slot)
        self._clear_volatiles(old_pokemon)
        old_pokemon.reset_stages()

        # Switch the active Pokemon
        self.state.active[side, active_slot] = new_slot

        # Apply entry hazards to new Pokemon
        self._apply_entry_hazards(side, new_slot)

        return True

    def _clear_volatiles(self, pokemon: Pokemon) -> None:
        """Clear volatile status conditions on switch-out."""
        # Reset all volatile indices (44-86 in layout)
        for i in range(P_VOL_PROTECT, P_VOL_TELEKINESIS + 1):
            if i < len(pokemon.data):
                pokemon.data[i] = 0

    def _apply_entry_hazards(self, side: int, team_slot: int) -> None:
        """Apply entry hazards when a Pokemon switches in."""
        pokemon = self.state.get_pokemon(side, team_slot)

        # Stealth Rock (1/8 HP * type effectiveness)
        if self.state.side_conditions[side, SC_STEALTH_ROCK] > 0:
            effectiveness = calculate_type_effectiveness(
                Type.ROCK,
                pokemon.type1,
                pokemon.type2,
                pokemon.data[P_TERA_TYPE],
            )
            damage = max(1, int(pokemon.max_hp * effectiveness / 8))
            pokemon.take_damage(damage)
            if pokemon.is_fainted:
                self.state._faint_queue.append((side, team_slot))
                return

        # Spikes (1/8, 1/6, 1/4 HP for 1, 2, 3 layers)
        spikes_layers = self.state.side_conditions[side, SC_SPIKES]
        if spikes_layers > 0 and self._is_grounded(pokemon):
            if spikes_layers == 1:
                damage = max(1, pokemon.max_hp // 8)
            elif spikes_layers == 2:
                damage = max(1, pokemon.max_hp // 6)
            else:
                damage = max(1, pokemon.max_hp // 4)
            pokemon.take_damage(damage)
            if pokemon.is_fainted:
                self.state._faint_queue.append((side, team_slot))
                return

        # Toxic Spikes (poison or bad poison)
        toxic_layers = self.state.side_conditions[side, SC_TOXIC_SPIKES]
        if toxic_layers > 0 and self._is_grounded(pokemon):
            # Poison-type absorbs Toxic Spikes
            if pokemon.type1 == Type.POISON.value or pokemon.type2 == Type.POISON.value:
                self.state.side_conditions[side, SC_TOXIC_SPIKES] = 0
            elif pokemon.status == STATUS_NONE:
                if toxic_layers == 1:
                    pokemon.status = STATUS_POISON
                else:
                    pokemon.status = STATUS_BADLY_POISONED
                    pokemon.status_counter = 0

        # Sticky Web (lower speed by 1)
        if self.state.side_conditions[side, SC_STICKY_WEB] > 0 and self._is_grounded(pokemon):
            pokemon.modify_stage(P_STAGE_SPE, -1)

    def _is_grounded(self, pokemon: Pokemon) -> bool:
        """Check if a Pokemon is grounded (affected by ground-based hazards)."""
        # Flying type is not grounded
        if pokemon.type1 == Type.FLYING.value or pokemon.type2 == Type.FLYING.value:
            return False
        # TODO: Check for Levitate ability, Air Balloon item, Magnet Rise, etc.
        # For now, simplify to just Flying type check
        return True

    def execute_move(self, action: Action) -> bool:
        """Execute a move action.

        Args:
            action: The move action

        Returns:
            True if move succeeded
        """
        side = action.side
        team_slot = action.slot
        move_id = action.move_id

        pokemon = self.state.get_pokemon(side, team_slot)

        # Check if Pokemon can move
        if pokemon.is_fainted:
            return False

        # Check flinch
        if pokemon.data[P_VOL_FLINCH]:
            return False

        # Check sleep
        if pokemon.status == STATUS_SLEEP:
            counter = pokemon.status_counter
            if counter > 0:
                pokemon.status_counter = counter - 1
                return False
            else:
                # Wake up
                pokemon.status = STATUS_NONE

        # Check freeze (20% chance to thaw)
        if pokemon.status == STATUS_FREEZE:
            if self.state.prng.random_chance(20, 100):
                pokemon.status = STATUS_NONE
            else:
                return False

        # Check paralysis (25% chance to be fully paralyzed)
        if pokemon.status == STATUS_PARALYSIS:
            if self.state.prng.random_chance(25, 100):
                return False

        # Check confusion
        if pokemon.data[P_VOL_CONFUSION] > 0:
            pokemon.data[P_VOL_CONFUSION] -= 1
            # 33% chance to hurt self
            if self.state.prng.random_chance(33, 100):
                # Apply confusion damage
                from .damage import calculate_confusion_damage
                damage = calculate_confusion_damage(pokemon)
                pokemon.take_damage(damage)
                if pokemon.is_fainted:
                    self.state._faint_queue.append((side, team_slot))
                return False

        move = self.get_move(move_id)
        if not move:
            return False

        # Find move slot and deduct PP
        move_slot = -1
        for i in range(4):
            if pokemon.get_move(i) == move_id:
                move_slot = i
                break

        if move_slot >= 0:
            if not pokemon.use_pp(move_slot):
                return False  # No PP left

        # Store active move info
        self.state.active_move = move_id
        self.state.active_pokemon = (side, team_slot)

        # Resolve targets
        targets = resolve_targets(self.state, action, move)
        if not targets:
            return False

        # Track move success and total damage (for recoil)
        move_success = False
        total_damage = 0

        # Check if this is a spread move
        is_spread = len([t for t in targets if t[1] >= 0]) > 1

        for target_side, target_slot in targets:
            # Handle side-targeting moves
            if target_slot < 0:
                success = self._apply_side_effect(move, side, target_side)
                move_success = move_success or success
                continue

            target = self.state.get_pokemon(target_side, target_slot)

            if target.is_fainted:
                continue

            self.state.active_target = (target_side, target_slot)

            # Check protection
            if self._check_protection(target_side, target_slot, move):
                continue

            # Check type immunity for damaging moves
            if move.category != MoveCategory.STATUS:
                effectiveness = calculate_type_effectiveness(
                    move.type,
                    target.type1,
                    target.type2,
                    target.data[P_TERA_TYPE],
                )
                if effectiveness == 0.0:
                    continue

            # Accuracy check
            if move.accuracy and move.accuracy > 0:
                acc_stage = pokemon.get_stage(P_STAGE_ACC)
                eva_stage = target.get_stage(P_STAGE_EVA)
                random_roll = self.state.prng.next(100)
                if not check_accuracy(move.accuracy, acc_stage, eva_stage, random_roll):
                    continue

            # Apply damage for damaging moves
            if move.category != MoveCategory.STATUS and move.base_power > 0:
                # Handle multi-hit moves
                num_hits = 1
                if move.multi_hit:
                    random_idx = self.state.prng.next(20)
                    num_hits = get_multi_hit_count(random_idx)

                for hit in range(num_hits):
                    if target.is_fainted:
                        break

                    result = calculate_damage(
                        pokemon, target, move, self.state,
                        is_spread=is_spread,
                    )

                    if result.is_immune:
                        break

                    actual_damage = target.take_damage(result.damage)
                    total_damage += actual_damage

                    if target.is_fainted:
                        self.state._faint_queue.append((target_side, target_slot))

                move_success = True

            # Apply secondary effects
            if move.secondary and move_success:
                self._apply_secondary_effect(pokemon, target, move)

        # Handle recoil
        if move.recoil > 0 and total_damage > 0:
            recoil_damage = calculate_recoil(total_damage, move.recoil)
            pokemon.take_damage(recoil_damage)
            if pokemon.is_fainted:
                self.state._faint_queue.append((side, team_slot))

        # Handle drain
        if move.drain > 0 and total_damage > 0:
            drain_amount = calculate_drain(total_damage, move.drain)
            pokemon.heal(drain_amount)

        # Update last move
        self.state.last_move = move_id
        self.state.last_damage = total_damage
        pokemon.data[P_VOL_LAST_MOVE] = move_id

        return move_success

    def _check_protection(self, side: int, slot: int, move: MoveData) -> bool:
        """Check if target is protected from the move."""
        pokemon = self.state.get_pokemon(side, slot)

        # Check if move can be protected
        if not (move.flags & MoveFlag.PROTECT):
            return False

        # Check Protect volatile
        if pokemon.data[P_VOL_PROTECT]:
            return True

        # Check Wide Guard (for spread moves)
        if move.target in (MoveTarget.ALL_ADJACENT, MoveTarget.ALL_ADJACENT_FOES, MoveTarget.ALL):
            if self.state.side_conditions[side, SC_WIDE_GUARD]:
                return True

        # Check Quick Guard (for priority moves)
        if move.priority > 0:
            if self.state.side_conditions[side, SC_QUICK_GUARD]:
                return True

        return False

    def _apply_side_effect(self, move: MoveData, user_side: int, target_side: int) -> bool:
        """Apply a side-targeting move effect."""
        # This is a stub for moves like Reflect, Light Screen, hazards, etc.
        # Full implementation would check move ID and apply appropriate effect
        return True

    def _apply_secondary_effect(self, attacker: Pokemon, target: Pokemon, move: MoveData) -> None:
        """Apply secondary effects of a move."""
        secondary = move.secondary
        if not secondary:
            return

        # Check chance
        if secondary.chance < 100:
            if not self.state.prng.random_chance(secondary.chance, 100):
                return

        # Apply status
        if secondary.status and target.status == STATUS_NONE:
            status_map = {
                'brn': STATUS_BURN,
                'par': STATUS_PARALYSIS,
                'psn': STATUS_POISON,
                'tox': STATUS_BADLY_POISONED,
                'frz': STATUS_FREEZE,
                'slp': STATUS_SLEEP,
            }
            if secondary.status in status_map:
                target.status = status_map[secondary.status]
                if secondary.status == 'slp':
                    # Sleep duration: 1-3 turns
                    target.status_counter = self.state.prng.random(1, 3)
                elif secondary.status == 'tox':
                    target.status_counter = 0

        # Apply stat boosts to target
        if secondary.boosts:
            for stat, delta in secondary.boosts.items():
                stage_map = {
                    'atk': P_STAGE_ATK, 'def': P_STAGE_DEF,
                    'spa': P_STAGE_SPA, 'spd': P_STAGE_SPD,
                    'spe': P_STAGE_SPE, 'acc': P_STAGE_ACC,
                    'eva': P_STAGE_EVA,
                }
                if stat in stage_map:
                    target.modify_stage(stage_map[stat], delta)

        # Apply stat boosts to attacker
        if secondary.self_boosts:
            for stat, delta in secondary.self_boosts.items():
                stage_map = {
                    'atk': P_STAGE_ATK, 'def': P_STAGE_DEF,
                    'spa': P_STAGE_SPA, 'spd': P_STAGE_SPD,
                    'spe': P_STAGE_SPE, 'acc': P_STAGE_ACC,
                    'eva': P_STAGE_EVA,
                }
                if stat in stage_map:
                    attacker.modify_stage(stage_map[stat], delta)

        # Apply confusion
        if secondary.volatile_status == 'confusion':
            if target.data[P_VOL_CONFUSION] == 0:
                target.data[P_VOL_CONFUSION] = self.state.prng.random(2, 5)

    # -------------------------------------------------------------------------
    # Faint Handling
    # -------------------------------------------------------------------------

    def _process_faints(self) -> None:
        """Process the faint queue."""
        while self.state._faint_queue:
            side, team_slot = self.state._faint_queue.pop(0)

            # Clear from active slots
            for active_slot in range(self.state.active_slots):
                if self.state.active[side, active_slot] == team_slot:
                    # Mark slot as needing replacement
                    self._pending_switches.append((side, active_slot))
                    # Don't clear active yet - will be done when replacement switches in
                    break

    def get_forced_switches(self) -> List[Tuple[int, int]]:
        """Get list of (side, active_slot) that need forced switches."""
        return list(self._pending_switches)

    def apply_forced_switch(self, side: int, active_slot: int, new_team_slot: int) -> bool:
        """Apply a forced switch after a faint.

        Args:
            side: Side index
            active_slot: Active slot that needs filling
            new_team_slot: Team slot of Pokemon to switch in

        Returns:
            True if switch succeeded
        """
        # Validate
        if new_team_slot < 0 or new_team_slot >= self.state.team_size:
            return False

        pokemon = self.state.get_pokemon(side, new_team_slot)
        if pokemon.is_fainted:
            return False

        if self.state.is_pokemon_active(side, new_team_slot):
            return False

        # Apply switch
        self.state.active[side, active_slot] = new_team_slot

        # Apply entry hazards
        self._apply_entry_hazards(side, new_team_slot)

        # Remove from pending
        if (side, active_slot) in self._pending_switches:
            self._pending_switches.remove((side, active_slot))

        return True

    def check_victory(self) -> Optional[int]:
        """Check if the battle has ended.

        Returns:
            Winning side index, or None if battle continues
        """
        for side in range(self.state.num_sides):
            # Check if all Pokemon on this side are fainted
            all_fainted = True
            for team_slot in range(self.state.team_size):
                pokemon = self.state.get_pokemon(side, team_slot)
                if pokemon.species_id > 0 and not pokemon.is_fainted:
                    all_fainted = False
                    break

            if all_fainted:
                # This side lost, other side wins
                return 1 - side

        return None

    # -------------------------------------------------------------------------
    # Residual Effects
    # -------------------------------------------------------------------------

    def run_residuals(self) -> None:
        """Run end-of-turn residual effects in speed order."""
        # Collect active Pokemon with their speeds
        actives = []
        for side in range(self.state.num_sides):
            for active_slot in range(self.state.active_slots):
                team_slot = self.state.active[side, active_slot]
                if team_slot >= 0:
                    pokemon = self.state.get_pokemon(side, team_slot)
                    if not pokemon.is_fainted:
                        actives.append((side, team_slot, pokemon.speed))

        # Sort by speed (higher first, or lower if Trick Room)
        if self.state.field[FIELD_TRICK_ROOM] > 0:
            actives.sort(key=lambda x: x[2])
        else:
            actives.sort(key=lambda x: -x[2])

        # Apply weather damage
        weather = self.state.field[FIELD_WEATHER]
        for side, team_slot, _ in actives:
            pokemon = self.state.get_pokemon(side, team_slot)
            if pokemon.is_fainted:
                continue
            self._apply_weather_damage(pokemon, weather, side, team_slot)

        # Apply status damage
        for side, team_slot, _ in actives:
            pokemon = self.state.get_pokemon(side, team_slot)
            if pokemon.is_fainted:
                continue
            self._apply_status_damage(pokemon, side, team_slot)

        # Apply Leech Seed
        for side, team_slot, _ in actives:
            pokemon = self.state.get_pokemon(side, team_slot)
            if pokemon.is_fainted:
                continue
            self._apply_leech_seed(pokemon, side, team_slot)

        # Apply terrain healing (Grassy Terrain)
        if self.state.field[FIELD_TERRAIN] == TERRAIN_GRASSY:
            for side, team_slot, _ in actives:
                pokemon = self.state.get_pokemon(side, team_slot)
                if pokemon.is_fainted:
                    continue
                if self._is_grounded(pokemon):
                    heal = max(1, pokemon.max_hp // 16)
                    pokemon.heal(heal)

    def _apply_weather_damage(self, pokemon: Pokemon, weather: int, side: int, team_slot: int) -> None:
        """Apply weather damage at end of turn."""
        if weather == WEATHER_SAND:
            # Sandstorm damages non-Rock/Ground/Steel types
            type1, type2 = pokemon.type1, pokemon.type2
            immune_types = (Type.ROCK.value, Type.GROUND.value, Type.STEEL.value)
            if type1 not in immune_types and type2 not in immune_types:
                damage = max(1, pokemon.max_hp // 16)
                pokemon.take_damage(damage)
                if pokemon.is_fainted:
                    self.state._faint_queue.append((side, team_slot))

        elif weather == WEATHER_HAIL:
            # Hail damages non-Ice types
            if pokemon.type1 != Type.ICE.value and pokemon.type2 != Type.ICE.value:
                damage = max(1, pokemon.max_hp // 16)
                pokemon.take_damage(damage)
                if pokemon.is_fainted:
                    self.state._faint_queue.append((side, team_slot))

    def _apply_status_damage(self, pokemon: Pokemon, side: int, team_slot: int) -> None:
        """Apply status condition damage at end of turn."""
        status = pokemon.status

        if status == STATUS_BURN:
            damage = max(1, pokemon.max_hp // 16)
            pokemon.take_damage(damage)
            if pokemon.is_fainted:
                self.state._faint_queue.append((side, team_slot))

        elif status == STATUS_POISON:
            damage = max(1, pokemon.max_hp // 8)
            pokemon.take_damage(damage)
            if pokemon.is_fainted:
                self.state._faint_queue.append((side, team_slot))

        elif status == STATUS_BADLY_POISONED:
            counter = pokemon.status_counter + 1
            pokemon.status_counter = counter
            damage = max(1, pokemon.max_hp * counter // 16)
            pokemon.take_damage(damage)
            if pokemon.is_fainted:
                self.state._faint_queue.append((side, team_slot))

    def _apply_leech_seed(self, pokemon: Pokemon, side: int, team_slot: int) -> None:
        """Apply Leech Seed damage at end of turn."""
        if pokemon.data[P_VOL_LEECH_SEED] == 0:
            return

        damage = max(1, pokemon.max_hp // 8)
        actual = pokemon.take_damage(damage)

        if pokemon.is_fainted:
            self.state._faint_queue.append((side, team_slot))

        # Heal the opponent (find first active non-fainted)
        opp_side = 1 - side
        for active_slot in range(self.state.active_slots):
            opp_slot = self.state.active[opp_side, active_slot]
            if opp_slot >= 0:
                opp = self.state.get_pokemon(opp_side, opp_slot)
                if not opp.is_fainted:
                    opp.heal(actual)
                    break

    def _decrement_field_counters(self) -> None:
        """Decrement field condition turn counters."""
        # Weather
        if self.state.field[FIELD_WEATHER_TURNS] > 0:
            self.state.field[FIELD_WEATHER_TURNS] -= 1
            if self.state.field[FIELD_WEATHER_TURNS] == 0:
                self.state.field[FIELD_WEATHER] = WEATHER_NONE

        # Terrain
        if self.state.field[FIELD_TERRAIN_TURNS] > 0:
            self.state.field[FIELD_TERRAIN_TURNS] -= 1
            if self.state.field[FIELD_TERRAIN_TURNS] == 0:
                self.state.field[FIELD_TERRAIN] = TERRAIN_NONE

        # Trick Room
        if self.state.field[FIELD_TRICK_ROOM] > 0:
            self.state.field[FIELD_TRICK_ROOM] -= 1

        # Gravity
        if self.state.field[FIELD_GRAVITY] > 0:
            self.state.field[FIELD_GRAVITY] -= 1

        # Side conditions
        for side in range(self.state.num_sides):
            # Reflect
            if self.state.side_conditions[side, SC_REFLECT] > 0:
                self.state.side_conditions[side, SC_REFLECT] -= 1
            # Light Screen
            if self.state.side_conditions[side, SC_LIGHT_SCREEN] > 0:
                self.state.side_conditions[side, SC_LIGHT_SCREEN] -= 1
            # Aurora Veil
            if self.state.side_conditions[side, SC_AURORA_VEIL] > 0:
                self.state.side_conditions[side, SC_AURORA_VEIL] -= 1
            # Safeguard
            if self.state.side_conditions[side, SC_SAFEGUARD] > 0:
                self.state.side_conditions[side, SC_SAFEGUARD] -= 1
            # Mist
            if self.state.side_conditions[side, SC_MIST] > 0:
                self.state.side_conditions[side, SC_MIST] -= 1
            # Tailwind
            if self.state.side_conditions[side, SC_TAILWIND] > 0:
                self.state.side_conditions[side, SC_TAILWIND] -= 1


# =============================================================================
# Convenience Constants for P_VOL_TELEKINESIS
# =============================================================================

P_VOL_TELEKINESIS = 86  # Re-export for clarity
