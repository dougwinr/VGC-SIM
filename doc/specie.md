## 1. What is a Pokémon *species*?

In the games, a **Pokémon species** is the *template* that all individual Pokémon of that kind are created from.  
Example: *Bulbasaur* is a species. Your level 12 Bulbasaur with certain IVs/EVs, nature, moves, etc., is an *individual instance* of that species.

A species defines **what is possible** for any individual of that species:

- Which **types** it can have (including per-form differences)
- Its **base stats**
- Which **abilities** it can have
- Which **moves** it can learn and *how* (level-up, TM, egg, tutor, special)
- Its **evolution line** and evolution methods
- Its **breeding properties** (egg groups, gender ratio, hatch time)
- Various **battle-relevant attributes** (weight, height, catch rate, EV yield, etc.)
- Whether it has **forms**, **Megas**, **Gigantamax**, special Z-Moves, etc.

The *individual Pokémon* adds the *random and customizable parts* (IVs, nature, EVs, current HP, status, held item, etc.), but all of that sits atop the species definition.

---

## 2. What does the species determine?

### 2.1 Identity & classification

Per species you have, at minimum:

- **Name**: e.g., “Garchomp”
- **Dex number(s)**: National Dex, regional Dex indices
- **Category flags**:
  - `is_legendary`
  - `is_mythical`
  - `is_ultra_beast`
  - `is_paradox`
  - `is_sub_legendary` (like the Tapus, Guardians, etc.)
- **Evolution family**:
  - Pre-evolutions and evolutions
  - Branching evolutions (Eevee, Wurmple, etc.)
  - Cross-generation evolutions (e.g., Pichu → Pikachu → Raichu, and Alolan Raichu)

These properties don’t change per individual; they’re inherent to the species/form.

---

### 2.2 Types & base stats

Each species (or form) has:

- **Types**:
  - Primary type (mandatory)
  - Optional secondary type
  - Some forms change types (e.g., Rotom forms, Alolan forms, Mega Evolutions, etc.).

- **Base stats** (0–255 each):
  - HP, Attack, Defense, Special Attack, Special Defense, Speed  
  Example: Garchomp has base stats `(108, 130, 95, 80, 85, 102)`.

These base stats + an individual’s IVs/EVs + nature determine the actual battle stats via the standard formulas.

---

### 2.3 Abilities

The species defines *which abilities are possible*:

- `abilities`: usually up to **2 normal abilities** (or 1)
- `hidden_ability`: 0 or 1 *Hidden Ability*
- Sometimes **form-specific abilities**:
  - Example: Aegislash Blade/Shield form share the same species but change stats via **Ability** Stance Change.
  - Mega Evolutions always have a special ability (e.g., Mega Gardevoir → Pixilate).

An individual Pokémon *selects one* of the available abilities (or hidden ability if allowed) from the species’ list.

**Species-level constraints:**

- Only the abilities defined in the species can ever appear on an individual (barring hacking).
- Some signature abilities are tied to a small set of species (e.g., Disguise on Mimikyu, Multiscale on Lugia, Schooling on Wishiwashi).

---

### 2.4 Learnsets (moves the species can learn)

The species defines which moves are *legally learnable* and by what method:

- **Level-up moves**:  
  A map `level → list of moves`.  
  Example: Charmander learns Ember at level 9.
- **TM / HM / TR moves**:  
  A list of TMs/TRs it can use (varies by generation).
- **Move tutors**:  
  Species-specific compatibility lists with tutor moves.
- **Egg moves**:
  - Moves inherited through breeding from compatible parents.
  - Depends on species’ egg groups and sometimes male/female pairing.
- **Special/event moves**:
  - Moves only available from distributions (e.g., Surfing Pikachu, V-create Rayquaza in events).

An individual Pokémon at runtime will have a *subset* of 4 moves chosen from these possibilities.

---

### 2.5 Evolution & family

The species encodes how it evolves:

