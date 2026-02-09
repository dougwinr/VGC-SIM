## 1. What is an Item in Pokémon?

In the main series Pokémon games, an **item** is any object that can be:

- Held by a Pokémon  
- Used by the player (in battle or on the field)  
- Required for a mechanic (Mega Evolution, Z-Moves, evolving, etc.)  
- Used as a resource or collectible (money items, fossils, etc.)

From the game-engine point of view, an item is a **data-driven effect** that can:

- Modify stats or damage  
- Cure or inflict conditions  
- Change forms, types, moves, or mechanics  
- Interact with other systems (abilities, moves, field states…)

---

## 2. Main Categories of Items

### 2.1. Held Items

Items that a Pokémon can hold. A Pokémon can usually hold **exactly one** item.

Typical behaviors:

- **Passive effects**: e.g. Leftovers (recover HP every turn), Choice Band (boost Attack but lock move).
- **Triggered effects / consumables**: e.g. Berries (heal HP, cure status), Focus Sash (leave 1 HP).

Held items are central to battle strategies and have the strongest interactions with abilities/moves.

---

### 2.2. Usable (Bag) Items

Items you use from the **bag**:

- In-battle: Potions, Revives, X Attack, etc. (usually banned in competitive formats).
- Out-of-battle (field): Escape Rope, Repel, stat-changing items like mints, etc.

Many are **single-use** and do not need to be “held” by a Pokémon.

---

### 2.3. Key Items

Special items that:

- Are not consumed.
- Are not held.
- Unlock systems (Fishing Rods, Bikes, Tera Orb, etc.).
- Often represent persistent **player abilities** rather than Pokémon abilities.

From a modeling standpoint, they are usually separate from the battle-focused item system.

---

### 2.4. Special Categories

- **Evolution items**: Stones (Fire Stone), special items (Razor Claw, King’s Rock), sometimes used while held during trade or level-up.
- **Form / type items**: Plates, Drives, Memories, Orbs (for Giratina, Kyogre, Groudon), etc.
- **Berries**: Technically held items or consumables, with many battle/out-of-battle effects.
- **Battle facility / money / fossils / collectibles**: Often not used in battle but important for economy and progression.

---

## 3. What Items Can Do (Functional Types)

Below is a functional overview of what items can do in the system, regardless of specific names.

### 3.1. HP & Status Management

**In battle:**

- Heal HP by a **fixed amount** or **percentage** (Berries, Potions).
- Restore **PP** (Ether, Elixir).
- Cure **status conditions** (Antidote, Full Heal, Lum Berry).
- Trigger healing under conditions:
  - HP threshold (Sitrus Berry, pinch berries).
  - Weather/terrain, etc. (e.g. certain berries).
- Keep the Pokémon alive:
  - Focus Sash (survive a KO from full HP).
  - Focus Band (chance to survive).

**Out of battle:**

- Same as above, but outside battles.
- Might have different rules (e.g. can’t revive fainted Pokémon in certain modes).

### 3.2. Stat & Damage Modifiers

Items can affect **stats** (Attack, Defense, Sp. Atk, Sp. Def, Speed, Accuracy, Evasion) and **damage**:

- **Flat multipliers**:
  - Choice Band/Specs/Scarf: Attack/Sp. Atk/Speed ×1.5, but locks the move.
  - Life Orb: multiplies damage, but damages holder.
  - Type boosters: Mystic Water (Water-type moves), Plates, Expert Belt, etc.

- **Conditional multipliers**:
  - Weakness Policy: boosts stats when hit by super effective move.
  - Assault Vest: boosts Sp. Def but prevents status moves.
  - Muscle Band/Wise Glasses: boost physical/special moves slightly.
  - Terrain Extender, Light Clay: extend duration of terrain/screens.

- **In-battle stat stage changes**:
  - X Attack, X Defense, etc. used from bag.
  - Some items indirectly cause boosts via triggered ability interactions.

### 3.3. Speed & Turn Order

Items can change **move order**:

- **Priority influence**:
  - Quick Claw: chance to move first.
  - Custap Berry: move first in pinch (in some generations).
