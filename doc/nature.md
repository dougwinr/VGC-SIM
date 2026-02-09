## 1. What is a Pokémon Nature?

A **Nature** is a hidden attribute each Pokémon has (introduced in Gen 3 and present in all later mainline games).  

It mainly does three things:

1. **Modifies stats** at a constant 10% bonus and 10% penalty:
   - Each non‑neutral nature **raises one stat by 10%** and **lowers another by 10%**.
   - Five “neutral” natures give **no stat change**.
   - HP is *never* affected by nature.

2. **Determines flavor preference** (for certain Berries / Pokéblocks / Poffins), indirectly affecting:
   - Contest stats in older gens (Cool, Beauty, etc.).
   - Berry-based mechanics where “likes” or “dislikes” matter.

3. **Persists as a permanent personality tag**:
   - It is part of what defines the Pokémon’s “identity” (like ID, Original Trainer, IVs, etc.).
   - Unlike EVs or items, it does not change normally (except via Mints’ stat effect, see below).

---

## 2. List of Natures and Their Effects

Natures affect **Attack (Atk)**, **Defense (Def)**, **Special Attack (SpA)**, **Special Defense (SpD)**, and **Speed (Spe)**.  

- **+10%** to one stat.
- **−10%** to another stat.
- Neutral ones affect nothing.

### 2.1 Stat Effects

| Nature   | +10% | −10% |
|----------|------|------|
| Hardy    | –    | –    |
| Lonely   | Atk  | Def  |
| Brave    | Atk  | Spe  |
| Adamant  | Atk  | SpA  |
| Naughty  | Atk  | SpD  |
| Bold     | Def  | Atk  |
| Docile   | –    | –    |
| Relaxed  | Def  | Spe  |
| Impish   | Def  | SpA  |
| Lax      | Def  | SpD  |
| Timid    | Spe  | Atk  |
| Hasty    | Spe  | Def  |
| Serious  | –    | –    |
| Jolly    | Spe  | SpA  |
| Naive    | Spe  | SpD  |
| Modest   | SpA  | Atk  |
| Mild     | SpA  | Def  |
| Quiet    | SpA  | Spe  |
| Bashful  | –    | –    |
| Rash     | SpA  | SpD  |
| Calm     | SpD  | Atk  |
| Gentle   | SpD  | Def  |
| Sassy    | SpD  | Spe  |
| Careful  | SpD  | SpA  |
| Quirky   | –    | –    |

Neutral natures: **Hardy, Docile, Serious, Bashful, Quirky**.

The multiplier used internally is:
- 1.1 for the boosted stat
- 0.9 for the reduced stat
- 1.0 for others (and for all stats in neutral natures)

---

### 2.2 Flavor Preferences

In many games, each nature also determines which Berry flavors a Pokémon:

- **Likes** → same stat that is **raised**
- **Dislikes** → same stat that is **lowered**

Mapping of stat ↔ flavor:

- **Atk → Spicy**
- **Def → Sour**
- **SpA → Dry**
- **SpD → Bitter**
- **Spe → Sweet**

Examples:
- **Adamant** (+Atk, −SpA)
  - Likes **Spicy**
  - Dislikes **Dry**
- **Bold** (+Def, −Atk)
  - Likes **Sour**
  - Dislikes **Spicy**
- **Neutral natures**: no strong like or dislike (flavors treated as neutral).

This influences:
- How much Contest Condition increases when you feed Pokéblocks/Poffins (Gen 3–4).
- Berry effects that depend on flavor preference (older systems).

---

## 3. How Natures Affect Stats (Formulas)

The nature modification is applied to the **final non-HP stats** after base stats, IVs, EVs, and level are taken into account.

Let:

- `Base` = base stat
- `IV` = individual value (0–31)
- `EV` = effort value (0–252, used in multiples of 4)
- `L` = level
- `N` = nature modifier (1.1, 1.0, or 0.9)

### 3.1 HP Formula (never affected by nature)

```text
HP = floor( ((2 * Base + IV + floor(EV / 4)) * L) / 100 ) + L + 10
```

### 3.2 Other Stats (Attack, Defense, SpA, SpD, Speed)

```text
Raw = floor( ((2 * Base + IV + floor(EV / 4)) * L) / 100 ) + 5
Stat = floor( Raw * N )
```

Where `N` is:
- 1.1 if the Pokémon’s nature boosts this stat
- 0.9 if the nature lowers this stat
- 1.0 otherwise

