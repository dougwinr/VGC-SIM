## 1. What is an Ability in Pokémon?

In mainline Pokémon games, an **Ability** is a passive property of a Pokémon that automatically affects battles (and sometimes the overworld) without needing to be chosen like a move.

Key characteristics:

- Every Pokémon normally has **one** Ability active at a time (two in some forms like Darmanitan’s Zen Mode if you count form mechanics, but only one “slot ability”).
- Each species usually has 1–3 possible abilities:
  - 1–2 “regular” abilities
  - 0–1 “Hidden” Ability
- A Pokémon’s Ability:
  - Always exists while it’s on the field (unless suppressed/changed).
  - Can modify **stats, damage, status, typing, turn order, weather/terrain, items, and more**.
  - Can be **trigger-based** (“on switch-in”, “when hit”, “each turn end”, etc.) or **continuous** (“always affect damage”, “always ignore hazards”, etc.).

Mechanically, you can think of an Ability as a set of **rules and callbacks** that the battle engine consults at many points in a turn.

---

## 2. What Can Abilities Do?

Below is a classification of what abilities can *give / remove / alter* in battle. Not exhaustive by name but covers the types of effects.

### 2.1. Stat modification

Abilities can modify stats:

- **Flat multipliers** to a stat:
  - *Huge Power*, *Pure Power* → double Attack.
  - *Fur Coat* → double Defense (physical).
- **Conditional multipliers**:
  - *Swift Swim* (Speed ×2 in rain)
  - *Chlorophyll* (Speed ×2 in sun)
  - *Hustle* (Attack ×1.5, physical accuracy down to 80%)
  - *Guts* (Attack ×1.5 while statused)
  - *Protosynthesis* / *Quark Drive* (boost highest stat in sun/Electric Terrain)
- **Stat stage changes** (like a passive “stat boost move”):
  - *Intimidate* → lowers foes’ Attack on switch-in.
  - *Competitive* / *Defiant* → raise your Sp.Atk / Attack when a stat is lowered.
  - *Moxie* → raises Attack after KOing a target.

These can apply:

- Continuously (always modify calculations).
- On a specific event (switch-in, KO, being hit, stat drop, etc).

---

### 2.2. Type interaction and immunity

Abilities can:

1. **Grant immunities** to damage types or status:
   - *Levitate* → Ground move + Spikes/Toxic Spikes immunity.
   - *Water Absorb*, *Volt Absorb*, *Storm Drain*, *Lightning Rod* → immunity to those types’ moves and healing / boosts instead.
   - *Soundproof* → immunity to sound-based moves.

2. **Modify type effectiveness**:
   - *Filter*, *Solid Rock* → reduce damage from super-effective hits.
   - *Thick Fat* → halves damage from Fire & Ice.
   - *Wonder Guard* → only super-effective moves can damage you.

3. **Modify or change the user’s type**:
   - *Libero* / *Protean* (before Gen 9 nerf: each move changes your type to that move’s type; in SV, once per switch-in).
   - *Color Change* → user becomes the type of the move that hit it.
   - *RKS System* & *Multitype* → user’s type depends on held item (Memory/Plate).

4. **Interact with typing-based mechanics** like Terastallization:
   - Terastallizing sets/overrides the Pokémon’s type to its Tera Type.
   - Type-changing effects (Soak, Trick-or-Treat, Forest’s Curse) and abilities like Libero/Protean:
     - Act **normally before** Terastallizing.
     - After Terastallizing in Scarlet/Violet, the Tera Type overrides most further type changes.

---

### 2.3. Damage modification

Abilities can:

- **Increase move power**:
  - *Adaptability* → STAB boost goes from 1.5× to 2×.
  - *Sheer Force* → 1.3× power for moves with secondary effects, but removes those secondary effects.
  - *Technician* → boosts moves base power ≤ 60.

- **Modify damage based on conditions**:
  - *Flare Boost* / *Toxic Boost* → boost Sp.Atk/Attack when burned/poisoned.
  - *Analytic* → boost power when moving last.
  - *Strong Jaw* → boost “bite” moves.
  - *Iron Fist* → boost punching moves.

- **Reduce incoming damage**:
  - *Marvel Scale* → Defense boost when statused.
  - *Ice Scales* → halves special damage.
  - *Heatproof* → halves Fire damage.

