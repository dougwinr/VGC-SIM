## 1. What is a Pokémon “move”?

A **move** is an action that a Pokémon can perform in battle. Every time you select *Fight* and pick an option, you’re choosing a move.

A move is defined by:

- What **it tries to do** (deal damage, inflict status, boost stats, change field, etc.)
- **How** it does that (type, category, priority, target, flags)
- **When** it fails or behaves differently (immunities, abilities, items, weather, terrain, etc.)
- **How often** you can use it (PP)

Moves are the core “verbs” of the battle system. Almost every other mechanic (abilities, items, special forms) is either:
- modifying a move, or  
- reacting to a move.

---

## 2. What is a “learnset”?

A **learnset** is the set of all moves a given Pokémon species (or form) is able to learn, and **how** it learns each one.

A Pokémon can usually learn moves via:

1. **Level-up**  
   - For each level, there may be 0–several moves it can learn.
   - If its move slots are full (usually 4), you must replace one.

2. **Machines / Records / Discs (TMs, TRs, etc.)**  
   - Items that permanently or semi-permanently teach specific moves.
   - Compatibility depends on species and, sometimes, form or region.

3. **Move Tutors**  
   - NPCs that teach specific moves to compatible species under some conditions.

4. **Egg Moves (breeding)**  
   - Moves inherited from parents or specially distributed.
   - Often moves the Pokémon could not normally learn by level-up or TM.

5. **Event / Special distribution moves**  
   - Exclusive moves granted by events, promotions, or in-game gifts.

6. **Move Reminder (Relearner)**  
   - Re-teach past level-up moves the Pokémon could know at or below its current level.

A **full learnset record** needs:
- species/form
- move
- learn method (level-up, TM, Egg, tutor, event)
- any conditions (level, game version, parent species, etc.)

---

## 3. Core attributes of a move

At minimum, a move has:

1. **Name**
2. **Type**: one of the 18 Pokémon types (Fire, Water, etc.)
3. **Category / Damage class**
   - *Physical* – uses Attack vs Defense.
   - *Special* – uses Special Attack vs Special Defense.
   - *Status* – usually does no direct HP damage; alters stats, status, field, etc.

4. **Base Power**
   - Numeric strength (0 or variable for some moves).
   - 0 often means “no direct damage” or “damage determined by other formulas”.

5. **Accuracy**
   - A percentage or “always hits” (or special rules).
   - Interacts with accuracy/evasion stat changes and various modifiers.

6. **PP**
   - How many times you can use the move before it runs out.
   - Items and abilities can restore or modify PP usage.

7. **Priority**
   - Determines order compared to other moves on the same turn, after considering Speed.
   - Positive priority moves often go first; negative usually go last.

8. **Targeting**
   - In singles: self / opponent.
   - In doubles: self, ally, one opponent, both opponents, everyone, etc.
   - Some moves choose a side or the whole field.

9. **Contact flag**
   - Whether using the move counts as “making contact”.
   - Triggers abilities like Rough Skin, Iron Barbs, items like Rocky Helmet, etc.

10. **Other flags/tags**
    Typical tags used by games & tools:
    - Sound moves
    - Punching moves
    - Biting moves
    - Wind moves
    - Dance moves
    - Projectile / ballistic moves
    - Slicing moves
    - Affected by Protect
    - Defrosts user
    - Hits in the air/dig/dive/etc.
    - High critical-hit rate
    - Multi-hit
    - Two-turn (charge + hit)
    - Forces recharge, etc.

These flags are important because **abilities, items, and other moves** often refer to these categories (e.g., “boost punching moves”, “copy dance moves”, “immune to sound moves”).

---

## 4. Effects and side effects of moves

Moves can have complex effects; often they are composed from building blocks:

### 4.1 Primary effects

- **Damage**
  - Standard damage (with the usual formula).
  - Fixed damage (e.g., based only on level or a constant).
  - OHKO moves (KO if they connect).
  - Damage based on target’s HP, user’s HP, weight, speed, stats, etc.

- **Healing**
  - Recover a portion of max HP (often 50%, sometimes modified by weather, etc.).
  - Drain moves (heal user for a fraction of damage dealt).