- **Speed manipulation**:
  - Iron Ball: halves Speed.
  - Lagging Tail/Full Incense: forces last move.
  - Choice Scarf: Speed ×1.5.
  - Room Service: lowers Speed when Trick Room active.

### 3.4. Accuracy, Crit Rate, and Accuracy Interactions

- **Accuracy**:
  - Wide Lens (boosts accuracy).
  - Zoom Lens (boosts accuracy if moving after target).
- **Critical hits**:
  - Scope Lens, Razor Claw: increase crit chance.
  - Items that boost crit moves indirectly.

### 3.5. Type & Form Manipulation

- **Type boosters** (e.g. Charcoal, Magnet).
- **Move-type defining**:
  - Hidden Power used IVs (no item), but example of data-based typing.
  - Natural Gift uses berry to give type + power.
- **Form-changing items**:
  - Plates/Drives/Memories for Arceus, Genesect, Silvally.
  - Orbs (Griseous, Red/Blue) for Primal/Giratina forms (older gens).
  - Some items change forms only when held.

### 3.6. Status Infliction & Defense

- **Inflict status on holder** (to synergize with abilities):
  - Flame Orb (burn).
  - Toxic Orb (badly poison).
- **Protect from status / secondary effects**:
  - Safety Goggles (immune to powder moves and weather damage).
  - Covert Cloak (blocks secondary effects).
  - Heavy-Duty Boots (ignores entry hazards).
  - Clear Amulet (prevents stat drops).
  - Protective Pads (avoid contact side effects).

### 3.7. EV & Long-term Stat Items

Out-of-battle items that affect **EVs / training**:

- **Vitamins**: increase EVs (HP Up, Protein, etc.).
- **Feathers / Wings**: smaller EV boosts.
- **EV-reducing berries**.
- **Mints**: change **nature effect** (stats) without changing actual nature string.

These don’t affect a single battle directly; they affect the Pokémon’s long-term stats.

### 3.8. Evolution Items

- **Stones**: Fire, Water, Leaf, etc.
- **Special items**:
  - Held during trade (e.g. Metal Coat for Scizor).
  - Used directly (e.g. linking cords in Legends Arceus-type games).
  - Level-up while holding (Razor Fang, Oval Stone, etc.).

Evolution items interact with level-up logic, trade logic, and species data.

### 3.9. Battle-Specific Utility Items

- **Z-Crystals**: allow Z-Moves once per battle (Gen 7 only).
- **Mega Stones**: allow Mega Evolution once per battle (Gen 6–7).
- **Dynamax-related** (Gen 8):
  - Dynamax Candy (increase Dynamax Level).
- **Terastal-related** (Gen 9):
  - Tera Shards, Tera Orb (not held by Pokémon but key-mechanic items).
- **Misc**:
  - Eject Button / Eject Pack / Red Card: force switching on certain triggers.
  - Rocky Helmet: damage on contact.
  - Weakness Policy, Adrenaline Orb, etc.

---

## 4. Single vs Double Battles: Item Behavior

### 4.1. General Rules

- Each Pokémon uses its own held item independently.
- Items often check **local context**: ally, foe, move type, target, field state (weather, terrain).
- Most items behave **identically** in singles/doubles; the difference is how many Pokémon they can affect.

### 4.2. Spread Moves and Item Interactions

- Damage boosters (Life Orb, Choice items) apply to each hit; in doubles, many moves have reduced power vs multiple targets.
- Items like **Rocky Helmet** trigger once per contact per holder.
- Berries that trigger on HP threshold can trigger simultaneously on multiple Pokémon.

### 4.3. Ally Interactions

- Items can interact with **Allies**:
  - Healing items like Sitrus Berry only affect the holder.
  - Some items make the holder more useful as support (e.g. Light Clay for screens).
- Moves like **Trick / Switcheroo / Bestow** can move items between allies and foes in doubles.

---

## 5. Interactions with Core Systems

### 5.1. With Pokémon Stats & Damage

In the damage formula, items enter as **multiplicative modifiers** or **preconditions**:

- Attack / Defense multipliers (Choice Band, Assault Vest).
- Move power multipliers (Life Orb, type boosters).
- Special conditions (Expert Belt boosts super-effective hits, Metronome boosts repeated use).

Items can also:

- Affect **HP** directly (healing/HP loss).
- Affect stat **stages** (X items, Weakness Policy).
- Influence **critical chance**, **accuracy**, and **speed** which feed into hit chance and turn order.

### 5.2. With Types

- Boost same-type moves (STAB amplifiers like type-specific items).
- Change form and thus type (Plates/Memories).
- Influence type-based mechanics:
  - Items that interact with specific types (e.g. Black Glasses for Dark moves).

### 5.3. With Status Conditions

- Cure or prevent status (berries, Full Heal).
- Self-inflict status (orbs).
- Change how status interacts with stats:
  - Flame Orb + Guts, Toxic Orb + Poison Heal, etc.
- Some items protect from powder moves, weather, hazard damage.

---

## 6. Interactions with Abilities

A non-exhaustive list of important ability–item interactions:

- **Klutz**: Holder ignores effects of most held items (but still “counts” as holding them).
- **Unnerve**: Prevents opposing Pokémon from eating berries.
- **Harvest**: Can regrow and reuse a consumed berry.
- **Pickup**: After battle or when an item is used, Pokémon may obtain items.
- **Frisk**: Reveals the opponent’s held items.
- **Sticky Hold**: Prevents removal/stealing of held item.
- **Magician / Pickpocket**: Steal held items when damaging or being hit.
- **Gluttony**: Makes berries trigger at higher HP %.
- **Unburden**: Doubles Speed when item is consumed or lost.
- **Cheek Pouch**: Additional healing when eating a berry.
- **Healer-like effects**: Some abilities combine with healing items for strong sustain.
- **Multitype / RKS System**: Change the type of specific legendary Pokémon based on held item (Plates / Memories).

Your design must allow items to **register hooks** that abilities can also hook into, so the engine can process interactions in the right order.

---

## 7. Interactions with Moves

Key move–item interactions:

- **Knock Off**: Removes target’s item and deals extra damage if target had an item.
- **Trick / Switcheroo**: Swap items between user and target.
- **Thief / Covet**: Steal the target’s item.
- **Fling**: Throw held item; power & effect depend on the item.
- **Pluck / Bug Bite**: Eat target’s berry and gain its effect.
- **Recycle**: Restore the last consumed item.
- **Embargo / Magic Room**:
  - Embargo: prevent specific Pokémon from using its item.
  - Magic Room: disable all held items temporarily.
- **Corrosive Gas**: Remove items (melt them).
- **Belch**: Requires the user to have eaten a berry.
- **Poltergeist**: Fails if target has no item.

Moves can:

- Check if an item exists, and what type.
- Change or destroy items.
- Trigger item effects indirectly.

Your model should reflect this with methods like `can_be_removed`, `can_be_tricked`, `on_fling`, etc.

---

## 8. Interactions with Special Mechanics

### 8.1. Mega Evolution (Gen 6–7)

- Requires a **Mega Stone** held by the Pokémon.
- Once per battle, a Pokémon holding its Mega Stone can Mega Evolve.
- Mega Stones usually:
  - Cannot be removed by Trick/Knock Off.
  - Block holding other items (you can only hold the stone).

### 8.2. Z-Moves (Gen 7)

- Require a **Z-Crystal** held by the Pokémon and a Z-Ring for the Trainer.
- Z-Crystals:
  - Usually cannot be removed via Trick/Knock Off.
  - Restrict items similarly to Mega Stones (you can’t hold two items).
  - Are not consumed; they enable one Z-Move per battle.

### 8.3. Dynamax / Gigantamax (Gen 8)

- Dynamax is triggered via Trainer’s Dynamax Band, not held items.
- Some items interact with Dynamax indirectly (e.g., items that boost HP or damage).
- **Dynamax Candy** modifies a Pokémon’s “Dynamax Level”, changing HP gained when Dynamaxed (out-of-battle item).

### 8.4. Terastalize (Gen 9)

- Triggered via **Tera Orb** (Trainer key item).
- Items like **Tera Shards** are used to change Tera Type (not held in battle).
- Some held items (e.g., Mirror Herb, Covert Cloak, Booster Energy, etc.) are just normal held items but play important roles in Tera metagame.

---

## 9. Edge Cases & Exceptions

To model items accurately, your design must handle:

- **Species-locked items**:
  - Items that only work on certain species or can’t be removed from them.
- **Irremovable items**:
  - Mega Stones, Z-Crystals, some form items, etc.
- **Items that hurt their holder** (Life Orb, Black Sludge on non-Poison types).
- **Items suppressed by field effects**:
  - Magic Room, Embargo.
- **Multi-use vs single-use**:
  - Berries consumed once.
  - Leftovers stay.
  - Recycle, Harvest can re-use.

---

## 10. Object-Oriented Modeling in Python

Below is a **high-level OOP model** tailored to Pokémon items, emphasizing extensibility and clarity rather than full game engine fidelity.

### 10.1. Design Goals

- Represent all relevant properties of items.
- Allow **event-based** effects:
  - On turn start/end, on taking damage, on using a move, etc.
- Differentiate **held**, **usable**, and **key** items.
- Allow **exceptions** (irremovable items, species-only, etc.).
- Pass a **context object** with references to:
  - `battle`, `user`, `target`, `move`, `ability`, `field`, `weather`, etc.

---

### 10.2. Core Interfaces and Base Classes

```python
from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Protocol


# --- Context Types ---

@dataclass
class BattleContext:
    battle: Any           # reference to battle engine
    user: Any             # Pokémon object holding/using the item
    target: Optional[Any] = None
    move: Optional[Any] = None
    damage: Optional[int] = None
    hit_result: Optional[Any] = None
    field: Optional[Any] = None
    weather: Optional[Any] = None
    terrain: Optional[Any] = None
    is_double_battle: bool = False
    side: Optional[Any] = None   # user side
    foe_side: Optional[Any] = None


# --- Base Item ---

@dataclass
class Item(ABC):
    """
    Base item definition. Most gameplay items inherit from this.
    """
    id: str                      # internal ID
    name: str                    # display name
    description: str
    category: str                # 'held', 'consumable', 'key', etc.
    battle_usable: bool = False
    field_usable: bool = False
    consumable: bool = False     # if True, item is removed after use
    max_stack: int = 99          # bag stack limit
    removable: bool = True       # can be removed by moves like Knock Off
    tradeable: bool = True       # can be traded
    species_locks: List[str] = field(default_factory=list)  # species that can use / must hold
    flags: Dict[str, Any] = field(default_factory=dict)     # for custom metadata

    # --- General use methods (bag use, not held effect) ---

    def can_use_in_battle(self, ctx: BattleContext) -> bool:
        return self.battle_usable

    def can_use_in_field(self, ctx: BattleContext) -> bool:
        return self.field_usable

    def use_in_battle(self, ctx: BattleContext) -> bool:
        """
        Execute effect when used from the bag in battle.
        Return True if the item is consumed.
        """
        if not self.can_use_in_battle(ctx):
            return False
        return self._apply_battle_use(ctx)

    def use_in_field(self, ctx: BattleContext) -> bool:
        """
        Execute effect when used from the bag on the field.
        Return True if the item is consumed.
        """
        if not self.can_use_in_field(ctx):
            return False
        return self._apply_field_use(ctx)

    @abstractmethod
    def _apply_battle_use(self, ctx: BattleContext) -> bool:
        ...

    @abstractmethod
    def _apply_field_use(self, ctx: BattleContext) -> bool:
        ...


# --- Held Item Base ---

@dataclass
class HeldItem(Item):
    category: str = field(init=False, default='held')
    battle_usable: bool = field(init=False, default=False)
    field_usable: bool = field(init=False, default=False)

    # Hooks: engine calls these at appropriate times.

    # When Pokémon enters battle
    def on_switch_in(self, ctx: BattleContext) -> None:
        pass

    # Before the Pokémon chooses a move (e.g., Choice items locking)
    def on_before_move_selection(self, ctx: BattleContext) -> None:
        pass

    # When calculating move base power
    def on_base_power(self, ctx: BattleContext) -> float:
        # return multiplier (1.0 = no change)
        return 1.0

    # When calculating final damage
    def on_damage_mod(self, ctx: BattleContext) -> float:
        return 1.0

    # Before move is executed (can cancel or modify)
    def on_before_move(self, ctx: BattleContext) -> None:
        pass

    # After move is used
    def on_after_move(self, ctx: BattleContext) -> None:
        pass

    # After taking damage
    def on_after_damage_taken(self, ctx: BattleContext) -> None:
        pass

    # End of turn effects (Leftovers, etc.)
    def on_end_of_turn(self, ctx: BattleContext) -> None:
        pass

    # When status changes
    def on_status_change(self, ctx: BattleContext) -> None:
        pass

    # Called when something tries to remove/steal the item
    def can_be_removed(self, ctx: BattleContext) -> bool:
        return self.removable

    # Fling integration
    def on_fling_power(self) -> int:
        """Base power when flung. 0 = cannot be flung."""
        return 0

    def on_fling_effect(self, ctx: BattleContext) -> None:
        """Extra effect when flung (e.g., status, stat change)."""
        pass

    # For Trick/Switcheroo restrictions
    def can_be_tricked(self, ctx: BattleContext) -> bool:
        return self.removable and self.tradeable
```