- **Reflect or add damage**:
  - *Rough Skin* / *Iron Barbs* → damage attacker on contact.
  - *Aftermath* → damage attacker when knocked out.
  - *Flame Body*, *Static*, *Poison Point* → chance to inflict status on contact.

---

### 2.4. Status conditions: granting, preventing, modifying

- **Prevent status**:
  - *Immunity* (no poison), *Limber* (no paralysis), *Insomnia* / *Vital Spirit* (no sleep), *Magma Armor* (no freeze), *Water Veil* (no burn), *Leaf Guard* (no status in sun).
  - *Comatose* → user is effectively always “asleep” for certain interactions but cannot be statused in the normal sense.

- **Prevent stat drops / flinches**:
  - *Clear Body* / *White Smoke* / *Full Metal Body* → prevent stat drops from foes’ effects.
  - *Inner Focus* → prevents flinching.

- **Reflect status**:
  - *Synchronize* → passes status back to the inflictor.
  - *Magic Bounce* → reflects many status moves and some hazards.

- **Alter status mechanics**:
  - *Quick Feet* → Speed boost when statused.
  - *Poison Heal* → heals instead of taking poison damage.

---

### 2.5. Field conditions: weather, terrain, rooms, hazards

Abilities can:

#### Weather

- **Set weather on switch-in**:
  - *Drizzle*, *Drought*, *Sand Stream*, *Snow Warning*.
  - *Orichalcum Pulse* → sets sun-like weather and boosts Attack.
  - *Hadron Engine* → sets Electric Terrain-like effect and boosts Sp.Atk.

- **Ignore weather**:
  - *Cloud Nine*, *Air Lock* → negate weather’s effects (but weather is still “present” for some checks).

- **Benefit from weather**:
  - *Swift Swim*, *Chlorophyll*, *Sand Rush*, *Slush Rush* → Speed in respective weather.
  - *Solar Power* → boosts Sp.Atk but damages user in sun.

#### Terrain

- Some abilities depend on or set terrain:
  - *Mimicry* → user’s type changes with terrain.
  - *Hadron Engine* (Gen 9) sets Electric Terrain-like effect.

#### Hazards

- Abilities to **ignore or reflect hazards**:
  - *Magic Guard* → no indirect damage (Spikes, Toxic Spikes, Leech Seed, recoil, weather, etc.).
  - *Levitate* & Flying-types ignore *Spikes* and *Toxic Spikes*, but not *Stealth Rock*.

---

### 2.6. Move mechanics: priority, targeting, choice restriction, accuracy

- **Priority modification**:
  - *Prankster* → non-damaging moves gain +1 priority.
  - *Gale Wings* (pre-nerf: all Flying moves; post-nerf: when at full HP) → gives +1 priority to Flying-type moves.
  - *Triage* → priority boosts for healing moves.

- **Move restrictions**:
  - *Gorilla Tactics* → Attack boost but locks you into the first move chosen (like permanent Choice Band).
  - *Truant* → act every other turn.
  - *Slow Start* → halves Attack and Speed for 5 turns.

- **Accuracy / evasion**:
  - *Compound Eyes* → boosts accuracy.
  - *No Guard* → all moves used by or on this Pokémon never miss.
  - *Keen Eye* → prevents accuracy drops.

- **Targeting / contact**:
  - *Long Reach* → contact moves don’t count as contact (avoids Static, Rough Skin, etc.).
  - *Telepathy* → no damage from allies’ attacks in doubles.

---

### 2.7. Item interaction

- **Finding or manipulating items**:
  - *Pickup* → chance to obtain items after battle or during battle (varies by gen).
  - *Frisk* → reveals opponents’ items on entry.
  - *Magician* / *Pickpocket* → steal the target’s item on hit or when hit.

- **Protect item/ability**:
  - *Sticky Hold* → prevents held item from being removed/knocked off.
  - (Item → Ability relationship) **Ability Shield** (item) prevents the holder’s ability from being changed or suppressed.

- **Use of certain items**:
  - *Multitype* (Arceus) & *RKS System* (Silvally) → change typing based on held items (Plates/Memories); these abilities themselves are often “locked” and cannot be suppressed or copied in some gens.

---

### 2.8. Form-changing / special mechanics

Some abilities control **form changes**, often with unique rules:

- *Zen Mode* (Darmanitan) → changes form below 50% HP (or when specific forms).
- *Schooling* (Wishiwashi) → forms change with HP thresholds.
- *Shields Down* (Minior) → differs between “Meteor” and “Core” forms based on HP.
- *Disguise* (Mimikyu) → first hit is negated, form changes, disguise breaks.
- *Ice Face* (Eiscue) → first physical hit consumes the “ice face”, form changes; restored in hail/snow.
- *Gulp Missile* (Cramorant) → form changes when using Surf/Dive and spits out fish/Arrokuda/Pikachu when hit.

Most of these:

- Are **not transferable** via moves like Skill Swap.
- Often **cannot be suppressed** fully or behave specially when suppressed (details are very generation-dependent).
- Are closely tied to **species identity** and are part of the form logic in the battle engine, not just a normal “flag”.

---

### 2.9. Meta effects: ignoring abilities, suppressing abilities, copying abilities

Ability mechanics among themselves are very rich:

#### 2.9.1. Ignoring abilities (Mold Breaker family, specific moves)

- *Mold Breaker*, *Teravolt*, *Turboblaze*:
  - The user’s moves ignore defensive abilities of the target that would:
    - Prevent damage (e.g., *Levitate* vs Ground, *Wonder Guard*),
    - Reduce damage (e.g., *Filter*, *Thick Fat*),
    - Change type effectiveness.
  - They **do not** ignore all abilities (e.g., they don’t stop *Intimidate* or offensive abilities on the target’s side).

- Certain signature moves also ignore abilities’ effects:
  - *Sunsteel Strike*, *Moongeist Beam*, *Photon Geyser* ignore abilities that would affect damage or effect (similar to Mold Breaker on a per-move basis).

#### 2.9.2. Suppressing abilities

- *Gastro Acid* → nullifies target’s ability (non-permanent; ends on switch out).
- *Neutralizing Gas* (Galarian Weezing):
  - While user is on field, most other abilities are treated as inactive.
  - Exceptions: some form-changing abilities and a few special cases still work.
- *Core Enforcer* → if target has moved this turn, its ability is suppressed.
- *Gravity* interacts with some abilities by changing type immunity (makes Flying/Levitate hit by Ground moves, etc.) but not strictly “suppressing” the ability; it just changes type immunity rules.

#### 2.9.3. Changing / copying abilities

- *Skill Swap* → swaps abilities between two Pokémon (with many exceptions).
- *Role Play* → copies target’s ability.
- *Entrainment* → replaces target’s ability with user’s.
- *Simple Beam* / *Worry Seed* → replace target’s ability with *Simple* or *Insomnia*.
- *Mummy*, *Wandering Spirit* → attackers that make contact get their ability changed to Mummy / swapped with Wandering Spirit.

Many abilities **cannot be changed / copied** this way (Multitype, As One, Schooling, etc.), and you would mark those as `immutable` or `uncopiable` in a model.

---

### 2.10. Interactions with other battle mechanics

#### 2.10.1. Mega Evolution

- On Mega Evolving:
  - The Pokémon’s Ability usually changes to the Mega’s Ability.
  - This change happens **immediately** before move execution that turn, so the new ability affects that very move.
  - Abilities that trigger “on switch-in” usually do **not** trigger when you Mega Evolve mid-battle (because this is not a switch).

#### 2.10.2. Dynamax / Gigantamax

- Dynamaxing does not change ability, but:
  - Abilities interact with Max Moves:
    - *Libero* / *Protean* change the user’s type based on the underlying move, not the “Max” type itself, but in practice you treat them as using a move of the underlying type.
  - Abilities that prevent flinching or status still work.
  - Size-related or fixed-damage moves that rely on target’s max HP interact with abilities like *Magic Guard*.

Some special abilities like *Disguise* and *Ice Face* have additional interactions with Dynamax/Max Moves (damage thresholds, etc.) but that level of detail is per-ability.

#### 2.10.3. Z-Moves

- Z-Moves:
  - Use the underlying move’s type and category but have fixed power/effects.
  - Most abilities that modify damage or type apply as usual (e.g., *Adaptability*, *Strong Jaw* if the Z-Move is based on a bite move).
  - Some Z-Moves override normal secondary effects, so abilities like *Sheer Force* are irrelevant for their added effects.

#### 2.10.4. Terastallization

- Tera changes the Pokémon’s type to its **Tera Type**:
  - STAB and type-based abilities are re-evaluated with new typing.
  - *Adaptability* may become much stronger if Tera matches its original type or a new type.