- **Basic parameters**:
  - Whether it can evolve
  - What it evolves *into*
  - Level or other conditions required

- **Common evolution triggers**:
  - Level (e.g., Lv 16)
  - Happiness/friendship (sometimes with time-of-day)
  - Holding an item & leveling up
  - Trade, sometimes holding an item
  - Knowing a specific move when leveling
  - Being in a specific location
  - Gender-dependent, version-dependent, or stat-comparison-dependent
  - Use of evolutionary stones
  - Using specific methods (spinning, walking certain steps, etc. in newer gens)

All of this is determined by the species you currently are and what species is defined as the next stage.

---

### 2.6 Breeding & growth

Species-level breeding properties:

- **Egg groups**: determine breeding compatibility.
- **Gender ratio**:
  - e.g., 87.5% male, 12.5% female  
  - Or genderless (e.g., Magnemite).
- **Base hatch time**: encoded as “egg cycles.”
- **Baby Pokémon** and pre-evolutions:
  - Sometimes species is marked as “baby form” (e.g., Pichu, Azurill).
- **Growth rate/experience curve**:
  - Fast / Medium Fast / Medium Slow / Slow / Fluctuating / Erratic.
  - Determines how much EXP is required per level.

---

### 2.7 Catch & friendship

Species defines:

- **Catch rate**: integer affecting capture probability.
- **Base friendship**: starting happiness.
  - Relevant for evolution by friendship and for moves like Return/Frustration.
- **Base EXP yield**: how much experience this species gives when defeated.

---

### 2.8 Physical properties

Several moves and mechanics rely on species-level physical attributes:

- **Height**
- **Weight**
  - Affects moves like Low Kick and Grass Knot (power scales with target weight).
  - Affects Heavy Slam / Heat Crash (relative weight to opponent).
  - Affects whether Sky Drop works (too heavy → immune).

---

### 2.9 Forms and variants

Many species have **multiple forms**, each with its own mechanical or cosmetic differences.

#### Types of forms:

1. **Regional forms** (Alolan, Galarian, Hisuian, Paldean):
   - Different typing
   - Different stats
   - Different moves/abilities
   - Sometimes different evolutions.

2. **Battle-only forms**:
   - **Mega Evolutions** (e.g., Mega Gengar)
   - **Primal Reversion** (Groudon, Kyogre)
   - **Ultra Burst** (Ultra Necrozma)
   - **Gigantamax** forms
   - Temporary forms like Wishiwashi Schooling, Minior’s core, etc.

3. **Form-change in-battle based on ability or move**:
   - Aegislash (Stance Change)
   - Darmanitan (Zen Mode)
   - Morpeko (Hunger Switch)
   - Mimikyu (Disguise / busted form)
   - Shaymin Land/Sky (Gracidea + day + not frozen)
   - Castform (weather-based)
   - Cherrim, Eiscue, etc.

4. **Cosmetic-only forms**:
   - Spinda spot patterns
   - Furfrou trims
   - Unown letters (mostly cosmetic, same stats)
   - Vivillon patterns (minor mechanical differences only via pattern interactions if any)
   - Cap Pikachu variants (mostly event cosmetic, sometimes move differences).

In data modeling, you either:

- Treat each form as a **separate “form object”** with its own stats/types/etc., or
- Treat each form as a **separate species entry** with a `base_species_id` and `form_id`.

---

## 3. How species interacts with battle systems

### 3.1 Single vs Double battles

The species doesn’t know “single vs double”; instead:

- The species defines:
  - Potential roles: tank, sweeper, support, etc., via its base stats, typing, abilities, movepool.
  - Affinities for strategies (Trick Room, weather teams, etc.).

- In **single** battles:
  - One Pokémon on each side.
  - Focus is on individual matchups and 1v1 coverage.

- In **double** battles:
  - 2 Pokémon per side simultaneously.
  - Species-specific interactions become more crucial:
    - Abilities like **Intimidate**, **Levitate**, **Storm Drain**, **Lightning Rod**.
    - Moves that affect multiple targets (Surf, Rock Slide, Earthquake).
    - Species that set up or exploit weather, terrain, etc.