- **Stat changes**
  - Raise or lower stats (Atk, Def, SpA, SpD, Spe, Accuracy, Evasion).
  - Affect user, target, or all on one side / field.
  - Sometimes conditional (e.g., raise stats if KO was achieved).

- **Status conditions**
  - Inflict major status (Burn, Poison, Paralysis, Sleep, Freeze).
  - Inflict volatile status (Confusion, Flinch, attraction, trapping, etc.)
  - These can be chance-based (e.g., 10% to burn) or guaranteed.

- **Field and side conditions**
  - Weather (Rain, Sun, Sandstorm, Hail/Snow).
  - Terrain (Electric, Grassy, Misty, Psychic).
  - Rooms (Trick Room, Wonder Room, Magic Room).
  - Screens (Reflect, Light Screen, Aurora Veil).
  - Entry hazards (Spikes, Stealth Rock, Toxic Spikes, Sticky Web).
  - Other side effects (Tailwind, Safeguard, Wish, etc.).

- **Switching and phasing**
  - Force target to switch out.
  - Force user to switch out after attacking (pivoting).
  - U-turn/Volt Switch-like moves.

- **Binding / trapping**
  - Prevent switching and cause residual damage.
  - Volatile conditions that last several turns.

- **Move-lock effects**
  - User must repeat the move for several turns, then maybe becomes confused.
  - Requires recharge after use.

- **Form / mode changing**
  - Some moves cause the user to change form mid-battle.

### 4.2 Secondary effects

Many damaging moves have chance-based “secondary effects”:
- e.g., 30% to flinch, 10% to paralyze, 50% to raise the user’s stat.

These interact with:
- abilities (boost chance, block them, or trigger on them),
- items (e.g., increased flinch chance),
- dynamic move lists (e.g., copying last move).

---

## 5. Damage calculation (high-level)

In simplified form, a damaging move’s base damage is roughly:

1. Compute a **base damage** from:
   - user’s level
   - base power
   - user Attack (or Sp. Atk) and target Defense (or Sp. Def)

2. Apply multiplicative modifiers:
   - **STAB** (Same-Type Attack Bonus) – usually ×1.5 (or more with certain abilities).
   - **Type effectiveness** – 0, 0.25, 0.5, 1, 2, or 4× vs target’s type(s).
   - **Critical hit** – multiplier if crit occurs.
   - **Weather & terrain** – may boost or weaken certain types.
   - **Items & abilities** – e.g., Choice items, Life Orb, Thick Fat, etc.
   - **Other field modifiers** (Reflect, Light Screen, etc.).
   - **Random factor** – usually a small randomized multiplier.

Moves that don’t use this formula have custom rules (e.g., fixed damage, OHKO, etc.).

---

## 6. Singles vs Doubles (and multi battles)

Mechanically, moves often differ in doubles / multi battles:

1. **Targeting**
   - Moves can target:
     - 1 ally,
     - 1 opponent,
     - all allies,
     - both opponents,
     - all other Pokémon,
     - or the entire field/side.
   - Some moves that target “both opponents” become single-target in singles.

2. **Spread damage modifier**
   - In doubles, moves that hit multiple targets have reduced damage to balance them (e.g., ~75% of original).

3. **Redirection and support**
   - Follow Me / Rage Powder redirect single-target moves.
   - Abilities like Lightning Rod, Storm Drain redirect certain types.
   - Helping Hand boosts ally moves.
   - Wide Guard/Quick Guard protect allies from certain categories of moves.

4. **Turn order complications**
   - Priority + speed (plus Trick Room, etc.) determine move order.
   - Moves that depend on “last move used” or “ally’s move” behave differently.

Some moves have explicitly **different text or behavior** in multi battles (e.g., some only activate if there’s an ally, some “hit all other Pokémon”).

---

## 7. Interactions with other systems

### 7.1 Moves & Pokémon

Moves depend on the Pokémon’s:

- **Stats** (for damage, accuracy/evasion, speed).
- **Types** (for STAB, weaknesses, immunities).
- **Form** (different forms may learn different moves or alter move power/type).
- **Weight / Height / Gender / Level** for certain move formulas.
- **Status conditions**: some moves fail or change power if the user/target is statused.