Nature is part of the **permanent stats shown on the summary screen**. There is no per-battle change; it’s baked into the displayed numbers.

---

## 4. How You Get / Change Natures

### 4.1 When a Pokémon is Generated

A nature is chosen when a Pokémon is first created:

- **Wild encounter**
- **Egg hatching**
- **In-game gift**
- **Event distribution**

By default, it’s random (uniform across the 25 natures), **except** when other mechanics influence it.

### 4.2 Synchronize Ability

Ability **Synchronize** can influence nature when the Pokémon with Synchronize is in the lead slot.

- **Gen 3–7**:
  - Wild Pokémon: **50% chance** to have the same nature as the lead with Synchronize.
  - Otherwise, nature is random.
- **Gen 8 (Sword/Shield)**:
  - Wild Pokémon: effectively **guaranteed** to have the same nature as the lead with Synchronize (with some edge-case exceptions like certain gifts).
- **Gen 9 (Scarlet/Violet)**:
  - Synchronize **no longer affects nature** of wild Pokémon (it still synchronizes status in battle, as usual).

### 4.3 Breeding & Everstone

When breeding:

- Without items: the child’s nature is random.
- With **Everstone**:
  - If a parent holds Everstone, the offspring **inherits that parent’s nature**.
  - Since Gen 6, this is essentially **100%** guaranteed (Gen 3–5 had slightly different odds but same idea).
  - Works with Ditto as well.

**Important with Mints (see below):** Everstone uses the Pokémon’s **true nature**, not its Mint-modified stat behavior.

---

## 5. Nature Mints (Gen 8+)

**Mints** are items that **change the way stats are calculated** as if the Pokémon had a specific nature, **without changing the Pokémon’s stored nature value**.

Example:
- A Pikachu with **Bold** nature uses a **Timid Mint**.
- In the summary screen, it may:
  - Still *say* “Bold” as the nature (depending on game UI).
  - But its **actual stats behave as if it were Timid** (+Spe, −Atk) for all stat calculations.

Important subtlety:

- The **underlying nature** (for:
  - flavor preferences,
  - Everstone inheritance,
  - “nature” shown in some UIs)
  remains the original one.
- The **effective nature for stats** becomes the Mint nature.

In code / modeling terms, you can think of a Pokémon having:

- `true_nature`: original nature assigned on creation
- `stat_nature`: effective nature used for stat multipliers (either same as true_nature, or overwritten by Mint)

---

## 6. Interactions With Other Systems

### 6.1 Abilities

Natures do **not** directly interact with abilities as special rules, but they influence **stats**, which many abilities reference.

Examples:

- **Beast Boost** (Nihilego, etc.):  
  Raises the **highest stat** after KOing a Pokémon.  
  Nature affects which stat ends up highest, so it can determine what gets boosted.

- **Download** (Porygon line):  
  Compares opponent’s **Def** and **SpD** to choose which offensive stat to raise (Atk or SpA).  
  Opponent’s nature modifies those stats, affecting Download’s choice.

- **Protosynthesis / Quark Drive** (Gen 9):  
  Boost the user’s **highest stat** (other than HP) in sun / Electric Terrain with Booster Energy, etc.  
  Nature again may change what the highest stat is.

- **Contrary, Simple, Huge Power, etc.**:
  These modify **stat stages or base stats**, but the nature multiplier is always there on top.

There is no special ability that directly says “this interacts with Natures”; all interaction is via **stat values**.

---

### 6.2 Items

Most items just act on stats or conditions; natures indirectly affect how useful items are.

- **Choice Band / Specs / Scarf**:
  - Boost Atk / SpA / Spe respectively.
  - Natures like **Adamant** (Atk+) or **Timid** (Spe+) stack multiplicatively for more impact.
- **Assault Vest**:
  - Increases SpD, so natures like **Calm / Careful** can maximize that.
- **Mints** (already covered) directly change effective nature for stat calculations.
- Berries that care about flavors / contest mechanics may be influenced by nature’s flavor preference.

Again, there is no item that “reads the nature” directly beyond Mints; items mostly operate on stats, which natures alter.

---

### 6.3 Moves

Natures interact with moves **indirectly through stats**.

- Any move using **Atk/Def/SpA/SpD/Spe** is affected:
  - **Physical moves** → depend on Atk and target’s Def.
  - **Special moves** → depend on SpA and target’s SpD.
  - **Speed** → determines turn order (ignoring priority).
