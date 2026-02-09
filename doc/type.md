## 1. What a “type” is in Pokémon

In the mainline Pokémon games, **type** is a core attribute that drives a large part of the battle system:

- **Pokémon have types** (1 or 2 at a time; sometimes temporarily 3 with moves like Forest’s Curse/Trick-or-Treat).
- **Moves have a type** (usually fixed, sometimes dynamic).
- **Mechanics** (Terastallization, Mega Evolution, Dynamax, Z-Moves, etc.) often *change* or *use* types.
- **Systems** like abilities, items, weather, terrain, and status conditions interpret and modify type in various ways.

In modern games (Gen 9), there are **18 standard elemental types**:

> Normal, Fire, Water, Grass, Electric, Ice, Fighting, Poison, Ground, Flying, Psychic, Bug, Rock, Ghost, Dragon, Dark, Steel, Fairy

---

## 2. The roles of type

### 2.1 Offensive role (attacking type)

When a move is used, its **type** is used to determine:

1. **Type effectiveness** (damage multiplier)
   - For each of the defender’s types, the game looks up `move_type -> defender_type`:
     - 0× (immune)
     - 0.5× (resisted)
     - 1× (neutral)
     - 2× (super-effective)
   - If the defender has **two types**, multipliers are multiplied. Example:
     - Fire vs Steel: 2×  
     - Fire vs Grass: 2×  
     - Fire vs Grass/Steel: 2×2 = 4× (quad-weak)

2. **STAB (Same-Type Attack Bonus)**
   - If the move’s type is one of the user’s types, damage gets a multiplier:
     - Normally **1.5×**
     - With **Adaptability**: **2×**
   - With Terastallization, this becomes richer (see below).

3. **Interaction with abilities and items**
   - Some abilities *negate* or *absorb* moves of certain types:
     - **Levitate**: immune to Ground moves.
     - **Volt Absorb**: Electric moves do 0 damage and heal HP.
     - **Water Absorb**, **Flash Fire**, **Sap Sipper**, **Lightning Rod**, **Storm Drain**, etc.
   - Some items boost moves of a given type:
     - **Type-boosting items**: Charcoal (Fire), Mystic Water (Water), etc.
     - **Plates** (for Arceus), **Drives** (for Genesect), **Memories** (for Silvally), etc.

4. **Interaction with field/misc mechanics**
   - **Weather**:  
     - Sun boosts Fire moves and weakens Water moves.  
     - Rain boosts Water moves and weakens Fire moves.
   - **Terrain**:  
     - Electric Terrain boosts Electric moves of grounded Pokémon.  
     - Grassy Terrain boosts Grass moves, etc.
   - **Other effects**: Reflect/Light Screen, Aurora Veil, etc. don’t care about type, but co-exist with type effects.

---

### 2.2 Defensive role (defender’s types)

A Pokémon’s type(s) determine:

1. **Damage taken from each attacking type**
   - Via the same chart: `move_type -> defender_type` multiplier.

2. **Immunities**
   - **Type chart** immunities:
     - Ground moves vs Flying-type: 0×
     - Normal & Fighting moves vs Ghost-type: 0×
     - Poison vs Steel-type: 0×
     - Electric vs Ground-type: 0×
   - **Ability-based** immunities:
     - Example: Levitate, Volt Absorb, Water Absorb, etc.

3. **Interaction with status / special move restrictions**
   - Type isn’t only about damage; it also controls whether some **status or move effects** work.
   - Important examples:
     - **Poisoning**
       - Poison- and Steel-types cannot be poisoned by *most* standard moves (Toxic, Sludge Bomb, etc.).
       - Ability **Corrosion** allows poisoning Steel- and Poison-types with Poison moves.
     - **Paralysis**
       - The move **Thunder Wave** cannot affect Ground-types (Electric-to-Ground immunity).
       - Other paralysis-causing moves (e.g. Stun Spore) can affect them if other conditions allow.
     - **Powder moves** (Sleep Powder, Spore, Leech Seed, etc.)
       - Grass-type Pokémon are immune to powder and spore moves.
     - **One-hit KO** moves:
       - Fissure (Ground) fails on Flying-types, etc., because of type immunity.

   - These are all examples where the **move type vs target type** is consulted even if the move’s primary effect is *not damage*.

---

## 3. Types and other systems

### 3.1 Types and Pokémon (species and form changes)

Each Pokémon species has:

- A **base typing** (e.g., Charizard: Fire/Flying).
- Some **forms** have different typings:
  - Regional forms (Alolan, Galarian, Hisuian, Paldean).
  - Alternate forms (Rotom forms, Arceus with Plates, Silvally with Memories).
  - **Mega Evolutions**: often change type (e.g., Mega Charizard X: Fire/Dragon).
  - **Primal Reversions** (Primal Groudon: Ground/Fire).