- Many type-changing moves/abilities don't alter a Terastallized Pokémon’s type afterward (game-specific behavior).
- Abilities like *Protosynthesis* / *Quark Drive* depend on field (Sun/Electric Terrain) and can make Tera synergize strongly with these.

---

### 2.11. Single vs Double Battles

In doubles, abilities often become more complex:

1. **Multi-target triggering**:
   - *Intimidate* affects all opposing active Pokémon.
   - *Download* compares both opponents’ stats to choose which stat to boost.
   - *Drizzle*, *Drought*, etc. affect the entire field.

2. **Ally-targeting abilities**:
   - *Flower Gift* → boosts allied Pokémon in sun.
   - *Friend Guard* → reduces damage taken by allies.
   - *Battery* → boosts special moves of ally.
   - *Telepathy* → prevents damage from ally’s moves (e.g., Earthquake).

3. **Order of activation**:
   - On switch-in or battle start, abilities activate in a specific sequence:
     - Turn order often depends on **Speed**, then position, but weather and terrain abilities have special priority rules (e.g., multiple weather setters: last one to activate “wins”).
   - *Neutralizing Gas* interactions: when Weezing-Galar enters, its ability activates before or after some other abilities depending on exact rules; most other abilities become suppressed once it is recognized on the field.

4. **Targeting and redirection**:
   - Abilities like *Storm Drain* and *Lightning Rod* can **redirect** moves to themselves (e.g., Water/Electric single-target moves can be forced to hit the ability user).

Your model needs to account for:

- Abilities that affect **all Pokémon**.
- Abilities that affect **only allies**, **only foes**, or **the user**.
- Activation order based on **battle events** and **speed order**.

---

## 3. How to Model Abilities in Object-Oriented Python

### 3.1. Main design idea

An Ability is best modeled as a class that reacts to **battle events**. The battle engine emits events like:

- `on_switch_in`
- `on_switch_out`
- `on_before_move`
- `on_after_move`
- `on_damage_calc`
- `on_status_inflict`
- `on_status_receive`
- `on_faint`
- `on_turn_start`
- `on_turn_end`
- `on_weather_start`, `on_weather_end`
- `on_terrain_start`, etc.

Each Ability can override the callbacks it cares about.

This suggests:

- An abstract base class `Ability` defining all possible callbacks (mostly empty).
- Concrete subclasses (or data-driven configs) implementing specific behaviors.

You also need supporting classes:

- `Pokemon`
- `Move`
- `Battle`
- `Field` (weather, terrain, rooms, global conditions)
- `Side` (team/side conditions)
- `EventContext` (context object with extra info like attacker/defender, damage, etc.)

---

### 3.2. Core abstractions for an Ability

At minimum, an `Ability` should know:

- `name`: string.
- `description`: string or localized text key.
- `generation_introduced`: int.
- Flags for behavior:
  - `immutable`: cannot be changed via Skill Swap, etc.
  - `suppressed`: runtime flag for whether it is currently suppressed.
  - `can_be_suppressed`: (Gastro Acid, Neutralizing Gas checks).
  - `hidden`: whether this is a Hidden Ability.
- A reference to its owner:
  - `owner: Pokemon`.

And it should expose methods for the battle engine to call:

- Initialization and toggling:
  - `__init__(self, owner: Pokemon)`
  - `activate(self, battle: Battle)` (e.g., on switch-in)
  - `deactivate(self, battle: Battle)` (e.g., on switch-out or faint)
  - `suppress(self, source)` / `unsuppress(self, source)`

- Event handlers, such as:
  - `on_switch_in(self, battle)`
  - `on_switch_out(self, battle)`
  - `on_before_move(self, move, battle)`
  - `on_after_move(self, move, battle)`
  - `on_damage_calc(self, attacker, defender, move, damage, battle) -> int`
  - `on_stat_change(self, stat, delta, source, battle) -> int`
  - `on_status_receive(self, status, source, battle) -> bool` (allow/deny)
  - `on_status_inflict(self, target, status, move, battle)`
  - `on_turn_start(self, battle)`
  - `on_turn_end(self, battle)`
  - `on_faint(self, battle)`
  - `on_weather_change(self, old_weather, new_weather, battle)`
  - etc.

You do **not** need to implement every effect in the base, just provide hooks so specific abilities can override them.