Species-level stats and abilities drive which species are viable for doubles roles (e.g., Hitmontop with Intimidate and Fake Out, Garchomp with Earthquake, Togekiss with Follow Me).

---

### 3.2 Types, STAB, weaknesses, and immunities

From species types we derive:

- **STAB** (Same-Type Attack Bonus):
  - If a Pokémon uses a move that matches one of its types, it gets a damage multiplier (typical: 1.5×; with Adaptability: 2×).
- **Weaknesses & resistances**:
  - Type chart applied to attacking move type vs defending species’ type(s).
- **Immunities**:
  - Ground-type moves vs Flying-type (or Levitate / non-grounded).
  - Electric vs Ground-types (Electric moves don’t affect them).
  - Status-related immunities (e.g., Electric-type generally immune to paralysis from Gen 6+ for Electric-status moves, Grass-type immune to powder moves, Ghost-type immune to trapping moves, etc.).

All of these are essentially functions of *species typing* (plus abilities/items/field).

---

### 3.3 Abilities and items (species interactions)

Species determines which **abilities** and some **species-specific items** exist:

- **Abilities**:  
  e.g., species with Drizzle, Intimidate, Flash Fire, Levitate, etc.  
  Abilities interact with:
  - Moves (e.g., Water Absorb and Surf)
  - Types (e.g., Levitate + Ground immunity)
  - Status (e.g., Immunity, Magic Guard)
  - Weather/terrain (e.g., Chlorophyll, Sand Rush)

- **Species-specific items**:
  - **Thick Club** (Marowak line) doubles Attack.
  - **Light Ball** (Pikachu) boosts Attack and Special Attack.
  - **Soul Dew** (Latios/Latias) boosts stats.
  - **Griseous Orb** (Giratina) required for Origin Form.
  - **Rusted Sword/Shield** (Zacian/Zamazenta) change forms and types.
  - **Mega Stones**, **Primal Orbs**, **Drive Plates**, **Memory items** (Silvally), etc.

Usually, the game enforces that only certain species can benefit or even hold some of these items meaningfully.

---

### 3.4 Status conditions

Species interacts with status via:

- **Type-based immunities**:
  - Electric-type generally immune to paralysis (for many sources).
  - Fire-type immune to burn from Fire-type moves.
  - Poison- and Steel-types immune to poison (to most sources).

- **Ability-based immunities**:
  - Immunity, Water Veil, Leaf Guard, etc., but these are ability-level, not species-level—though species determines *if it can even have that ability*.

No species is “hard-coded” to be immune to every status, but type and ability combinations effectively create such behavior.

---

### 3.5 Interactions with special mechanics

#### 3.5.1 Mega Evolution

- Only certain species have **Mega forms**.
- Requirements:
  - Correct species + matching Mega Stone.
  - Occurs during battle, consuming your Mega slot for that battle.
- Changes:
  - Type (maybe)
  - Ability (always changes to a specific Mega ability)
  - Base stats (modified significantly)

Species-level modeling:

- “Base species” has a list of `mega_forms`.
- Each Mega form behaves mechanically like a separate form/species during battle.
- Individual-level attributes (IVs, EVs, nature, current HP, moves) **carry over**.

Constraints:

- Can’t Mega and use a Z-Move on the same Pokémon in the same battle (Gen 7).
- Megas are generally incompatible with Dynamax (SwSh meta).

---

#### 3.5.2 Primal Reversion

- Similar to Mega, but:
  - Groudon <-> Primal Groudon via Red Orb.
  - Kyogre <-> Primal Kyogre via Blue Orb.
- Transformation is automatic at battle start if holding the correct orb.
- Changes type, ability, stats.

Modeled like a form linked to both species and item.

---

#### 3.5.3 Z-Moves