During battle, Pokémon types can change temporarily by:

- **Soak** → changes target to pure Water.
- **Magic Powder** → pure Psychic.
- **Trick-or-Treat** → adds Ghost type (can make 3 types temporarily).
- **Forest’s Curse** → adds Grass type.
- **Terastallization** → changes to a single **Tera Type**.

#### Terastallization (Gen 9)

- Each Pokémon has a **Tera Type** (any of the 18).
- When Terastallized:
  - **Defensively**: the Pokémon becomes **pure Tera Type**. Original types no longer matter for weaknesses/resistances.
  - **Offensively (STAB)**:
    - STAB applies to:
      - All of the Pokémon’s *original* types, and
      - Its Tera Type.
    - If move type == Tera Type and that type was already one of its original types:
      - STAB becomes **2×**.
    - If move type == Tera Type but that type was *not* an original type:
      - STAB is **1.5×** (normal STAB).
    - Other original types still get STAB (1.5×).

Example (offense):

- Original type: Water/Flying  
- Tera Type: Water  
- During Tera:
  - Water moves: 2× STAB  
  - Flying moves: 1.5× STAB  
  - Other types: 1×

---

### 3.2 Types and moves

Every move has:

- A **type** (Fire, Water, …).
- A **category**: Physical, Special, Status (separate concept from type).
- Some moves have dynamic type:
  - **Hidden Power** (pre-Gen 8): type based on IVs.
  - **Weather Ball**: type changes with weather.
  - **Judgment** (Arceus), **Techno Blast** (Genesect), **Multi-Attack** (Silvally): type changes based on held item.
  - **Revelation Dance**: type matches the user’s primary type.
  - **Tera Blast**:
    - Type becomes user’s Tera Type while Terastallized.
    - Category (Physical/Special) changes based on user’s higher offensive stat.

Type effects that usually matter:

- **Damage**: based on move type vs target type(s).
- **Status immunity through type** (as above).
- **STAB**: based on whether move type matches attacker’s type(s) / Tera type.

---

### 3.3 Types and abilities (non-exhaustive but important patterns)

Abilities that **interact directly with type** (main categories):

1. **Immunities / absorption**
   - Levitate (Ground), Volt Absorb (Electric), Water Absorb (Water), Lightning Rod (Electric), Storm Drain (Water), Sap Sipper (Grass), Flash Fire (Fire), etc.
   - Some also **raise a stat** when hit by that type.

2. **Type conversion / type-based STAB change**
   - Protean / Libero: change user’s type to the type of the move they use (once per switch-in in modern gens).
   - Normalize: converts *all* the user’s moves to Normal-type and boosts them.
   - Color Change: user’s type becomes the type of the last move that hit it.

3. **Boosts to certain types**
   - Steelworker: boosts Steel-type moves.
   - Mega Launcher: boosts aura/pulse moves (partial type correlation).
   - Tinted Lens: doesn’t change type directly but interacts with resistances.

4. **Field- or weather-related type boosts**
   - Sand Force: boosts Rock/Ground/Steel moves in sandstorm.
   - Solar Power, Chlorophyll, Swift Swim: stats change based on weather, indirectly affecting how type-boosted moves perform.

You generally **do not encode all of this inside the “type” object**; you encode it as abilities that *modify* the damage or effectiveness computed from type.

---

### 3.4 Types and items

Items that explicitly deal with types:

- **Type-boosting items**: Charcoal (Fire), Mystic Water (Water), etc. — typically 1.2× boost.
- **Plates** (for Arceus): change Arceus’s type and Judgment’s type.
- **Drives** (for Genesect): change Techno Blast’s type.
- **Memories** (for Silvally): change Multi-Attack’s type.
- **Orbs / signature items**: Griseous Orb (Giratina), etc., sometimes boosting specific types.

Again, items are *modifiers* to the basic type system.

---

### 3.5 Types, Z-Moves, Dynamax, and Max/G-Max moves

- **Z-Moves**
  - Keep the original move’s type.
  - Type effectiveness and STAB are computed using that type.
  - Mostly just a big base power modification and unique effects; type logic is unchanged.

- **Dynamax / Max Moves**
  - Max Moves inherit the **type of the base move**.
  - Type effectiveness & STAB use that type.
  - Additionally, Max Moves cause **secondary field effects** depending on type:
    - Max Flare (Fire) sets Sun.
    - Max Geyser (Water) sets Rain.
    - Max Lightning (Electric) sets Electric Terrain, etc.

- **Gigantamax Moves**
  - Type is fixed (often same type as base move).
  - May have unique added effect, but type logic is standard.

---

### 3.6 Single vs Double Battles

Type rules themselves **don’t change** between singles and doubles, but battles are affected by:

- **Spread moves** (Earthquake, Surf, Rock Slide):
  - Hit multiple targets, but have a **0.75× damage modifier** in doubles/triples.
  - Still use regular type effectiveness for each target individually.