---

### 3.3. Base class example

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from battle import Battle
    from pokemon import Pokemon
    from move import Move
    from enums import Stat, Status, Weather, Terrain

class Ability(ABC):
    """
    Abstract base class for all abilities.
    Battle engine calls these hooks at appropriate times.
    """

    name: str = "Unknown Ability"
    description: str = ""
    generation_introduced: int = 3
    hidden: bool = False

    # Rules about ability interactions
    immutable: bool = False        # cannot be changed by Skill Swap, etc.
    can_be_suppressed: bool = True # Gastro Acid / Neutralizing Gas affect it

    def __init__(self, owner: Pokemon) -> None:
        self.owner = owner
        self.suppressed: bool = False  # runtime flag

    # ---- Utility methods ----

    def is_active(self) -> bool:
        """Return True if ability is currently functioning."""
        return (not self.suppressed) and (not self.owner.is_fainted)

    def suppress(self, source: Optional[Pokemon] = None) -> None:
        """Called when a move like Gastro Acid suppresses this ability."""
        if self.can_be_suppressed and not self.immutable:
            self.suppressed = True

    def unsuppress(self, source: Optional[Pokemon] = None) -> None:
        """Called when suppression ends (e.g., switch out or end of effect)."""
        self.suppressed = False

    # ---- Activation / lifecycle ----

    def on_switch_in(self, battle: Battle) -> None:
        """Called when owner becomes active."""
        pass

    def on_switch_out(self, battle: Battle) -> None:
        """Called when owner leaves the field."""
        pass

    def on_faint(self, battle: Battle) -> None:
        """Called when owner faints."""
        pass

    # ---- Turn structure ----

    def on_turn_start(self, battle: Battle) -> None:
        """Called at the beginning of each full turn."""
        pass

    def on_turn_end(self, battle: Battle) -> None:
        """Called at the end of each full turn."""
        pass

    # ---- Move-related hooks ----

    def on_before_move(self, move: Move, battle: Battle) -> None:
        """Called before owner selects/executes a move."""
        pass

    def on_after_move(self, move: Move, battle: Battle) -> None:
        """Called after owner executes a move."""
        pass

    def on_move_targeted(
        self, move: Move, attacker: Pokemon, battle: Battle
    ) -> None:
        """
        Called when a move is targeting the owner.
        Used for things like move redirection, immunity messages, etc.
        """
        pass

    # ---- Damage & stat calc hooks ----

    def on_damage_calc(
        self,
        attacker: Pokemon,
        defender: Pokemon,
        move: Move,
        base_damage: int,
        battle: Battle,
    ) -> int:
        """
        Called during damage calculation.
        Should return possibly modified damage.
        """
        return base_damage

    def on_stat_calc(
        self,
        stat: Stat,
        base_value: int,
        battle: Battle,
    ) -> int:
        """
        Called when a stat is being computed (after EV/IV, before stage multipliers).
        For static multipliers like Huge Power, Fur Coat, etc.
        """
        return base_value

    def on_stat_change(
        self,
        stat: Stat,
        delta: int,
        source: Optional[Pokemon],
        battle: Battle,
    ) -> int:
        """
        Called when a stat stage change is attempted (e.g. -1 Attack from Intimidate).
        Can modify or cancel the change by returning a different delta (including 0).
        """
        return delta

    # ---- Status & conditions ----

    def on_status_receive(
        self,
        status: Status,
        source: Optional[Pokemon],
        battle: Battle,
    ) -> bool:
        """
        Called when owner is about to receive a non-volatile status.
        Return True to allow, False to block (e.g. Immunity / Insomnia).
        """
        return True

    def on_status_inflict(
        self,
        target: Pokemon,
        status: Status,
        move: Move,
        battle: Battle,
    ) -> None:
        """
        Called when owner inflicts a status.
        For things like Synchronize, Poison Touch, etc.
        """
        pass

    # ---- Field effects ----

    def on_weather_change(
        self,
        old_weather: Optional[Weather],
        new_weather: Optional[Weather],
        battle: Battle,
    ) -> None:
        """
        Called whenever weather changes.
        For Swift Swim, Chlorophyll, Dry Skin checks, etc.
        """
        pass

    def on_terrain_change(
        self,
        old_terrain: Optional[Terrain],
        new_terrain: Optional[Terrain],
        battle: Battle,
    ) -> None:
        """
        Called whenever terrain changes.
        For Mimicry, Hadron Engine effects, etc.
        """
        pass

    # ---- Misc events ----

    def on_contact_hit(
        self,
        attacker: Pokemon,
        move: Move,
        damage: int,
        battle: Battle,
    ) -> None:
        """
        Called when the owner is hit by a contact move.
        For Static, Flame Body, Rough Skin, etc.
        """
        pass