Example patterns:
- Moves that scale with **user’s HP** (stronger when healthier or weaker).
- Moves that scale with **target’s weight**.
- Moves that work only if user or target meets certain criteria (e.g., asleep, low HP, opposite gender, etc.).

### 7.2 Moves & abilities

Abilities often:

- Modify **power** or **type** of moves (e.g., “boost Fire moves”, “change type of Normal moves”).
- Modify **priority** (e.g., +1 for status moves of a certain type).
- Modify **accuracy** or allow hits through immunities.
- Prevent or reflect status / stat lowering / entry hazards.
- Change move behavior (e.g., turn resisted hits into immunity and get a boost).

Common patterns:
- **Immunities**: abilities that grant immunity to certain types or statuses.
- **Copying / blocking**: copy an opponent’s stat changes or block them.
- **On-contact**: trigger when a contacting move hits (damage back, status, ability swap).
- **Weather / terrain**: abilities that create or benefit from field states.

Moves must check abilities:
- before damage (immunity / blocking),
- during damage (modifiers),
- after damage (reactive triggers).

### 7.3 Moves & items

Items can:

- Modify move power (Life Orb, Choice items, type-boosting items).
- Modify priority (some items give pseudo +1 to specific moves).
- Modify accuracy or critical rate.
- Limit choice (Choice Band/Specs lock into first move used).
- Consume to boost a specific move once (e.g., certain gems, berries).
- Trigger on being hit (e.g., damage recoil on contact).
- Enable special mechanics (Mega Stones, Z-Crystals, etc.).

A move’s execution pipeline must consider item effects at all phases:
- can it be selected?
- does its power change?
- does its type change?
- does the item get consumed?
- do post-move item effects trigger?

### 7.4 Moves & field states (weather, terrain, rooms, hazards)

Moves:

- **Set** field states (weather, terrains, screens, hazards, rooms).
- **Depend on** them (boosted/reduced power, special effects only in certain conditions).
- **Interact with** them (removing hazards, negating effects).

Examples:
- Weather boosting Fire or Water moves, or altering healing.
- Terrain preventing certain statuses, boosting grounded moves.
- Trick Room inverting speed order.
- Screens reducing damage for the team.

### 7.5 Special generational mechanics

#### 7.5.1 Mega Evolution

- A Pokémon holding a **Mega Stone** can Mega Evolve once per battle.
- Mega form often changes:
  - stats,
  - ability,
  - sometimes type.
- This affects:
  - STAB,
  - how moves are modified by abilities,
  - speed order (depending on generation’s calculation timing),
  - ability interactions (e.g., newly gained ability now affects moves).

The moves themselves are the same; the **user’s data changes** mid-battle.

#### 7.5.2 Z-Moves

- Once per battle, a Pokémon holding a compatible **Z-Crystal** can turn one move into a **Z-Move**.
- Z-Moves:
  - have boosted base power, based on the original move’s power.
  - keep the same type (for generic Z-Moves).
  - may have **unique animations** for specific species/moves.
- **Z-Status moves**:
  - keep their original effect,
  - plus add a guaranteed stat boost or other bonus.

Key modeling points:
- Z-move choice is a wrapper around an existing move.
- The move’s **type, power, secondary effects** may change when used as a Z-Move.
- One-use-per-battle constraint.

#### 7.5.3 Dynamax / Gigantamax

- When Dynamaxed:
  - Pokémon’s HP is multiplied.
  - All damaging moves turn into **Max Moves** with:
    - standardized base powers by original move power,
    - fixed secondary effects (e.g., setting weather, terrain, screens).
  - Some status moves become **Max Guard** (a Protect-like move).
- Gigantamax has special forms with custom Max Moves.

Modeling notes:
- Dynamax moves are dynamic **transformations** of normal moves.
- Original move category/type primarily decides which Max Move type and base power.
- Additional rules: cannot be flinched, certain moves fail, etc.

#### 7.5.4 Terastallization

