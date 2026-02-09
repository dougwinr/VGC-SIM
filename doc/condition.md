## 1. What is a “condition” in Pokémon battles?

In battle terms, a **condition** is any persistent state that changes how a Pokémon, a side (team), or the whole field behaves over time.

Conditions can:

- Modify stats (Attack, Speed, etc.)
- Cause damage over time
- Block or force certain moves
- Change targeting or priority
- Change type matchups or move power
- Change turn order
- Interact with **items**, **abilities**, **moves**, and battle mechanics (Mega, Dynamax, Z-Moves, Terastallization)

Conceptually, they are:

- **Attached to a scope**: Pokémon, side (team), or field
- **Have a duration** (turn-based, until switch-out, or permanent)
- **Are created and removed** by moves, abilities, items, or scripts

You can think of them as “buffs/debuffs/effects” in other RPGs, but more structured.

---

## 2. Major categories of conditions

### 2.1. Primary (non-volatile) status conditions

These are the classic ones shown on the status bar and persist when switching (but not outside battle in this explanation).

Common ones (names for reference):

- **POISON** (regular)
- **BADLY POISONED** (toxic)
- **BURN**
- **PARALYSIS**
- **SLEEP**
- **FREEZE**
- **FAINTED** (terminal condition, basically “not usable” in battle)

**Key characteristics:**

- Only **one primary status** at a time (per Pokémon).
- Persist when you switch out (within that battle).
- Many moves and abilities care specifically about these (e.g., “if target is burned…”).
- Cured by:
  - Some moves (heals, “aromatherapy”-style)
  - Some abilities at turn end or upon switch
  - Some held items
  - Switching out in a few special cases (e.g. some temporary-like statuses in special formats).

**Effects overview (simplified):**

- **Poison**: Lose fixed fraction of max HP each turn.
- **Badly Poisoned**: Damage over time increases each turn the Pokémon remains active.
- **Burn**: Lose HP each turn and Physical damage output is reduced (mostly physical Attack).
- **Paralysis**: Speed heavily reduced + chance to be unable to act each turn.
- **Sleep**: Can't act except with specific moves; lasts several turns; some moves wake you up.
- **Freeze**: Usually prevents acting, with a chance to thaw each turn or by certain moves/damage types.

**Interactions with other systems:**

- **Types**:
  - Poison-type and Steel-type Pokémon usually cannot be poisoned by standard means.
  - Ice-types have special interactions with freeze in some generations (hard or impossible to freeze).
- **Abilities**:
  - Some “prevent” specific statuses (e.g., immunity to sleep/paralysis/burn/poison).
  - Some “benefit” from being statused (e.g., increased Attack, Defense, or Speed).
- **Items**:
  - Status orbs that deliberately inflict burn/poison to trigger “Guts-like” abilities.
  - Berries and healing items that cure specific or any status.
- **Moves**:
  - Some moves fail or have enhanced power if target is already statused.
  - Some moves become more powerful if the user is statused.

In a model, this is usually a **single attribute per Pokémon**, e.g.:

```python
pokemon.primary_status  # None or StatusCondition instance
```

---

### 2.2. Volatile status conditions (on Pokémon)

These are temporary “sub-statuses” that go away when you switch out or after a certain number of turns. They usually are NOT shown as the main battle “status icon” and you can have **several at once**.

Common volatile conditions include (not exhaustive):

- **Confusion**: Chance to hurt self instead of acting for a few turns.
- **Flinch**: A one-turn condition that prevents action if applied before you move.
- **Attract**: Chance not to act against certain foes.
- **Leech Seed**: Target loses HP each turn; user recovers.
- **Nightmare / Curse (on target)**: Extra HP loss each turn under certain circumstances.
- **Taunt**: Target can only use damaging moves.
- **Torment**: Target cannot use the same move twice in a row.
- **Disable**: A specific move is unusable for a few turns.
- **Encore**: Target is forced to repeat its last move for several turns.
- **Perish Song counter**: After a set number of turns, the Pokémon faints.
- **Trapped / Partially Trapped**: Cannot switch and may take damage over time.
- **Aqua Ring / Ingrain**: Heals a bit each turn, but may also prevent switching (Ingrain).
- **Substitute**: Surrogate HP barrier that absorbs damage and some statuses.
- **Focus Energy**: Raises critical hit ratio.
- **Transform**: User copies stats/moves/species of target.
- **Magnet Rise / Telekinesis**: Temporary immunity changes (e.g., to Ground).