- **Redirection abilities** (Lightning Rod, Storm Drain):
  - Matter more in doubles because one Pokémon can “absorb” moves aimed at its partner.
- **Friendly fire**:
  - Moves like Earthquake can hit your ally, and type effectiveness applies normally.

---

## 4. Modeling “type” in an object-oriented Python design

Below is a **clean OO approach** that:

- Keeps type logic focused and reusable.
- Separates raw type effectiveness from context (abilities/items/field).
- Supports:
  - Single type
  - Dual type
  - Terastallization
  - Future extensions

We’ll use:

- `Enum` for the elemental types.
- A centralized **type chart** for multipliers.
- A `Typing` class for a Pokémon’s current type combination.
- A small “engine” for computing:
  - Raw effectiveness
  - STAB (including Tera logic)

### 4.1 Enumerating types

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Iterable


class ElementType(Enum):
    NORMAL = auto()
    FIRE = auto()
    WATER = auto()
    ELECTRIC = auto()
    GRASS = auto()
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

    def __str__(self) -> str:
        return self.name.capitalize()
```

### 4.2 Type chart (data layer)

Define a **data structure** for raw type effectiveness. The exact values can be stored in:

- A Python dictionary.
- Or an external JSON/YAML file loaded at runtime.

Structure example (partial; you’d fill in the whole chart):

```python
# type: ElementType (attacking) -> ElementType (defending) -> multiplier
RAW_TYPE_CHART: dict[ElementType, dict[ElementType, float]] = {
    ElementType.FIRE: {
        ElementType.GRASS: 2.0,
        ElementType.ICE: 2.0,
        ElementType.BUG: 2.0,
        ElementType.STEEL: 2.0,

        ElementType.FIRE: 0.5,
        ElementType.WATER: 0.5,
        ElementType.ROCK: 0.5,
        ElementType.DRAGON: 0.5,
        # other targets default to 1.0
    },
    ElementType.WATER: {
        ElementType.FIRE: 2.0,
        ElementType.GROUND: 2.0,
        ElementType.ROCK: 2.0,

        ElementType.WATER: 0.5,
        ElementType.GRASS: 0.5,
        ElementType.DRAGON: 0.5,
    },
    # ...fill out all attacking types...
}
```

You can then wrap this in a helper function:

```python
def raw_type_multiplier(attacking: ElementType, defending: ElementType) -> float:
    """Return the base effectiveness of attacking vs defending, ignoring abilities/items."""
    return RAW_TYPE_CHART.get(attacking, {}).get(defending, 1.0)
```

> Design choice: Keeping the chart as data makes it easy to tweak, patch, or handle cross-gen differences if you want.

---

### 4.3 Modeling a Pokémon’s typing

A Pokémon can have:

- 1 type (primary only).
- 2 types (primary + secondary).
- Temporarily 3 types due to certain moves (Forest’s Curse, Trick-or-Treat).
- A Tera Type *overriding defensive typing* and modifying STAB.

We’ll create a `Typing` class to represent **the current in-battle typing** of a Pokémon, independent of species:

```python
@dataclass(frozen=True)
class Typing:
    """
    Represents a Pokémon's current typing:
    - One or two 'natural' types.
    - Optionally, an applied Tera Type (for offense/defense adjustments).
    """
    primary: ElementType
    secondary: Optional[ElementType] = None
    tera_type: Optional[ElementType] = None

    def natural_types(self) -> tuple[ElementType, ...]:
        """Return the Pokémon's non-Tera types (1 or 2)."""
        if self.secondary is None:
            return (self.primary,)
        if self.secondary == self.primary:
            return (self.primary,)
        return (self.primary, self.secondary)

    def effective_defensive_types(self) -> tuple[ElementType, ...]:
        """
        Types used for defensive effectiveness:
        - If tera_type is applied: Pokémon is treated as pure tera_type defensively.
        - Otherwise: use natural types.
        """
        if self.tera_type is not None:
            return (self.tera_type,)
        return self.natural_types()

    def raw_effectiveness_from(self, attacking_type: ElementType) -> float:
        """
        Base type effectiveness of an attacking type against this Pokémon,
        ignoring abilities, items, weather, etc.
        """
        multiplier = 1.0
        for t in self.effective_defensive_types():
            multiplier *= raw_type_multiplier(attacking_type, t)
            if multiplier == 0.0:
                break
        return multiplier