- **Type-based Z-Moves**:
  - Any species with a damaging move of a given type and the corresponding Z-Crystal can use that Z-Move.
- **Species-specific Z-Moves**:
  - Only certain species (or line) can use them.
  - Require:
    - Specific species
    - Specific base move
    - Specific Z-Crystal
  - Example: Pikachu + Volt Tackle + Pikanium Z → Catastropika.

Species data thus includes:

- Whether it has any **signature Z-Moves**.
- The mapping from base move + species → unique Z-Move.

---

#### 3.5.4 Dynamax & Gigantamax

- **Dynamax**:
  - Most species can Dynamax.
  - HP multiplier is generic, but absolute HP depends on species’ base HP (and level, EVs, etc.).
  - Offensive moves become **Max Moves** whose type depends on the move’s type (which is determined by species’ movepool).

- **Gigantamax**:
  - Certain species (or specific forms) have a Gigantamax form.
  - Unique **G-Max Moves** replace certain Max Moves.
  - G-Max forms typically only cosmetic + signature move differences, but still species-defined.

Species data needs:

- `can_dynamax` (generally true except in restricted formats).
- `gmax_form` (if any) and its `gmax_moves`.

---

#### 3.5.5 Terastallization

- **Tera Type**:
  - Each individual has a Tera Type, but typically defaults to one of the species’ own types.
  - It can be changed by in-game mechanics.

Species-level roles:

- The species types and movepool define **how effective** a Tera Type is.
- Certain species have unique Tera mechanics:
  - Ogerpon masks (forms + Tera interactions),
  - Terapagos forms.

In modeling, you’d keep Tera Type on the individual, but species strongly influences what makes sense strategically.

---

## 4. Edge cases & oddities (high level)

Examples of special species behaviors:

- **Ditto**:
  - Special move Transform; copies species/moves of opponent.
  - In breeding, acts as a “wild card” pairing.

- **Shedinja**:
  - HP is always 1 regardless of stats; defined by species rules.
  - Gets Wonder Guard ability almost uniquely.

- **Wishiwashi**:
  - Schooling ability changes it from Solo to School form above certain HP.
  - Forms have wildly different stats.

- **Zygarde**:
  - 10%, 50%, Complete forms, some obtained via assembly mechanic.

- **Rotom**:
  - Many appliance forms with different secondary types and signature moves.

All these are good test cases when designing your data model, because they challenge naive assumptions.

---

## 5. Modeling Pokémon species in Python (OOP)

### 5.1 Separation of concerns

A robust model should clearly separate:

1. **Species template** — “what this species/form is in theory”
   - `PokemonSpecies` (or `SpeciesTemplate`)

2. **Individual Pokémon** — “this specific Pikachu”
   - `Pokemon` (or `PokemonInstance`)
   - Has: species reference, level, IVs, EVs, nature, current stats, moves, held item, status, etc.

3. **Battle state** — “this Pokémon right now in this battle”
   - `Battler` or `BattlePokemon`
   - Adds: stat stages, volatile statuses (Substitute, confused, etc.), temporary form (mega, gmax, tera), position in field, etc.

Here we’ll focus on the **species class**, but will sketch related classes for context.

---

### 5.2 Support types/enums

First define lightweight enums and small value classes:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Set, Callable


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
    # (Add others as needed)


class Stat(Enum):
    HP = auto()
    ATTACK = auto()
    DEFENSE = auto()
    SP_ATTACK = auto()
    SP_DEFENSE = auto()
    SPEED = auto()


class GrowthRate(Enum):
    FAST = auto()
    MEDIUM_FAST = auto()
    MEDIUM_SLOW = auto()
    SLOW = auto()
    FLUCTUATING = auto()
    ERRATIC = auto()