**Key traits:**

- Stored per Pokémon, typically in a **collection** (list/dict/set).
- Each has its own **duration**, counters, and logic.
- Removed when:
  - Their duration ends.
  - The Pokémon switches out.
  - Explicitly removed by moves (e.g., Haze-like effects).
  - Overridden by something else (e.g., per-turn replacement).

**Single vs Double Battles:**

- Effects are the same, but:
  - Redirection abilities (e.g., Follow Me / Rage Powder) only matter in multi-battles.
  - Some volatile effects can target multiple Pokémon (e.g., Perish Song).
  - “Trapped” logic has to account for double/multi sides.

---

### 2.3. Stat stage changes

Not always called “conditions,” but they behave like them and should be modeled similarly.

Each Pokémon has **stat stages** ranging from typically -6 to +6 for:

- Attack, Defense, Sp. Atk, Sp. Def, Speed
- Accuracy, Evasion

These stages are:

- Changed by **moves**, **abilities**, **items**.
- Affected by certain abilities (e.g., invert stat changes, prevent reductions).
- Reset on switch-out or by certain global moves (e.g., Haze-like).

They’re not “status conditions” in the UI, but from a design standpoint they are **persistent modifiers** with:

- Attribute: current stage value.
- Cap: min/max.
- Hooks: used in damage/accuracy calculations.

---

### 2.4. Field-wide conditions (global)

These affect **everyone** on the field.

#### 2.4.1. Weather

Common weather effects:

- **Harsh Sunlight**
- **Rain**
- **Sandstorm**
- **Hail / Snow**
- Stronger “permanent” variants from certain abilities (though now often limited in duration).

Weather can affect:

- Power of certain types (e.g., Fire/Water).
- Recovery moves’ effectiveness.
- Hit chance of certain moves.
- HP chip damage for non-immune types.
- Certain abilities (healing, stat boosts, immunity).

Duration:

- Usually a fixed number of turns (e.g., 5, 8 with an item).
- May be infinite under special mechanics in some generations.

Weather is shared in:

- **Singles**: 2 Pokémon; both affected.
- **Doubles**: 4 Pokémon; all affected the same.

#### 2.4.2. Terrain

- **Electric Terrain**
- **Grassy Terrain**
- **Misty Terrain**
- **Psychic Terrain**

Terrains affect:

- Power of moves of certain types used by grounded Pokémon.
- Status immunity (e.g., no sleep on grounded Pokémon).
- Priority interactions (e.g., block priority moves for grounded targets).
- Recovery over time or move-specific effects.

Duration: fixed number of turns.

Only grounded Pokémon are affected; Flying-type or Levitate may not be.

#### 2.4.3. “Rooms” and other field effects

Examples:

- **Trick Room**: Inverts move order: slower Pokémon act first.
- **Magic Room**: Negates or alters held items.
- **Wonder Room**: Swaps Defense and Sp. Defense.
- **Gravity**: Lowers evasion, grounds Flying/Levitate Pokémon, some moves cannot be used.
- Legacy effects such as Mud Sport/Water Sport, Ion Deluge, etc.

All of these:

- Affect all Pokémon on the field.
- Have a fixed duration.
- May alter move legality, accuracy, or damage.

---

### 2.5. Side conditions (team-side)

These affect **one side** (one trainer’s field) rather than a single Pokémon.

Common examples:

- **Reflect**: Reduces physical damage to that side.
- **Light Screen**: Reduces special damage.
- **Aurora Veil**: Reduces both physical and special damage under certain weather.
- **Safeguard**: Protects team from status conditions.
- **Mist**: Prevents stat reduction.
- **Tailwind**: Doubles Speed of that side’s active Pokémon.
- **Entry Hazards**:
  - Stealth Rock: Damage on switch-in scaled by target’s typing.
  - Spikes: Damage on switch-in for grounded targets.
  - Toxic Spikes: Inflict poison on grounded switch-ins.
  - Sticky Web: Lowers Speed on grounded switch-in.

Also:

- **Wish** / **Future Sight / Doom Desire**: “Delayed” side-bound effects.

**Single vs Double Battles:**

- Same side has one instance of each (e.g., one Reflect applies to both active Pokémon).
- Entry hazards apply when any Pokémon switches into that side, regardless of format.

---