- A Pokémon can change its type to its **Tera Type** once per battle.
- STAB now applies to that new type (often stronger).
- Some moves (like a certain special move) change type or power when Terastallized.
- **Tera Blast** changes type to match Tera Type and uses the higher of Atk/SpA.

Modeling:
- Moves must re-check:
  - user’s current type(s) for STAB,
  - type interactions for Tera-specific behavior.
- Some moves override their type when Tera is active.

---

## 8. How to model moves in object-oriented Python

### 8.1 Design principles

Because moves have tons of exceptions and interactions:

1. **Separate data from behavior**
   - The Move object should carry static data (name, type, base power, flags).
   - Behavior (damage calculation, effect application) should be factored into reusable components or methods that can be overridden/plugged in.

2. **Use enums & small helper classes**
   - Types, categories, targets, status, etc., should be enums.
   - Complex effects should be represented by structured data (e.g., `SecondaryEffect`, `StatChange`).

3. **Use a BattleContext**
   - A separate object representing the whole battle state (weather, terrain, turn, etc.).
   - The move methods receive the context to know how to behave.

4. **Avoid giant “if move.name == ...” chains**
   - Instead, assign a per-move “behavior” object or function for special cases.
   - Generic moves can use a default behavior.

5. **Plan for generation-specific variations**
   - You may either:
     - fix your model to one generation, or  
     - add generation flags and versioned behavior.

Below is a **simplified but extensible** model in Python. It’s not fully implementing the entire mechanics (that would need hundreds of pages), but it shows how to structure a robust OOP model.

---

## 9. Example Python OOP model for moves

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List, Optional, Dict, Any, Protocol


# --- Basic Enums -------------------------------------------------------------

class MoveCategory(Enum):
    PHYSICAL = auto()
    SPECIAL = auto()
    STATUS = auto()


class MoveTarget(Enum):
    SELF = auto()
    SINGLE_OPPONENT = auto()
    ALL_OPPONENTS = auto()
    ALL_ALLIES = auto()
    ALL_OTHERS = auto()       # all except user
    FIELD = auto()            # affects entire field
    SIDE = auto()             # user side or opponent side
    RANDOM_OPPONENT = auto()
    USER_AND_ALLIES = auto()


class Type(Enum):
    NORMAL = auto()
    FIRE = auto()
    WATER = auto()
    GRASS = auto()
    ELECTRIC = auto()
    ICE = auto()
    FIGHTING = auto()
    POISON = auto()
    GROUND = auto()
    FLYING = auto()
    PSYCHIC = auto()
    BUG = auto()
    ROCK = auto()
    GHOST = auto()
    DRAGON = auto()
    DARK = auto()
    STEEL = auto()
    FAIRY = auto()


class StatusCondition(Enum):
    NONE = auto()
    BURN = auto()
    POISON = auto()
    BADLY_POISONED = auto()
    PARALYSIS = auto()
    SLEEP = auto()
    FREEZE = auto()


class Stat(Enum):
    ATTACK = auto()
    DEFENSE = auto()
    SP_ATTACK = auto()
    SP_DEFENSE = auto()
    SPEED = auto()
    ACCURACY = auto()
    EVASION = auto()


# --- Move flags --------------------------------------------------------------

@dataclass
class MoveFlags:
    makes_contact: bool = False
    sound: bool = False
    punch: bool = False
    bite: bool = False
    dance: bool = False
    ballistic: bool = False
    slicing: bool = False
    wind: bool = False
    affected_by_protect: bool = True
    high_crit: bool = False
    # Add more as needed (thaws_user, hits_minimize, etc.)


# --- Support data structures -------------------------------------------------

@dataclass
class StatChange:
    stat: Stat
    stages: int  # positive = raise, negative = lower
    target_self: bool = False  # True: affects user, False: affects target


@dataclass
class SecondaryEffect:
    """Chance-based extra effect when the move hits."""
    chance: float  # 0.0 - 1.0
    stat_changes: List[StatChange] = field(default_factory=list)
    status: Optional[StatusCondition] = None
    flinch: bool = False
    target_self: bool = False  # if status/stat changes are on user
    # You could add custom hooks/callbacks here


# --- Protocols for battle entities ------------------------------------------