```

This base class:

- Defines **attributes** and **hooks** but no concrete behavior.
- Gives you a unified way for the battle engine to ask each ability: “Do you want to modify this event?”

---

### 3.4. Example concrete abilities

#### 3.4.1. Intimidate

Effect:

- On switch-in, lowers all adjacent opponents’ Attack by 1 stage.

```python
class Intimidate(Ability):
    name = "Intimidate"
    description = "Lowers the foe's Attack stat on switch-in."
    generation_introduced = 3

    def on_switch_in(self, battle: Battle) -> None:
        if not self.is_active():
            return

        # In singles: one opponent; in doubles: up to two
        for foe in battle.get_adjacent_opponents(self.owner):
            if foe.is_fainted:
                continue

            # Check ability blockers like Clear Body / Ability Shield, etc.
            # Let foe's ability decide whether to allow stat drop
            delta = foe.ability.on_stat_change(
                stat=battle.Stat.ATTACK,
                delta=-1,
                source=self.owner,
                battle=battle,
            )

            if delta != 0:
                foe.modify_stat_stage(battle.Stat.ATTACK, delta, source=self.owner)
                battle.log(f"{foe.name}'s Attack fell due to Intimidate!")
```

Here:

- `battle.get_adjacent_opponents(self.owner)` must respect singles/doubles/triples rules.
- `foe.ability.on_stat_change` gives target’s ability a chance to prevent or modify the drop (*Clear Body*, *Contrary*, *Defiant*, etc.).

---

#### 3.4.2. Levitate

Effect:

- Grants immunity to Ground-type moves, Arena Trap, Spikes/Toxic Spikes, etc.

```python
class Levitate(Ability):
    name = "Levitate"
    description = "Gives full immunity to all Ground-type moves."
    generation_introduced = 3

    def on_move_targeted(self, move: Move, attacker: Pokemon, battle: Battle) -> None:
        if not self.is_active():
            return

        # If move is Ground-type and this Pokémon would be hit
        if move.type.is_ground() and move.is_damaging():
            # Check for Mold Breaker-like effects
            if attacker.ability and attacker.ability.ignores_defender_abilities():
                return

            # Grant immunity
            battle.log(f"{self.owner.name} is levitating and avoids the attack!")
            move.cancel_for_target(self.owner, reason="Levitate")

    def on_hazard_damage_check(self, hazard_type: str, battle: Battle) -> bool:
        """
        Called before applying hazard damage such as Spikes or Toxic Spikes.
        Return False to prevent damage; True to allow.
        """
        if not self.is_active():
            return True

        if hazard_type in ("spikes", "toxic_spikes"):
            return False

        return True
```

You’d need to define the `ignores_defender_abilities` method on “Mold Breaker-like” abilities, or a flag.

---

#### 3.4.3. Mold Breaker

Effect:

- User’s moves ignore the target’s defensive abilities that would affect damage/immunity.

```python
class MoldBreaker(Ability):
    name = "Mold Breaker"
    description = "Moves can be used regardless of the foe's abilities."
    generation_introduced = 4

    def ignores_defender_abilities(self) -> bool:
        return self.is_active()
```

Then in your damage / targeting logic:

```python
def calculate_damage(attacker: Pokemon, defender: Pokemon, move: Move, battle: Battle) -> int:
    base_damage = battle.compute_base_damage(attacker, defender, move)

    # Apply defensive ability unless ignored
    if not attacker.ability or not attacker.ability.ignores_defender_abilities():
        base_damage = defender.ability.on_damage_calc(attacker, defender, move, base_damage, battle)
    else:
        # Attacker is ignoring defender's ability (Mold Breaker etc.)
        pass

    # Apply offensive ability
    if attacker.ability:
        base_damage = attacker.ability.on_damage_calc(attacker, defender, move, base_damage, battle)

    return max(1, base_damage)