class EggGroup(Enum):
    MONSTER = auto()
    WATER_1 = auto()
    BUG = auto()
    FLYING = auto()
    FIELD = auto()
    FAIRY = auto()
    GRASS = auto()
    HUMAN_LIKE = auto()
    WATER_3 = auto()
    MINERAL = auto()
    AMORPHOUS = auto()
    WATER_2 = auto()
    DITTO = auto()
    DRAGON = auto()
    UNDISCOVERED = auto()


class GenderRatio(Enum):
    GENDERLESS = auto()
    FEMALE_ONLY = auto()
    MALE_ONLY = auto()
    FEMALE_1_8 = auto()   # 12.5% female
    FEMALE_1_4 = auto()   # 25% female
    FEMALE_1_2 = auto()   # 50% female
    FEMALE_3_4 = auto()   # 75% female
    FEMALE_7_8 = auto()   # 87.5% female
```

A simple stats container:

```python
@dataclass(frozen=True)
class BaseStats:
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int

    def as_dict(self) -> Dict[Stat, int]:
        return {
            Stat.HP: self.hp,
            Stat.ATTACK: self.attack,
            Stat.DEFENSE: self.defense,
            Stat.SP_ATTACK: self.sp_attack,
            Stat.SP_DEFENSE: self.sp_defense,
            Stat.SPEED: self.speed,
        }
```

You’d similarly define:

- `Move` class
- `Ability` class
- `Item` class
- `StatusCondition` enum, etc.

---

### 5.3 Evolution data modeling

Encapsulate species-level evolution rules:

```python
class EvolutionTrigger(Enum):
    LEVEL = auto()
    ITEM_USE = auto()
    TRADE = auto()
    FRIENDSHIP = auto()
    FRIENDSHIP_TIME = auto()
    LOCATION = auto()
    MOVE_KNOWN = auto()
    STAT_COMPARISON = auto()
    GENDER = auto()
    OTHER = auto()  # For very special cases


@dataclass(frozen=True)
class EvolutionRule:
    target_species_id: str  # or int, depending on your ID system
    trigger: EvolutionTrigger
    min_level: Optional[int] = None
    item_required: Optional[str] = None       # Item id
    move_required: Optional[str] = None       # Move id
    min_friendship: Optional[int] = None
    time_of_day: Optional[str] = None         # 'day', 'night', etc.
    gender_required: Optional[str] = None     # 'male', 'female'
    location_required: Optional[str] = None
    extra_condition: Optional[Callable[..., bool]] = None
    # extra_condition can encode arbitrary conditions (e.g., walk 1000 steps, spin, etc.)
```

---

### 5.4 Form data modeling

A `PokemonSpecies` can have multiple forms.  
Each form can override type, base stats, abilities, etc.

```python
@dataclass
class SpeciesForm:
    form_id: str  # internal id, e.g. "default", "alola", "gmax", "mega"
    display_name: Optional[str] = None        # name shown in UI, if different
    types: Tuple[Type, Optional[Type]] = (Type.NORMAL, None)
    base_stats: BaseStats = field(default_factory=lambda: BaseStats(1,1,1,1,1,1))
    abilities: List[str] = field(default_factory=list)  # ability ids
    hidden_ability: Optional[str] = None
    weight_kg: float = 1.0
    height_m: float = 0.1
    is_default: bool = False
    is_mega: bool = False
    is_gmax: bool = False
    is_primal: bool = False
    # Other per-form flags (regional, battle-only, etc.)