- Moves like **Psyshock / Psystrike**:
  - Use SpA vs target’s **Def**, so both attacker’s SpA nature and defender’s Def nature matter.

Other interesting examples:

- **Foul Play**:  
  Uses the **target’s Atk** stat for damage → target’s nature matters.

- **Trick Room**:  
  Reverses turn order based on Speed; nature heavily affects which Pokémon function better or worse in Trick Room.

- **Confusion** self-hit:  
  Uses the target’s **own Atk vs Def** stats; nature changes both.

There is a move called **Nature Power**, but it has nothing to do with Natures; it just changes the move it becomes based on terrain/battle location.

---

### 6.4 Battle Mechanics: Mega, Dynamax, Z-Moves, Terastal

- **Mega Evolution**:
  - Nature does not change upon Mega evolving.
  - The base stats change, but **the same nature multiplier** applies to the evolved stats.

- **Dynamax**:
  - HP is multiplied; other stats remain the same.
  - Nature’s effect on Atk/Def/SpA/SpD/Spe is unchanged.

- **Z-Moves**:
  - Use the underlying move’s category (physical/special).
  - Damage scaling uses the user’s Atk or SpA → nature applies as usual.

- **Terastal (Tera)**:
  - Changes type and boosts certain same-type moves.
  - Nature still affects Atk/SpA (for damage) and Spe (turn order), as normal.

So **none of these mechanics override or bypass nature**; they all work on the already nature-modified stats.

---

### 6.5 Status Conditions

Status conditions modify stats multiplicatively; nature is one multiplicative factor among others.

Example (simplified):

- **Burn** (without Guts, etc.):
  - Halves **Attack** for physical moves.
- **Paralysis**:
  - Reduces **Speed** (to 25% in early gens, 50% in recent gens).

Order conceptually:
1. Compute base stat (Base+IV+EV+Level).
2. Apply **Nature** modifier.
3. Apply **status** modifier (Burn, Paralysis, etc.).
4. Apply other field/ability modifiers.

So both nature and status conditions combine multiplicatively.

---

### 6.6 Single vs Double Battles

Mechanically, **natures work identically** in Singles and Doubles.

Differences are **strategic**, not mechanical:

- Singles often prioritize:
  - Maximum offensive power or specific defensive spreads.
  - Natures like **Jolly / Timid / Adamant / Modest** for sweeping.
- Doubles often emphasize:
  - Speed control (Trick Room, Tailwind, Icy Wind, etc.).
  - Bulk, so natures like **Calm / Careful / Bold** appear more.
  - Synergy (e.g., making your special attacker bulky enough to survive certain spread moves).

But the underlying formula and implementation of nature is the same.

---

## 7. What Natures Do **Not** Affect

Natures **do not** influence:

- HP
- Accuracy / Evasion
- Critical hit rates
- Move priority
- IVs / EVs themselves
- Shiny odds
- Hidden Power type/power (older gens)
- Characteristic text (“Likes to thrash about” etc. – that’s based on highest IV, not nature)

They only affect:
- Non-HP stats (Atk / Def / SpA / SpD / Spe) through a fixed multiplier
- Flavor preference and some associated side mechanics

---

## 8. Object-Oriented Modeling in Python

### 8.1 Design Goals

We want a **Nature** model that:

1. Encodes all 25 natures.
2. Knows:
   - Which stat it increases
   - Which stat it decreases
   - Stat multipliers
   - Flavor preferences
3. Can:
   - Provide the multiplier for a given stat.
   - Apply itself to a stat or to a full stat dictionary.
4. Works nicely inside a larger `Pokemon` model (with IVs, EVs, etc.).
5. Optionally supports **Mint** behavior via “effective nature”.

We’ll model:

- `Stat` as an Enum.
- `Flavor` as an Enum.
- `Nature` as an Enum with per-member data and behaviors.
- A minimal `Pokemon` class to show how Nature is actually used.

---

### 8.2 Enums for Stat and Flavor

```python
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class Stat(Enum):
    HP   = "hp"
    ATK  = "atk"
    DEF  = "def"
    SPA  = "spa"
    SPD  = "spd"
    SPE  = "spe"


class Flavor(Enum):
    SPICY  = "spicy"
    DRY    = "dry"
    SWEET  = "sweet"
    BITTER = "bitter"
    SOUR   = "sour"
```

Mapping from stat → flavor:

```python
STAT_TO_FLAVOR: Dict[Stat, Flavor] = {
    Stat.ATK: Flavor.SPICY,
    Stat.DEF: Flavor.SOUR,
    Stat.SPA: Flavor.DRY,
    Stat.SPD: Flavor.BITTER,
    Stat.SPE: Flavor.SWEET,
    # HP has no flavor mapping
}
```

---

### 8.3 Nature Enum With Behavior

We use an `Enum` because the set of natures is finite and known.  
Each member stores:

- `label`: human-readable name
- `increased`: boosted stat (or `None` for neutral)
- `decreased`: lowered stat (or `None` for neutral)

```python
class Nature(Enum):
    # name       label     increased     decreased
    HARDY   = ("Hardy",    None,         None)
    LONELY  = ("Lonely",   Stat.ATK,     Stat.DEF)
    BRAVE   = ("Brave",    Stat.ATK,     Stat.SPE)
    ADAMANT = ("Adamant",  Stat.ATK,     Stat.SPA)
    NAUGHTY = ("Naughty",  Stat.ATK,     Stat.SPD)

    BOLD    = ("Bold",     Stat.DEF,     Stat.ATK)
    DOCILE  = ("Docile",   None,         None)
    RELAXED = ("Relaxed",  Stat.DEF,     Stat.SPE)
    IMPISH  = ("Impish",   Stat.DEF,     Stat.SPA)
    LAX     = ("Lax",      Stat.DEF,     Stat.SPD)

    TIMID   = ("Timid",    Stat.SPE,     Stat.ATK)
    HASTY   = ("Hasty",    Stat.SPE,     Stat.DEF)
    SERIOUS = ("Serious",  None,         None)
    JOLLY   = ("Jolly",    Stat.SPE,     Stat.SPA)
    NAIVE   = ("Naive",    Stat.SPE,     Stat.SPD)

    MODEST  = ("Modest",   Stat.SPA,     Stat.ATK)
    MILD    = ("Mild",     Stat.SPA,     Stat.DEF)
    QUIET   = ("Quiet",    Stat.SPA,     Stat.SPE)
    BASHFUL = ("Bashful",  None,         None)
    RASH    = ("Rash",     Stat.SPA,     Stat.SPD)

    CALM    = ("Calm",     Stat.SPD,     Stat.ATK)
    GENTLE  = ("Gentle",   Stat.SPD,     Stat.DEF)
    SASSY   = ("Sassy",    Stat.SPD,     Stat.SPE)
    CAREFUL = ("Careful",  Stat.SPD,     Stat.SPA)
    QUIRKY  = ("Quirky",   None,         None)

    def __init__(
        self,
        label: str,
        increased: Optional[Stat],
        decreased: Optional[Stat],
    ) -> None:
        self.label = label
        self.increased = increased
        self.decreased = decreased

    # ---------- Core behavior ----------

    def modifier_for(self, stat: Stat) -> float:
        """Return the multiplier this nature applies to a given stat."""
        if stat == Stat.HP:
            return 1.0
        if self.increased is not None and stat == self.increased:
            return 1.1
        if self.decreased is not None and stat == self.decreased:
            return 0.9
        return 1.0

    def apply_to_stat(self, stat: Stat, base_value: int) -> int:
        """Return the integer stat after applying nature modifier."""
        mult = self.modifier_for(stat)
        # In games, this is floor of (Raw * mult)
        return int(base_value * mult // 1)

    def apply_to_all_stats(self, stats: Dict[Stat, int]) -> Dict[Stat, int]:
        """
        Given a dictionary of stats (already computed from base, IV, EV, level),
        return a new dictionary with this nature applied.
        """
        return {
            stat: self.apply_to_stat(stat, value)
            for stat, value in stats.items()
        }

    # ---------- Flavor preferences ----------

    @property
    def liked_flavor(self) -> Optional[Flavor]:
        """
        Flavor corresponding to the boosted stat, or None for neutral natures.
        """
        if self.increased is None:
            return None
        return STAT_TO_FLAVOR.get(self.increased)

    @property
    def disliked_flavor(self) -> Optional[Flavor]:
        """
        Flavor corresponding to the lowered stat, or None for neutral natures.
        """
        if self.decreased is None:
            return None
        return STAT_TO_FLAVOR.get(self.decreased)

    # ---------- Helpers ----------

    @classmethod
    def from_name(cls, name: str) -> "Nature":
        """
        Get a Nature by English name, case-insensitive.
        Raises KeyError if not found.
        """
        normalized = name.strip().upper()
        for nature in cls:
            if nature.label.upper() == normalized or nature.name == normalized:
                return nature
        raise KeyError(f"Unknown nature: {name}")
```