class PokemonLike(Protocol):
    """Minimal interface a Move expects from a Pokémon object."""
    name: str
    level: int
    types: List[Type]
    ability: Any  # replace with your Ability class
    item: Any     # replace with your Item class
    stats: Dict[Stat, int]  # current effective stats
    status: StatusCondition

    def is_fainted(self) -> bool: ...
    def modify_stat_stages(self, changes: List[StatChange]) -> None: ...
    def apply_status(self, status: StatusCondition) -> None: ...
    def take_damage(self, amount: int, source_move: Move) -> None: ...
    def heal(self, amount: int) -> None: ...


class BattleContext(Protocol):
    """
    Represents the full battle state.
    Moves query this to know about weather, terrain, side conditions, etc.
    """
    weather: Any
    terrain: Any
    turn_number: int
    # ... add properties/methods for screens, hazards, etc.

    def get_effectiveness(self, move_type: Type, target: PokemonLike) -> float: ...
    def is_protected(self, user: PokemonLike, target: PokemonLike, move: Move) -> bool: ...
    def apply_field_effect(self, effect: Any, side: Optional[str] = None) -> None: ...
    # etc.


# --- Move behavior abstraction ----------------------------------------------

class MoveBehavior(Protocol):
    """
    Strategy object that encapsulates 'special' behavior of a move.
    Generic moves can use a DefaultDamageBehavior or DefaultStatusBehavior.
    """

    def can_execute(
        self,
        move: Move,
        user: PokemonLike,
        targets: List[PokemonLike],
        ctx: BattleContext
    ) -> bool:
        ...

    def execute(
        self,
        move: Move,
        user: PokemonLike,
        targets: List[PokemonLike],
        ctx: BattleContext
    ) -> None:
        ...


# --- Default behaviors ------------------------------------------------------

@dataclass
class DefaultDamageBehavior:
    """Standard damaging move behavior using the usual damage formula."""

    def can_execute(
        self,
        move: Move,
        user: PokemonLike,
        targets: List[PokemonLike],
        ctx: BattleContext
    ) -> bool:
        # Generic checks: PP, status like freeze/sleep, etc. could go here.
        return True

    def execute(
        self,
        move: Move,
        user: PokemonLike,
        targets: List[PokemonLike],
        ctx: BattleContext
    ) -> None:
        for target in targets:
            if target.is_fainted():
                continue

            if ctx.is_protected(user, target, move) and move.flags.affected_by_protect:
                # Move is blocked; in a real engine you'd handle partial hits, Feint, etc.
                continue

            base_damage = self._calculate_base_damage(move, user, target, ctx)
            final_damage = self._apply_modifiers(move, user, target, ctx, base_damage)

            target.take_damage(final_damage, move)

            # Apply secondary effects if the move successfully hit
            self._apply_secondary_effects(move, user, target, ctx)

    def _calculate_base_damage(
        self,
        move: Move,
        user: PokemonLike,
        target: PokemonLike,
        ctx: BattleContext
    ) -> int:
        # Highly simplified example; real games use a more complex formula.
        if move.category == MoveCategory.PHYSICAL:
            attack_stat = user.stats[Stat.ATTACK]
            defense_stat = target.stats[Stat.DEFENSE]
        elif move.category == MoveCategory.SPECIAL:
            attack_stat = user.stats[Stat.SP_ATTACK]
            defense_stat = target.stats[Stat.SP_DEFENSE]
        else:
            return 0

        level_factor = (2 * user.level / 5) + 2
        base = ((level_factor * move.base_power * attack_stat / defense_stat) / 50) + 2
        return max(1, int(base))  # at least 1 damage if it hits

    def _apply_modifiers(
        self,
        move: Move,
        user: PokemonLike,
        target: PokemonLike,
        ctx: BattleContext,
        base_damage: int
    ) -> int:
        # Type effectiveness
        effectiveness = ctx.get_effectiveness(move.type, target)

        # STAB
        stab = 1.5 if move.type in user.types else 1.0

        # Random factor (simplified as constant here)
        random_factor = 0.925

        # This is where you’d also apply abilities, items, weather, terrain, crits.
        modified = base_damage * effectiveness * stab * random_factor
        return max(1, int(modified))

    def _apply_secondary_effects(
        self,
        move: Move,
        user: PokemonLike,
        target: PokemonLike,
        ctx: BattleContext
    ) -> None:
        import random

        for sec in move.secondary_effects:
            if random.random() <= sec.chance:
                receiver = user if sec.target_self else target

                if sec.stat_changes:
                    receiver.modify_stat_stages(sec.stat_changes)

                if sec.status and receiver.status == StatusCondition.NONE:
                    receiver.apply_status(sec.status)

                if sec.flinch:
                    # You would mark the target as flinched for this turn.
                    pass