### 2.6. Very short-lived / single-turn conditions

Examples:

- **Protect / Detect / Max Guard**: Blocking moves for one turn, with stacking failure chance.
- **Charge**: Doubles next Electric move and reduces damage of an incoming move type.
- **Helping Hand**: Buffs ally’s move this turn.
- **Follow Me / Rage Powder**: Redirect attacks to the user (doubles).
- **Wide Guard / Quick Guard / Crafty Shield**: Protects side from certain categories of moves.

These are usually:

- Removed at end of the current turn.
- Modeled as volatile conditions with **duration = 1** or as flags set for the turn.

---

## 3. Interactions with abilities, items, and mechanics

### 3.1. Abilities

Abilities can:

- **Prevent** conditions: e.g., immunity to burn/poison/sleep.
- **Modify** their behavior: e.g., double duration, no HP loss, invert positive/negative stat stages.
- **Trigger** on condition events: e.g., “on status applied, heal”; “on weather active, boost Speed.”
- **Alter targeting and priority**: e.g., redirection abilities, priority modifiers.

Your condition system needs ability hooks like:

- `on_condition_apply`
- `on_condition_check`
- `on_damage_calc`
- `on_turn_start` / `on_turn_end`

So abilities can override or modify condition logic.

### 3.2. Items

Items can:

- Automatically cure conditions at certain triggers (hit by attack, low HP, end of turn).
- Extend durations (weather, terrain, screens).
- Create conditions when held (orbs that self-inflict status, items creating weather on entry).
- Tie you to a move (choice items behave like a “move-lock condition”).

Model-wise, you often treat these as:

- Item object with hooks similar to abilities.
- Some items **create a Condition object** (e.g., “ChoiceLockCondition”).

### 3.3. Major mechanics

- **Mega Evolution**:
  - Abilities and stats change; conditions remain but some interactions may change (new ability may now prevent a status or remove it).
- **Dynamax / Gigantamax**:
  - HP is multiplied; existing conditions’ damage over time must use base max HP or new max HP depending on rule choice.
  - Protect-like effects become weaker against Max Moves.
  - Certain conditions cannot be applied or are modified (e.g., flinch, some status/weight-based moves).
- **Z-Moves**:
  - Typically are single powerful moves; they interact with conditions mainly as powerful break points (e.g., breaking through Protect for chip damage).
- **Terastallization**:
  - Changes type for type-based immunities (e.g., immune to certain status moves or hazards).
  - Conditions relying on type (hazards, weather boosts) need to re-check type.

This means your condition system must not hard-code type/ability behavior; instead, it should **query current Pokémon state** (types, ability, items, form) at runtime.

---

## 4. Modeling conditions in Python (object-oriented)

Below is one way to model a flexible, extensible condition system.

### 4.1. High-level architecture

Core classes (simplified):

- `Battle`: owns all battle state.
- `Field`: owns field-wide conditions (weather, terrain, rooms).
- `Side`: one per player/team; owns side conditions (screens, hazards).
- `Pokemon`: owns:
  - stats & stat stages
  - primary status
  - volatile conditions
  - ability, item, types, etc.
- `Move`: executes actions.
- `Ability`, `Item`: encapsulate their effects/hooks.
- **`Condition`**: base class for all conditions.

The **Condition** class provides:

- Identity: `id`, `name`
- Scope: `pokemon`, `side`, `field`
- Duration: `turns_left`, `max_turns`
- Source: `source_pokemon`, `source_move`, `source_item`, `source_ability`
- Hooks for lifecycle:
  - `on_apply`
  - `on_remove`
  - `on_turn_start`
  - `on_turn_end`
  - `on_before_move`
  - `on_after_move`
  - `on_damage_calc`
  - `on_switch_in`
  - `on_switch_out`
  - etc.

### 4.2. Base enums and interfaces

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any, Dict, List, Protocol


class ConditionScope(Enum):
    POKEMON = auto()
    SIDE = auto()
    FIELD = auto()


class ConditionCategory(Enum):
    PRIMARY_STATUS = auto()
    VOLATILE_STATUS = auto()
    STAT_STAGE = auto()
    WEATHER = auto()
    TERRAIN = auto()
    ROOM = auto()
    SIDE_CONDITION = auto()
    HAZARD = auto()
    TEMPORARY_TURN = auto()
    OTHER = auto()