This base design lets you implement any held item by overriding relevant hooks.

---

### 10.3. Example: Sitrus Berry (Simple Consumable Held Item)

```python
@dataclass
class SitrusBerry(HeldItem):
    id: str = "sitrus_berry"
    name: str = "Sitrus Berry"
    description: str = "Restores HP when the holder's HP is low."
    consumable: bool = True
    removable: bool = True
    tradeable: bool = True

    def _apply_battle_use(self, ctx: BattleContext) -> bool:
        # Sitrus Berry is not used from bag in battle in main games
        return False

    def _apply_field_use(self, ctx: BattleContext) -> bool:
        # You could allow manual feeding / EV logic here if desired
        user = ctx.user
        if user.is_fainted():
            return False
        healed = user.heal_fraction(0.25)  # example: 25% max HP
        return healed > 0  # consumed if actually used

    def on_after_damage_taken(self, ctx: BattleContext) -> None:
        user = ctx.user
        if user.is_fainted():
            return
        if self.consumable and not user.item_consumed:
            threshold = 0.5  # classic gens; some gens changed to 25% for pinch, etc.
            if user.hp_ratio() <= threshold:
                healed = user.heal_fraction(0.25)
                if healed > 0:
                    user.consume_item()  # engine removes item & sets flags
```

Engine logic would:

1. On damage taken, call `held_item.on_after_damage_taken(ctx)`.
2. `user.consume_item()` marks item as consumed and triggers Unburden, Harvest, etc.

---

### 10.4. Example: Choice Band (Persistent Held Item Affecting Base Power)

```python
@dataclass
class ChoiceBand(HeldItem):
    id: str = "choice_band"
    name: str = "Choice Band"
    description: str = "Boosts Attack but locks the holder into one move."
    consumable: bool = False
    removable: bool = True
    tradeable: bool = True

    def _apply_battle_use(self, ctx: BattleContext) -> bool:
        return False

    def _apply_field_use(self, ctx: BattleContext) -> bool:
        return False

    def on_base_power(self, ctx: BattleContext) -> float:
        user = ctx.user
        move = ctx.move
        # Only physical moves are boosted
        if move is None or not move.is_physical():
            return 1.0
        # Ignore if ability like Klutz or if item is suppressed by Magic Room
        if user.is_item_suppressed():
            return 1.0
        return 1.5  # example multiplier

    def on_before_move_selection(self, ctx: BattleContext) -> None:
        user = ctx.user
        # If user already locked into a move, restrict other choices
        if user.choice_lock_move is not None:
            user.restrict_move_selection(user.choice_lock_move)

    def on_after_move(self, ctx: BattleContext) -> None:
        user = ctx.user
        if user.choice_lock_move is None:
            user.choice_lock_move = ctx.move
```

Here, the Pokémon object (`user`) must have properties like `choice_lock_move`, `restrict_move_selection`, `is_item_suppressed`, etc.

---

### 10.5. Example: Life Orb (Damage Modifier with Recoil)