@dataclass
class DefaultStatusBehavior:
    """Non-damaging move: stat boosts, status, field effects, etc."""
    # Could be parametrized with what exactly this status move does.
    def can_execute(
        self,
        move: Move,
        user: PokemonLike,
        targets: List[PokemonLike],
        ctx: BattleContext
    ) -> bool:
        return True

    def execute(
        self,
        move: Move,
        user: PokemonLike,
        targets: List[PokemonLike],
        ctx: BattleContext
    ) -> None:
        # For a generic Status move, we might just apply its primary effect(s)
        # which would be represented in move.primary_effects or dedicated fields.
        # Here we leave it abstract.
        pass


# --- Core Move class --------------------------------------------------------

@dataclass
class Move:
    name: str
    type: Type
    category: MoveCategory
    base_power: int
    accuracy: float  # 0.0-1.0; use 1.0 for "100%".
    max_pp: int
    priority: int = 0
    target: MoveTarget = MoveTarget.SINGLE_OPPONENT
    flags: MoveFlags = field(default_factory=MoveFlags)

    # Secondary effects (chance-based extras when the move hits)
    secondary_effects: List[SecondaryEffect] = field(default_factory=list)

    # Additional metadata for generational mechanics
    z_power: Optional[int] = None             # base power as a Z-Move
    max_move_power: Optional[int] = None      # base power as a Max Move

    # Behavior strategy for special cases
    behavior: MoveBehavior = field(
        default_factory=lambda: DefaultDamageBehavior()
    )

    # Internal state
    current_pp: int = field(init=False)

    def __post_init__(self) -> None:
        self.current_pp = self.max_pp

    # --- Public API ---------------------------------------------------------

    def can_use(self, user: PokemonLike, ctx: BattleContext) -> bool:
        """
        Check PP, user status, Choice item lock, etc.
        This is where you enforce things like 'once per battle' mechanics externally.
        """
        if self.current_pp <= 0:
            return False
        # Additional checks: Disable, Taunt, Imprison, etc.
        return self.behavior.can_execute(self, user, [], ctx)

    def select_targets(
        self,
        user: PokemonLike,
        ctx: BattleContext
    ) -> List[PokemonLike]:
        """
        Given the battle context and move's target type, determine the actual
        list of target Pokémon in this situation.
        The BattleContext would need APIs to query allies, opponents, etc.
        """
        # This is left abstract; in a real engine you'd query ctx for positions.
        return []

    def use(
        self,
        user: PokemonLike,
        ctx: BattleContext
    ) -> None:
        """
        Perform the move:
        - consume PP
        - determine targets
        - invoke behavior
        - handle post-move effects (recoil, stat drops, etc.)
        """
        if not self.can_use(user, ctx):
            return  # fail silently or raise an exception

        self.consume_pp(user, ctx)
        targets = self.select_targets(user, ctx)
        self.behavior.execute(self, user, targets, ctx)
        self._after_use(user, targets, ctx)

    def consume_pp(self, user: PokemonLike, ctx: BattleContext) -> None:
        """
        Decrement PP, accounting for abilities/items that modify PP consumption.
        """
        # Example: Pressure increases PP usage for targeting that Pokémon.
        # For simplicity, just reduce by 1 here.
        if self.current_pp > 0:
            self.current_pp -= 1

    def _after_use(
        self,
        user: PokemonLike,
        targets: List[PokemonLike],
        ctx: BattleContext
    ) -> None:
        """
        Handle recoil, self-stat drops, recharge turns, move-lock mechanics, etc.
        """
        pass

    # --- Helpers for special mechanics --------------------------------------

    def as_z_move(self, user: PokemonLike) -> Move:
        """
        Return a new Move instance representing this move as a Z-Move,
        with appropriate power/type and behavior overrides.
        """
        if self.category == MoveCategory.STATUS:
            # Z-Status: often keeps 0 power but has special secondary effect,
            # which would be modeled with a specific ZStatusBehavior.
            new_behavior = self.behavior  # or a Z-status-specific one
            return Move(
                name=f"Z-{self.name}",
                type=self.type,
                category=self.category,
                base_power=0,
                accuracy=1.0,
                max_pp=1,  # used only once
                priority=self.priority,
                target=self.target,
                flags=self.flags,
                secondary_effects=self.secondary_effects,
                z_power=self.z_power,
                max_move_power=self.max_move_power,
                behavior=new_behavior
            )
        else:
            # Offensive Z-Move: power is determined by z_power (precomputed)
            power = self.z_power or self.base_power  # fallback
            return Move(
                name=f"Z-{self.name}",
                type=self.type,
                category=self.category,
                base_power=power,
                accuracy=1.0,  # Z-Moves generally don't miss barring some cases
                max_pp=1,
                priority=self.priority,
                target=self.target,
                flags=self.flags,
                secondary_effects=self.secondary_effects,
                z_power=self.z_power,
                max_move_power=self.max_move_power,
                behavior=self.behavior
            )

    def as_max_move(self, user: PokemonLike) -> Move:
        """
        Return a new Move instance representing the Max Move version of this move.
        In a full engine, the Max Move type, power, and behavior depends on
        this move and the user's data (e.g., G-Max forms).
        """
        power = self.max_move_power or self.base_power
        # Max moves have standardized secondary effects; you'd attach
        # specific behavior here (e.g., set weather, terrain).
        return Move(
            name=f"Max {self.name}",
            type=self.type,
            category=self.category,
            base_power=power,
            accuracy=1.0,
            max_pp=3,  # Dynamax lasts 3 turns, but you can decide how to track this
            priority=self.priority,
            target=self.target,
            flags=self.flags,
            secondary_effects=[],  # replaced by Max Move built-in effects
            behavior=self.behavior
        )