class BattleHooks(Protocol):
    def log(self, message: str) -> None: ...
    # Additional interfaces to interact with battle state (damage, switch, etc.)


@dataclass
class ConditionContext:
    """Information passed to conditions when their hooks are called."""
    battle: BattleHooks
    holder: Any       # The object this condition is attached to (Pokemon, Side, Field)
    target: Optional[Any] = None
    move: Optional[Any] = None
    source: Optional[Any] = None
    # You can add more: damage, hit_result, etc.
```

### 4.3. Base `Condition` class

```python
@dataclass
class Condition:
    id: str
    name: str
    scope: ConditionScope
    category: ConditionCategory
    max_turns: Optional[int] = None    # None = infinite or until removed manually
    turns_left: Optional[int] = None   # Set on apply
    volatile: bool = True              # True = removed on switch (for pokemon-scope)
    stackable: bool = False            # If multiple copies allowed
    data: Dict[str, Any] = field(default_factory=dict)

    # LIFECYCLE ---------------------------------------------------------------

    def initialize(self) -> None:
        """Called right after creation, before on_apply."""
        if self.max_turns is not None and self.turns_left is None:
            self.turns_left = self.max_turns

    def on_apply(self, ctx: ConditionContext) -> None:
        """Called when the condition is first applied."""
        ctx.battle.log(f"{self.name} applied to {ctx.holder}.")

    def on_remove(self, ctx: ConditionContext) -> None:
        """Called when the condition is removed."""
        ctx.battle.log(f"{self.name} ended on {ctx.holder}.")

    def on_turn_start(self, ctx: ConditionContext) -> None:
        """Called at the start of each turn."""
        pass

    def on_turn_end(self, ctx: ConditionContext) -> None:
        """Called at the end of each turn."""
        # Default duration handling:
        if self.turns_left is not None:
            self.turns_left -= 1
            if self.turns_left <= 0:
                ctx.battle.log(f"{self.name} naturally expired on {ctx.holder}.")
                ctx.holder.remove_condition(self.id)

    def on_before_move(self, ctx: ConditionContext) -> None:
        """Called before move selection is finalized."""
        pass

    def on_attempt_move(self, ctx: ConditionContext) -> bool:
        """
        Called right before executing a move.
        Return False to prevent the move (e.g., paralysis, flinch).
        """
        return True

    def on_damage_calc(self, ctx: ConditionContext, damage: int) -> int:
        """Allow the condition to modify damage."""
        return damage

    def on_switch_in(self, ctx: ConditionContext) -> None:
        pass

    def on_switch_out(self, ctx: ConditionContext) -> None:
        pass