Usage example:

```python
adamant = Nature.ADAMANT
print(adamant.increased, adamant.decreased)  # Stat.ATK Stat.SPA
print(adamant.modifier_for(Stat.ATK))  # 1.1
print(adamant.modifier_for(Stat.SPA))  # 0.9
print(adamant.liked_flavor)           # Flavor.SPICY
print(adamant.disliked_flavor)        # Flavor.DRY
```

---

### 8.4 Minimal Pokémon Class Using Nature

Now we define a simple `Pokemon` class that uses:

- `base_stats`
- `ivs`
- `evs`
- `level`
- `true_nature` (original nature)
- `mint_nature` (optional; if set, overrides stats behavior)

```python
@dataclass
class Pokemon:
    species_name: str
    level: int
    base_stats: Dict[Stat, int]  # base stats per stat
    ivs: Dict[Stat, int]
    evs: Dict[Stat, int]

    true_nature: Nature
    mint_nature: Optional[Nature] = None  # None if no Mint used

    @property
    def effective_nature(self) -> Nature:
        """
        Nature used for stat calculations (Mint-aware).
        """
        return self.mint_nature or self.true_nature

    def _raw_stat(self, stat: Stat) -> int:
        """
        Compute the stat before applying nature.
        (Equivalent to 'Raw' in the formula description above.)
        """
        base = self.base_stats[stat]
        iv = self.ivs.get(stat, 0)
        ev = self.evs.get(stat, 0)
        L = self.level

        if stat == Stat.HP:
            if base == 1:
                # Edge case like Shedinja remains 1 HP
                return 1
            return ((2 * base + iv + (ev // 4)) * L) // 100 + L + 10
        else:
            return ((2 * base + iv + (ev // 4)) * L) // 100 + 5

    def stat(self, stat: Stat) -> int:
        """
        Full effective stat, including nature (but not in-battle modifiers like burn).
        """
        raw = self._raw_stat(stat)

        if stat == Stat.HP:
            return raw

        nature = self.effective_nature
        mult = nature.modifier_for(stat)
        return int(raw * mult // 1)

    def all_stats(self) -> Dict[Stat, int]:
        """
        Compute all six stats with nature applied.
        """
        return {stat: self.stat(stat) for stat in Stat}
```

Example usage:

```python
# Example: Garchomp-like stats
garchomp_base = {
    Stat.HP: 108,
    Stat.ATK: 130,
    Stat.DEF: 95,
    Stat.SPA: 80,
    Stat.SPD: 85,
    Stat.SPE: 102,
}

garchomp_ivs = {stat: 31 for stat in Stat}
garchomp_evs = {
    Stat.HP: 0,
    Stat.ATK: 252,
    Stat.DEF: 0,
    Stat.SPA: 0,
    Stat.SPD: 4,
    Stat.SPE: 252,
}

chomp = Pokemon(
    species_name="Garchomp",
    level=100,
    base_stats=garchomp_base,
    ivs=garchomp_ivs,
    evs=garchomp_evs,
    true_nature=Nature.ADAMANT,
)

print(chomp.stat(Stat.ATK))  # Atk with Adamant nature
print(chomp.stat(Stat.SPA))  # SpA with nature penalty
```

If the Pokémon uses a **Mint** (e.g., Timid Mint), you just set:

```python
chomp.mint_nature = Nature.TIMID
```

Now `chomp.effective_nature` becomes Timid, and all stats recalc with Timid’s modifiers instead of Adamant’s, while `true_nature` remains Adamant for breeding, flavor, etc.

---

### 8.5 Extending the Model

To integrate more of the system:

- **Abilities**:
  - Add an `Ability` object and have it read stats computed via nature.
- **Items**:
  - Add an `Item` system where items can further multiply stats or override behavior.
- **Battle system**:
  - Separate “display stats” (base + IV + EV + nature) from “effective in-battle stats” (with statuses, items, field effects).
- **Persistence**:
  - Store nature by name (e.g., `"Adamant"`) and convert to the `Nature` enum via `Nature.from_name`.

The key idea: **Nature is a pure, stat-multiplying trait** with immutable data and simple methods that plug cleanly into any larger battle/stat calculation system.

---

If you want, I can extend this with:

- A full example of a battle damage calculation that explicitly uses nature.
- A more elaborate `Pokemon` model including moves, abilities, and items.