```

---

## 10. Modeling learnsets (brief)

You would usually **not bake learnsets into the Move class**; instead, you define:

```python
class LearnMethod(Enum):
    LEVEL_UP = auto()
    TM = auto()
    TUTOR = auto()
    EGG = auto()
    EVENT = auto()
    REMINDER = auto()


@dataclass
class LearnEntry:
    move: Move
    method: LearnMethod
    level: Optional[int] = None  # for level-up
    tm_id: Optional[str] = None  # for TM/TR identifiers
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Learnset:
    species_id: str
    entries: List[LearnEntry]

    def get_moves_by_level(self, level: int) -> List[Move]:
        return [
            entry.move
            for entry in self.entries
            if entry.method == LearnMethod.LEVEL_UP
            and entry.level is not None
            and entry.level <= level
        ]

    def get_tm_moves(self) -> List[Move]:
        return [e.move for e in self.entries if e.method == LearnMethod.TM]
```

This keeps **moves** and **learnsets** separate but linked.

---

## 11. Summary

- A **move** is a rich object: type, category, power, accuracy, priority, targeting, flags, and effects (primary + secondary).
- Moves interact deeply with:
  - Pokémon (stats, type, form, status),
  - abilities,
  - items,
  - field states (weather, terrain, screens, hazards),
  - special mechanics (Mega, Z-Moves, Dynamax, Terastallization),
  - and format (singles vs doubles).
- In Python OOP:
  - use enums & dataclasses for clarity,
  - use a `Move` class holding static data + a pluggable `MoveBehavior`,
  - use a `BattleContext` to supply environment and side information,
  - keep **learnsets** as separate objects (e.g., `Learnset` with `LearnEntry`).

This structure gives you a flexible, extensible base where you can implement additional exceptions and mechanics incrementally without turning everything into giant `if`/`else` blocks.