```

You would subclass `Condition` to implement each specific effect.

### 4.4. Example: Burn as a primary status condition

```python
class BurnCondition(Condition):
    def __init__(self):
        super().__init__(
            id="burn",
            name="Burn",
            scope=ConditionScope.POKEMON,
            category=ConditionCategory.PRIMARY_STATUS,
            max_turns=None,
            volatile=False,
            stackable=False,
        )
        self.initialize()

    def on_turn_end(self, ctx: ConditionContext) -> None:
        # HP loss
        pokemon = ctx.holder
        max_hp = pokemon.stats["hp"]
        damage = max(1, max_hp // 16)
        ctx.battle.log(f"{pokemon} is hurt by its burn!")
        pokemon.apply_damage(damage, ctx)

        # Then call base to handle duration (none for burn)
        super().on_turn_end(ctx)

    def on_damage_calc(self, ctx: ConditionContext, damage: int) -> int:
        # Reduce physical damage unless special abilities override it
        pokemon = ctx.holder
        # Example ability check (Guts-like)
        if pokemon.ability and pokemon.ability.ignores_burn_attack_drop:
            return damage
        # Check move category from ctx.move
        if ctx.move and ctx.move.is_physical:
            return damage // 2
        return damage
```

Here:

- The burn condition is **non-volatile** and has **no fixed duration**.
- It applies **chip damage** at end of turn.
- It reduces physical damage dealt by the burned Pokémon, unless an ability overrides it.

### 4.5. Example: Reflect as a side condition

```python
class ReflectCondition(Condition):
    def __init__(self, duration: int):
        super().__init__(
            id="reflect",
            name="Reflect",
            scope=ConditionScope.SIDE,
            category=ConditionCategory.SIDE_CONDITION,
            max_turns=duration,
            volatile=False,
            stackable=False,
        )
        self.initialize()

    def on_damage_calc(self, ctx: ConditionContext, damage: int) -> int:
        # Applies only if target is on this side, damage is physical, etc.
        side = ctx.holder  # The side that has Reflect
        move = ctx.move

        if not move or not move.is_physical:
            return damage

        # Example: if target belongs to this side
        if ctx.target and ctx.target.side is side:
            # Some abilities ignore screens, so check that:
            if ctx.target.ability and ctx.target.ability.ignores_screens:
                return damage
            # Double battles often use a different multiplier (e.g. 2/3 vs 1/2)
            if ctx.battle.is_double:
                return int(damage * 2 / 3)
            else:
                return damage // 2
        return damage
```

### 4.6. Example: Weather (Rain) as a field condition

```python
class RainCondition(Condition):
    def __init__(self, duration: int):
        super().__init__(
            id="rain",
            name="Rain",
            scope=ConditionScope.FIELD,
            category=ConditionCategory.WEATHER,
            max_turns=duration,
            volatile=False,
            stackable=False,
        )
        self.initialize()

    def on_apply(self, ctx: ConditionContext) -> None:
        ctx.battle.log("It started to rain!")

    def on_remove(self, ctx: ConditionContext) -> None:
        ctx.battle.log("The rain stopped.")

    def on_damage_calc(self, ctx: ConditionContext, damage: int) -> int:
        move = ctx.move
        if not move:
            return damage
        # Example type-based effect:
        if move.type == "Water":
            return int(damage * 1.5)
        if move.type == "Fire":
            return int(damage * 0.5)
        return damage
```

---

### 4.7. Integrating conditions into `Pokemon`, `Side`, and `Field`

#### Pokémon class (simplified)

```python
class Pokemon:
    def __init__(self, name: str):
        self.name = name
        self.primary_status: Optional[Condition] = None
        self.volatile_conditions: Dict[str, Condition] = {}
        self.stats = {"hp": 100}   # Simplified
        self.current_hp = 100
        self.ability = None
        self.item = None
        self.side: Optional["Side"] = None  # Assigned later
        # Stat stages, etc.

    def __str__(self):
        return self.name

    # CONDITION MANAGEMENT ---------------------------------------------------

    def set_primary_status(self, condition: Condition, ctx_base: ConditionContext) -> bool:
        if self.primary_status is not None:
            ctx_base.battle.log(f"{self} already has a primary status.")
            return False

        # Check immunities from type, ability, item here...
        # if immune: return False

        self.primary_status = condition
        ctx = ConditionContext(
            battle=ctx_base.battle,
            holder=self,
            source=ctx_base.source,
            move=ctx_base.move,
        )
        condition.on_apply(ctx)
        return True

    def add_volatile_condition(self, condition: Condition, ctx_base: ConditionContext) -> bool:
        if not condition.stackable and condition.id in self.volatile_conditions:
            ctx_base.battle.log(f"{self} already has {condition.name}.")
            return False

        self.volatile_conditions[condition.id] = condition
        ctx = ConditionContext(
            battle=ctx_base.battle,
            holder=self,
            source=ctx_base.source,
            move=ctx_base.move,
        )
        condition.on_apply(ctx)
        return True

    def remove_condition(self, condition_id: str) -> None:
        if self.primary_status and self.primary_status.id == condition_id:
            cond = self.primary_status
            self.primary_status = None
        else:
            cond = self.volatile_conditions.pop(condition_id, None)

        if cond:
            # In a real engine you would have a battle reference here
            # to create a ConditionContext; omitted for brevity.
            pass

    def apply_damage(self, amount: int, ctx: ConditionContext) -> None:
        self.current_hp = max(0, self.current_hp - amount)
        ctx.battle.log(f"{self} took {amount} damage (HP: {self.current_hp}).")
        if self.current_hp == 0:
            # Fainting could itself be represented as a condition or a flag
            ctx.battle.log(f"{self} fainted!")

    # TURN HOOKS -------------------------------------------------------------

    def on_turn_start(self, ctx: ConditionContext) -> None:
        if self.primary_status:
            self.primary_status.on_turn_start(ctx)
        for cond in list(self.volatile_conditions.values()):
            cond.on_turn_start(ctx)

    def on_turn_end(self, ctx: ConditionContext) -> None:
        if self.primary_status:
            self.primary_status.on_turn_end(ctx)
        for cond in list(self.volatile_conditions.values()):
            cond.on_turn_end(ctx)

    def modify_damage(self, ctx: ConditionContext, damage: int) -> int:
        # Apply conditions from self (attacker or defender, depending on ctx)
        if self.primary_status:
            damage = self.primary_status.on_damage_calc(ctx, damage)
        for cond in self.volatile_conditions.values():
            damage = cond.on_damage_calc(ctx, damage)
        return damage
```

#### Side class (simplified)

```python
class Side:
    def __init__(self, name: str):
        self.name = name
        self.conditions: Dict[str, Condition] = {}

    def add_condition(self, condition: Condition, battle: BattleHooks, source: Any = None):
        if not condition.stackable and condition.id in self.conditions:
            battle.log(f"{self.name} already has {condition.name}.")
            return False
        self.conditions[condition.id] = condition
        ctx = ConditionContext(battle=battle, holder=self, source=source)
        condition.on_apply(ctx)
        return True

    def remove_condition(self, condition_id: str, battle: BattleHooks):
        cond = self.conditions.pop(condition_id, None)
        if cond:
            ctx = ConditionContext(battle=battle, holder=self)
            cond.on_remove(ctx)
```

#### Field class (simplified)

```python
class Field:
    def __init__(self):
        self.conditions: Dict[str, Condition] = {}

    def set_condition(self, condition: Condition, battle: BattleHooks, source: Any = None):
        # Only one weather/terrain/room of each type, usually:
        self.conditions[condition.id] = condition
        ctx = ConditionContext(battle=battle, holder=self, source=source)
        condition.on_apply(ctx)
        return True

    def remove_condition(self, condition_id: str, battle: BattleHooks):
        cond = self.conditions.pop(condition_id, None)
        if cond:
            ctx = ConditionContext(battle=battle, holder=self)
            cond.on_remove(ctx)
```

### 4.8. Applying conditions in a turn

In a battle loop, end of turn might look like:

```python
def end_of_turn(battle: BattleHooks, field: Field, sides: List[Side], pokemons: List[Pokemon]):
    # Field conditions
    for cond in list(field.conditions.values()):
        ctx = ConditionContext(battle=battle, holder=field)
        cond.on_turn_end(ctx)

    # Side conditions
    for side in sides:
        for cond in list(side.conditions.values()):
            ctx = ConditionContext(battle=battle, holder=side)
            cond.on_turn_end(ctx)

    # Pokemon conditions
    for p in pokemons:
        ctx = ConditionContext(battle=battle, holder=p)
        p.on_turn_end(ctx)
```

---

## 5. Modeling singles vs doubles

Your **Battle** class should know whether the format is single or double:

```python
class Battle(BattleHooks):
    def __init__(self, is_double: bool = False):
        self.is_double = is_double
        # teams, field, etc.

    def log(self, message: str) -> None:
        print(message)
```

Conditions then:

- Read `ctx.battle.is_double` to apply different multipliers (e.g., Reflect, spread-move damage).
- For redirect effects (Follow Me, Rage Powder), you can have a **turn-only condition** on a Pokémon that changes target selection if `is_double` is True.
- Hazards and screens automatically affect both allies in doubles because they are attached to `Side`.

---

## 6. Summary

- “Conditions” in Pokémon include:
  - Primary statuses
  - Volatile statuses
  - Stat stages
  - Field conditions (weather, terrain, rooms)
  - Side conditions (screens, hazards, support)
  - Short-lived turn conditions (Protect, follow-me-like behavior)
- They interact with **abilities**, **items**, **moves**, and **mechanics** (Mega, Dynamax, Z, Tera) by:
  - Changing damage, accuracy, targeting, turn order, and state transitions.
- A robust Python OOP model:
  - Uses a generic `Condition` base class with:
    - Scope, category, duration
    - Lifecycle hooks (`on_apply`, `on_remove`, `on_turn_start`, `on_turn_end`, `on_attempt_move`, `on_damage_calc`, etc.)
  - Attaches conditions to `Pokemon`, `Side`, and `Field`.
  - Lets abilities and items interact via similar hooks.

If you’d like, I can next:

- Expand with a more complete set of concrete condition subclasses (poison, paralysis, sleep, hazards, Trick Room).
- Or show a minimal “playable skeleton” battle loop that demonstrates a full turn with statuses, weather, and screens applied.