```

---

### 5.5 The `PokemonSpecies` class

Now the main species template:

```python
@dataclass
class PokemonSpecies:
    species_id: str                # internal id, e.g. "garchomp"
    name: str                      # display name
    national_dex: int
    generation: int
    forms: Dict[str, SpeciesForm]  # key = form_id
    default_form_id: str

    # Classification
    is_legendary: bool = False
    is_mythical: bool = False
    is_ultra_beast: bool = False
    is_paradox: bool = False

    # Breeding
    egg_groups: Tuple[EggGroup, Optional[EggGroup]] = (EggGroup.FIELD, None)
    gender_ratio: GenderRatio = GenderRatio.FEMALE_1_2
    egg_cycles: int = 20  # base hatch time

    # Growth / capture / friendship
    growth_rate: GrowthRate = GrowthRate.MEDIUM_FAST
    base_experience_yield: int = 100
    catch_rate: int = 45
    base_friendship: int = 70

    # EV yield (on defeating this species)
    ev_yield: Dict[Stat, int] = field(default_factory=dict)

    # Evolution
    evolutions: List[EvolutionRule] = field(default_factory=list)
    pre_evolution_id: Optional[str] = None

    # Learnsets
    level_up_moves: Dict[int, List[str]] = field(default_factory=dict)  # level -> move ids
    tm_moves: Set[str] = field(default_factory=set)
    tutor_moves: Set[str] = field(default_factory=set)
    egg_moves: Set[str] = field(default_factory=set)
    event_moves: Set[str] = field(default_factory=set)

    # Special mechanics
    mega_stones: Dict[str, str] = field(default_factory=dict)
    # mega_stones: item_id -> mega_form_id
    gmax_available: bool = False
    # species-specific Z-moves: (move_id, z_item_id) -> z_move_id
    signature_z_moves: Dict[Tuple[str, str], str] = field(default_factory=dict)
```

---

### 5.6 Core methods for `PokemonSpecies`

#### Get a form

```python
    def get_default_form(self) -> SpeciesForm:
        return self.forms[self.default_form_id]

    def get_form(self, form_id: Optional[str] = None) -> SpeciesForm:
        if form_id is None:
            return self.get_default_form()
        return self.forms[form_id]
```

#### Check move learnability

```python
    def can_learn_move_by_level(self, move_id: str, gen: Optional[int] = None) -> bool:
        # gen argument can be used to filter by generation if needed
        for moves_at_level in self.level_up_moves.values():
            if move_id in moves_at_level:
                return True
        return False

    def can_learn_move_by_tm(self, move_id: str) -> bool:
        return move_id in self.tm_moves

    def can_learn_move_by_tutor(self, move_id: str) -> bool:
        return move_id in self.tutor_moves

    def can_learn_move_by_egg(self, move_id: str) -> bool:
        return move_id in self.egg_moves

    def can_learn_move(self, move_id: str) -> bool:
        return (
            self.can_learn_move_by_level(move_id)
            or self.can_learn_move_by_tm(move_id)
            or self.can_learn_move_by_tutor(move_id)
            or self.can_learn_move_by_egg(move_id)
            or move_id in self.event_moves
        )
```

#### Get abilities for a form

```python
    def get_abilities_for_form(self, form_id: Optional[str] = None) -> List[str]:
        form = self.get_form(form_id)
        return list(form.abilities)

    def get_hidden_ability_for_form(self, form_id: Optional[str] = None) -> Optional[str]:
        form = self.get_form(form_id)
        return form.hidden_ability