```python
@dataclass
class LifeOrb(HeldItem):
    id: str = "life_orb"
    name: str = "Life Orb"
    description: str = "Boosts damage at the cost of some HP after attacks."
    consumable: bool = False

    def _apply_battle_use(self, ctx: BattleContext) -> bool:
        return False

    def _apply_field_use(self, ctx: BattleContext) -> bool:
        return False

    def on_damage_mod(self, ctx: BattleContext) -> float:
        user = ctx.user
        move = ctx.move
        if move is None or move.is_status():
            return 1.0
        if user.is_item_suppressed():
            return 1.0
        return 1.3

    def on_after_move(self, ctx: BattleContext) -> None:
        user = ctx.user
        move = ctx.move
        # Recoil only if damage dealt, not on status moves or if move failed
        if move is None or move.is_status():
            return
        if ctx.hit_result is None or not ctx.hit_result.success:
            return
        if user.is_item_suppressed():
            return
        # Lose some HP (e.g., 10% max HP)
        user.lose_fraction(0.10)
```

---

### 10.6. Modeling Special / Irremovable Items (Mega Stones, Z-Crystals)

```python
@dataclass
class MegaStone(HeldItem):
    id: str = "charizardite_x"
    name: str = "Charizardite X"
    description: str = "Enables Charizard to Mega Evolve in battle."
    removable: bool = False
    tradeable: bool = True   # tradeable from bag, but not removable by Knock Off
    species_locks: List[str] = field(default_factory=lambda: ["Charizard"])

    def _apply_battle_use(self, ctx: BattleContext) -> bool:
        return False

    def _apply_field_use(self, ctx: BattleContext) -> bool:
        return False

    def can_be_tricked(self, ctx: BattleContext) -> bool:
        return False

    def can_be_removed(self, ctx: BattleContext) -> bool:
        return False

    def on_switch_in(self, ctx: BattleContext) -> None:
        user = ctx.user
        # engine checks: if trainer chooses Mega Evolution, use this item
        # Mega evolution logic belongs mostly to Pokémon & battle engine,
        # but they check for presence of this item.
```

Z-Crystals would be similar but with hooks to allow one Z-Move per battle. They might not need to override damage unless implementing a unique Z-Move effect.

---

### 10.7. Handling Single vs Double Battles

`BattleContext` includes `is_double_battle`, `side`, and `foe_side`. For items that behave differently in doubles, your hooks can check:

```python
def on_end_of_turn(self, ctx: BattleContext) -> None:
    user = ctx.user
    if ctx.is_double_battle:
        # Maybe handle ally-based effect
        ally = ctx.side.get_ally(user)
        # Apply effect to both, or conditionally
```

This pattern allows all per-turn effects to scale to singles/doubles/triples (if implemented) simply by interpreting the battle context.

---

### 10.8. Modeling Usable (Bag) Items

For items like Potions/X items, inherit from `Item` directly (or a `UsableItem` subclass):

```python
@dataclass
class Potion(Item):
    id: str = "potion"
    name: str = "Potion"
    description: str = "Restores a small amount of HP."
    category: str = "consumable"
    battle_usable: bool = True
    field_usable: bool = True
    consumable: bool = True

    def _apply_battle_use(self, ctx: BattleContext) -> bool:
        target = ctx.target or ctx.user
        if target.is_fainted():
            return False
        healed = target.heal_fixed(20)  # example amount
        return healed > 0

    def _apply_field_use(self, ctx: BattleContext) -> bool:
        target = ctx.target or ctx.user
        if target.is_fainted():
            return False
        healed = target.heal_fixed(20)
        return healed > 0
```

---

## 11. Summary

- In Pokémon, **items** are general-purpose effect containers that modify almost every system: HP, stats, types, status, abilities, moves, forms, and special mechanics.
- Items are heavily **event-driven**, especially held items, and must integrate with:
  - Abilities (Klutz, Unburden, Harvest, etc.).
  - Moves (Knock Off, Trick, Fling, Magic Room, etc.).
  - Special mechanics (Mega, Z-Moves, Dynamax, Terastal).
- A robust OOP model in Python:
  - Uses a base `Item` class for shared structure (id, name, description, flags).
  - Uses a `HeldItem` subclass with hooks for all relevant battle events.
  - Passes a `BattleContext` with references to the battle, Pokémon, move, field, etc.
  - Allows item-specific subclasses to override only the hooks they need.

This pattern lets you gradually implement more items and interactions while keeping the design clean, extensible, and close to the real game’s behavior.