```

---

#### 3.4.4. Neutralizing Gas

Effect:

- While the user is active, most other abilities are considered suppressed.

This is easiest to handle in the **Battle** class:

```python
class NeutralizingGas(Ability):
    name = "Neutralizing Gas"
    description = "While the Pokémon is in battle, the effects of all other Abilities are nullified."
    generation_introduced = 8

    # This ability itself is generally unsuppressible by its own effect
    immutable = True
    can_be_suppressed = False

    def on_switch_in(self, battle: Battle) -> None:
        if not self.is_active():
            return
        battle.apply_neutralizing_gas(self.owner)

    def on_switch_out(self, battle: Battle) -> None:
        battle.remove_neutralizing_gas(self.owner)

    def on_faint(self, battle: Battle) -> None:
        battle.remove_neutralizing_gas(self.owner)
```

And in `Battle`:

```python
class Battle:
    def __init__(self):
        self.neutralizing_gas_active = False
        self.neutralizing_gas_sources: set[Pokemon] = set()

    def apply_neutralizing_gas(self, source: Pokemon) -> None:
        self.neutralizing_gas_sources.add(source)
        self.neutralizing_gas_active = True
        # Suppress abilities for all non-neutralizing-gas Pokémon
        for mon in self.all_active_pokemon():
            if mon.ability and not isinstance(mon.ability, NeutralizingGas):
                mon.ability.suppress(source=source)

    def remove_neutralizing_gas(self, source: Pokemon) -> None:
        if source in self.neutralizing_gas_sources:
            self.neutralizing_gas_sources.remove(source)
        if not self.neutralizing_gas_sources:
            self.neutralizing_gas_active = False
            # Restore abilities
            for mon in self.all_active_pokemon():
                if mon.ability:
                    mon.ability.unsuppress(source=source)
```

You should also respect **Ability Shield**:

```python
def apply_neutralizing_gas(self, source: Pokemon) -> None:
    self.neutralizing_gas_sources.add(source)
    self.neutralizing_gas_active = True
    for mon in self.all_active_pokemon():
        if mon is source:
            continue
        if mon.ability and not isinstance(mon.ability, NeutralizingGas):
            if mon.holds_ability_shield():
                continue
            mon.ability.suppress(source=source)
```

---

### 3.5. How to organize all abilities

For a full system:

1. **Registry pattern**:
   - Maintain a dict `ABILITY_REGISTRY: dict[str, type[Ability]]` mapping ability names/IDs to classes.
   - Use a decorator to register abilities:

   ```python
   ABILITY_REGISTRY = {}

   def register_ability(cls):
       ABILITY_REGISTRY[cls.name] = cls
       return cls
   ```

2. Define abilities:

   ```python
   @register_ability
   class Intimidate(Ability):
       ...
   ```

3. When creating a Pokémon:

   ```python
   def create_ability(name: str, owner: Pokemon) -> Ability:
       ability_cls = ABILITY_REGISTRY[name]
       return ability_cls(owner)
   ```

4. **Data-driven configuration** (optional, more advanced):
   - Some abilities are simple “multipliers” or “immunities”.
   - You can store their behavior as data (JSON/YAML) and use generic ability classes like `StatModifierAbility`, `TypeImmunityAbility` instead of one class per ability.
   - For complex abilities (Mold Breaker, Neutralizing Gas, form-changing ones), write custom classes.

---

### 3.6. Summary of modeling recommendations

- Treat **Ability** as a **component** attached to `Pokemon` with:
  - Metadata (name, gen, immutable flags).
  - Runtime state (`suppressed`, possible stacks/counters).
  - A set of **event handlers** called by the battle engine.

- Implement the battle engine using a **central event dispatcher**:
  - For each event (`on_switch_in`, `on_damage_calc`, etc.), iterate through all active Pokémon’s abilities and let them modify the event.

- Carefully model **exceptions** with flags:
  - `immutable` / `can_be_suppressed` / `can_be_copied` / `can_be_swapped`.
  - Special-case form-changing abilities and signature abilities.

- For doubles:
  - Make sure `Battle` provides utilities like `get_adjacent_opponents`, `get_allies`, `all_active_pokemon`.
  - Abilities need to query the battle state, not hard-code “single” vs “double”.

With this structure, you can implement essentially any Ability from the games, including their interactions with items, moves, Mega/Dynamax/Z/Tera mechanics, and partner Pokémon in double battles.