```

#### Stat calculation for an individual

This belongs logically to the individual Pokémon, but we can expose a helper here:

```python
    def calculate_stat(
        self,
        stat: Stat,
        level: int,
        iv: int,
        ev: int,
        nature_multiplier: float,
        form_id: Optional[str] = None,
    ) -> int:
        """Return the actual stat value given IV/EV/nature.
        nature_multiplier is 0.9, 1.0, or 1.1 for non-HP stats; 1.0 for HP.
        """
        form = self.get_form(form_id)
        base = form.base_stats.as_dict()[stat]

        if stat is Stat.HP:
            if base == 1:
                # Handle Shedinja-style species
                return 1
            return int(((2 * base + iv + ev // 4) * level) / 100) + level + 10
        else:
            return int(((((2 * base + iv + ev // 4) * level) / 100) + 5) * nature_multiplier)
```

#### Evolution queries

```python
    def get_evolution_options(self) -> List[EvolutionRule]:
        return list(self.evolutions)

    def can_evolve(
        self,
        level: int,
        friendship: int,
        held_item_id: Optional[str],
        move_ids: List[str],
        time_of_day: Optional[str],
        gender: Optional[str],
        location_id: Optional[str],
        extra_context: Dict = None,
    ) -> List[EvolutionRule]:
        """Return all evolution rules currently satisfied by an individual."""
        extra_context = extra_context or {}
        eligible = []

        for rule in self.evolutions:
            # Level requirement
            if rule.min_level is not None and level < rule.min_level:
                continue

            # Friendship
            if rule.min_friendship is not None and friendship < rule.min_friendship:
                continue

            # Item requirement (held vs used is context-dependent; this is simplified)
            if rule.item_required is not None and held_item_id != rule.item_required:
                continue

            # Move known
            if rule.move_required is not None and rule.move_required not in move_ids:
                continue

            # Time-of-day
            if rule.time_of_day is not None and time_of_day != rule.time_of_day:
                continue

            # Gender
            if rule.gender_required is not None and gender != rule.gender_required:
                continue

            # Location
            if rule.location_required is not None and location_id != rule.location_required:
                continue

            # Extra custom conditions
            if rule.extra_condition is not None and not rule.extra_condition(extra_context):
                continue

            eligible.append(rule)

        return eligible
```

#### Species-specific items & special mechanics

```python
    def get_mega_form_for_item(self, item_id: str) -> Optional[str]:
        """Return the form_id of the Mega form if this item is a valid Mega Stone."""
        return self.mega_stones.get(item_id)

    def has_gmax_form(self) -> bool:
        return self.gmax_available

    def get_signature_z_move(
        self,
        base_move_id: str,
        z_item_id: str,
    ) -> Optional[str]:
        return self.signature_z_moves.get((base_move_id, z_item_id))
```

---

### 5.7 Individual Pokémon class (brief sketch)

To connect species to an actual Pokémon:

```python
@dataclass
class Pokemon:
    species: PokemonSpecies
    form_id: Optional[str]
    level: int
    nature_id: str
    ivs: Dict[Stat, int]
    evs: Dict[Stat, int]
    ability_id: str
    moves: List[str]
    held_item_id: Optional[str]
    tera_type: Optional[Type] = None
    current_hp: Optional[int] = None
    status_condition: Optional[str] = None  # e.g., 'burn', 'paralysis', etc.

    def recalculate_stats(self, nature_multipliers: Dict[Stat, float]) -> Dict[Stat, int]:
        stats = {}
        for stat in Stat:
            mult = nature_multipliers.get(stat, 1.0)
            stats[stat] = self.species.calculate_stat(
                stat=stat,
                level=self.level,
                iv=self.ivs.get(stat, 0),
                ev=self.evs.get(stat, 0),
                nature_multiplier=mult,
                form_id=self.form_id,
            )
        # Initialize current HP if not set
        if self.current_hp is None:
            self.current_hp = stats[Stat.HP]
        return stats
```

A battle system would then wrap `Pokemon` into a `Battler` object that adds volatile states, turn-by-turn temporary effects, positions in the field (for doubles), Dynamax state, Terastallization, etc.

---

## 6. Summary

- A **Pokémon species** is the *static blueprint* that defines what any individual of that species *can* be and do.
- It controls:
  - Base stats, types, abilities
  - Learnable moves
  - Breeding, growth, evolution
  - Physical properties affecting moves
  - Forms, Megas, Gigantamax, Z-Moves, and Terastallization-related quirks
- The **individual Pokémon** adds the random and dynamic aspects (IVs, EVs, nature, current state).
- In Python OOP, you model this cleanly by:
  - A `PokemonSpecies` class holding all static/templated data
  - A `SpeciesForm` for form-specific overrides
  - Supporting classes/enums for moves, abilities, types, growth rate, etc.
  - A separate `Pokemon` class for an actual creature, referencing the species.

This architecture lets you faithfully represent the complex mechanics of Pokémon while keeping responsibilities clearly separated and code maintainable.