```

This handles:

- Normal single/dual typing.
- Defensive behavior of Terastallization (pure tera type).

---

### 4.4 STAB computation (including Tera logic)

Now we need a function/method that answers:

> Given a move type and the user’s typing, what is the **STAB multiplier**?

We’ll use **current official Tera rules**:

```python
def stab_multiplier(
    user_typing: Typing,
    move_type: ElementType,
    has_adaptability: bool = False
) -> float:
    """
    Compute STAB multiplier for a given move type, considering:
    - Natural types
    - Tera type (if any)
    - Adaptability (as a simple flag here)
    """
    natural = set(user_typing.natural_types())
    tera = user_typing.tera_type

    base_stab = 1.0

    # Does move match an original type?
    natural_match = move_type in natural

    # Does move match the Tera Type?
    tera_match = tera is not None and move_type == tera

    if not natural_match and not tera_match:
        return 1.0  # no STAB at all

    # If move matches Tera type and that type is also natural:
    #   STAB becomes 2× (or 2.25× with Adaptability if you want to support that).
    if tera_match and natural_match:
        base_stab = 2.0
    else:
        # Normal STAB
        base_stab = 1.5

    if has_adaptability:
        # Adaptability: boosts STAB to 2× instead of 1.5×
        # For Tera+Adaptability, you might model as 2.25× or keep at 2×
        # depending on which generation/engine rules you approximate.
        if base_stab == 1.5:
            base_stab = 2.0
        elif base_stab == 2.0:
            base_stab = 2.25  # design choice / approximation

    return base_stab
```

> In a fully accurate simulator, you’d codify the **exact formula per generation** and test it against known battle scenarios, but the structure above supports that.

---

### 4.5 Putting it together: calculating damage-relevant multipliers

A **battle engine** would do something like:

```python
@dataclass
class DamageContext:
    attacker_typing: Typing
    defender_typing: Typing
    move_type: ElementType
    attacker_has_adaptability: bool = False
    # Add more flags/refs for abilities, items, weather, terrain, etc.
    # e.g. attacker_ability, defender_ability, field_state, items...


def type_based_multiplier(ctx: DamageContext) -> float:
    """
    Compute the combined type-based multiplier part of damage:
    STAB × type effectiveness, ignoring non-type modifiers (crit, random factor, etc.)
    """
    # STAB
    stab = stab_multiplier(
        user_typing=ctx.attacker_typing,
        move_type=ctx.move_type,
        has_adaptability=ctx.attacker_has_adaptability,
    )

    # Raw effectiveness
    effectiveness = ctx.defender_typing.raw_effectiveness_from(ctx.move_type)

    return stab * effectiveness
```

Then you can extend `DamageContext` and this function to include:

- Ability-based immunities (e.g. set effectiveness to 0 if Levitate + Ground).
- Ability-based stat or damage multipliers (Flash Fire, etc.).
- Item-based type boosts (Charcoal, etc.).
- Weather and terrain boosts.

**Important design principle**: keep the **core type system** (chart + typing + STAB) separate from:

- Abilities
- Items
- Field effects

These should be **pluggable layers** that modify or override the base multiplier.

---

### 4.6 Handling special mechanics cleanly

To model more mechanics, you can extend the same approach:

- **Ability system**
  - Make an `Ability` base class with hooks like:
    - `modify_type_multiplier(ctx, current_multiplier) -> float`
    - `modify_stab(ctx, current_stab) -> float`
    - `on_move_targeted(ctx) -> None`
  - Concrete abilities (Levitate, Flash Fire, etc.) override these.

- **Item system**
  - Similar to abilities; items have hooks to modify multipliers.

- **Field/Weather/Terrain**
  - Represented as a `FieldState` class with methods:
    - `modify_type_multiplier(ctx, current_multiplier) -> float`
    - `modify_stab(ctx, current_stab) -> float`

**Example integration flow in a battle engine**:

1. Compute base STAB.
2. Let abilities modify STAB.
3. Compute base effectiveness from type chart.
4. Let abilities/items/field alter this (immunities, boosts).
5. Multiply STAB × effectiveness × other damage factors.

The **type classes** never need to know about specific abilities or items; they only know about **types and multipliers**. This keeps them simple, testable, and reusable.

---

## 5. Summary

- A **type** in Pokémon is a foundational concept that influences:
  - Damage (type chart, STAB).
  - Status application (Poison/Steel immunity, powder immunity).
  - Interaction with abilities, items, weather, terrain, and major mechanics (Tera, Mega, Dynamax, Z-Moves).
- In an OO Python design:
  - Represent elemental types with an `Enum`.
  - Store the type chart as **data** (dicts or JSON).
  - Use a `Typing` class to represent a Pokémon’s current typing (including Tera).
  - Provide small, focused functions:
    - `raw_type_multiplier(attacking, defending)`
    - `Typing.raw_effectiveness_from(attacking_type)`
    - `stab_multiplier(user_typing, move_type, ...)`
  - Let abilities/items/field effects be separate objects that **hook into** damage processing, rather than hard-coding them into `Type`.

This architecture is flexible enough to handle all the depth and exceptions of the Pokémon type system while staying maintainable and testable for a full battle simulator.