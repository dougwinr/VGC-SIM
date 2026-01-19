"""
Lightweight double-battle simulator.

This is intentionally simplified so we can iterate on mechanics without pulling
in the full Pokémon Showdown engine. It supports:
  - Two teams of two Pokémon each (doubles format).
  - Turn order based on move priority then effective Speed (Tailwind aware).
  - Damage with a trimmed formula (levels, power, Atk/SpA vs Def/SpD,
    STAB, Adaptability, item/ability/terrain/weather tweaks, type chart).
  - Common item/ability effects used by the sample team:
      Life Orb, Focus Sash, Assault Vest, Black Glasses, Choice Band,
      Light Clay (extending Aurora Veil), Supreme Overlord, Adaptability,
      Good as Gold (blocks status moves), Grassy Surge, Snow Warning.
  - A handful of status/field moves: Protect, Nasty Plot, Tailwind,
    Aurora Veil, Grassy Terrain, Snow (from Snow Warning), basic screens.

This is not a pixel-perfect battle engine; it is a pragmatic starting point
so we can validate data plumbing and iterate on future mechanics.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Sequence

from classes.ability import Ability
from classes.item import Item
from classes.move import Move, MoveCategory
from classes.pokemon import Pokemon, Stats
from classes.type import Type, TypeChart


# ----- Battle State ----------------------------------------------------------------------


@dataclass
class FieldState:
    weather: Optional[str] = None  # e.g. "snow", "rain"
    terrain: Optional[str] = None  # e.g. "grassy"
    tailwind_turns: dict[int, int] = field(default_factory=dict)  # team index -> turns left
    screens: dict[int, dict[str, int]] = field(default_factory=dict)  # team index -> {"aurora_veil": turns}


@dataclass
class BattlePokemon:
    pokemon: Pokemon
    team_index: int
    slot: int
    current_hp: int
    status: Optional[str] = None  # e.g. "burn", "paralysis"
    stat_stages: dict[str, int] = field(default_factory=lambda: {"atk": 0, "defense": 0, "spa": 0, "spd": 0, "spe": 0})
    protect_active: bool = False
    sash_consumed: bool = False

    @classmethod
    def from_pokemon(cls, pokemon: Pokemon, team_index: int, slot: int) -> BattlePokemon:
        hp = pokemon.battle_stats().hp
        return cls(pokemon=pokemon, team_index=team_index, slot=slot, current_hp=hp)

    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    def effective_speed(self, field: FieldState) -> int:
        stats = self.pokemon.battle_stats()
        base_speed = _apply_stage(stats.speed, self.stat_stages["spe"])
        tailwind_active = field.tailwind_turns.get(self.team_index, 0) > 0
        if tailwind_active:
            base_speed *= 2
        if self.status == "paralysis":
            base_speed = math.floor(base_speed * 0.5)
        return base_speed


@dataclass
class Action:
    actor: BattlePokemon
    move: Move
    target: BattlePokemon


# ----- Core helpers ----------------------------------------------------------------------


def _apply_stage(value: int, stage: int) -> int:
    if stage >= 0:
        return math.floor(value * (2 + stage) / 2)
    return math.floor(value * 2 / (2 - stage))


def _stab_multiplier(attacker: BattlePokemon, move: Move) -> float:
    names = {t.name for t in attacker.pokemon.active_types}
    if move.move_type.name in names:
        if attacker.pokemon.ability and attacker.pokemon.ability.name.lower() == "adaptability":
            return 2.0
        return 1.5
    return 1.0


def _item_attack_multiplier(attacker: BattlePokemon, move: Move) -> float:
    item = attacker.pokemon.item
    if not item:
        return 1.0
    name = item.name.lower()
    if name == "life orb":
        return 1.3
    if name == "choice band" and move.category is MoveCategory.PHYSICAL:
        return 1.5
    if name == "black glasses" and move.move_type.name == "dark":
        return 1.2
    return 1.0


def _supreme_overlord_multiplier(attacker: BattlePokemon, allies: Sequence[BattlePokemon]) -> float:
    if not attacker.pokemon.ability or attacker.pokemon.ability.name.lower() != "supreme overlord":
        return 1.0
    fainted = sum(1 for ally in allies if ally.is_fainted() and ally is not attacker)
    return 1.0 + 0.1 * fainted


def _is_status_move(move: Move) -> bool:
    return move.category is MoveCategory.STATUS


def _good_as_gold_blocks(target: BattlePokemon, move: Move) -> bool:
    ability = target.pokemon.ability
    return ability and ability.name.lower() == "good as gold" and _is_status_move(move)


def _focus_sash_survival(target: BattlePokemon, damage: int) -> int:
    item = target.pokemon.item
    if not item or target.sash_consumed:
        return target.current_hp - damage
    if item.name.lower() == "focus sash" and target.current_hp == target.pokemon.battle_stats().hp and damage >= target.current_hp:
        target.sash_consumed = True
        return 1
    return target.current_hp - damage


def _terrain_multiplier(field: FieldState, move: Move) -> float:
    if field.terrain == "grassy" and move.move_type.name == "grass":
        return 1.3
    return 1.0


def _screen_multiplier(field: FieldState, defender: BattlePokemon) -> float:
    screens = field.screens.get(defender.team_index, {})
    if screens.get("aurora_veil", 0) > 0:
        return 0.5
    return 1.0


def calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move: Move,
    type_chart: TypeChart,
    field: FieldState,
    allies: Sequence[BattlePokemon],
) -> int:
    if _is_status_move(move):
        return 0

    stats_attacker = attacker.pokemon.battle_stats()
    stats_defender = defender.pokemon.battle_stats()

    if move.category is MoveCategory.PHYSICAL:
        attack = _apply_stage(stats_attacker.attack, attacker.stat_stages["atk"])
        defense = _apply_stage(stats_defender.defense, defender.stat_stages["defense"])
        # Burn halves physical output.
        if attacker.status == "burn":
            attack = math.floor(attack * 0.5)
    else:
        attack = _apply_stage(stats_attacker.sp_attack, attacker.stat_stages["spa"])
        defense = _apply_stage(stats_defender.sp_defense, defender.stat_stages["spd"])
        # Assault Vest bonus to SpDef.
        if defender.pokemon.item and defender.pokemon.item.name.lower() == "assault vest":
            defense = math.floor(defense * 1.5)

    # Base power tweaks for specific moves we care about.
    base_power = move.power or 0
    if move.name.lower() == "last respects":
        fainted_allies = sum(1 for ally in allies if ally.is_fainted())
        base_power = 50 + 50 * fainted_allies

    level = attacker.pokemon.level
    # Trimmed main damage formula.
    damage = math.floor((((2 * level / 5 + 2) * base_power * attack / max(1, defense)) / 50) + 2)

    damage = math.floor(damage * _stab_multiplier(attacker, move))
    damage = math.floor(damage * type_chart.damage_multiplier(move.move_type, defender.pokemon.active_types))
    damage = math.floor(damage * _item_attack_multiplier(attacker, move))
    damage = math.floor(damage * _supreme_overlord_multiplier(attacker, allies))
    damage = math.floor(damage * _terrain_multiplier(field, move))
    damage = math.floor(damage * _screen_multiplier(field, defender))

    # Life Orb recoil: apply after damage is dealt.
    life_orb = attacker.pokemon.item and attacker.pokemon.item.name.lower() == "life orb"

    # Prevent zero damage in most cases.
    damage = max(1, damage)

    # Apply Focus Sash check.
    remaining_hp = _focus_sash_survival(defender, damage)

    defender.current_hp = remaining_hp
    if defender.current_hp <= 0:
        defender.current_hp = 0

    if life_orb and not attacker.is_fainted():
        recoil = max(1, math.floor(attacker.pokemon.battle_stats().hp * 0.1))
        attacker.current_hp = max(0, attacker.current_hp - recoil)

    # Simple recoil for Wave Crash.
    if move.name.lower() == "wave crash" and damage > 0:
        recoil = max(1, math.floor(damage / 3))
        attacker.current_hp = max(0, attacker.current_hp - recoil)

    return damage


# ----- Move resolution -------------------------------------------------------------------


def apply_move(
    action: Action,
    opponents: Sequence[BattlePokemon],
    allies: Sequence[BattlePokemon],
    type_chart: TypeChart,
    field: FieldState,
) -> None:
    user = action.actor
    move = action.move
    target = action.target

    if user.is_fainted():
        return

    # Protect expires each turn; set off before resolving moves.
    if move.name.lower() == "protect":
        user.protect_active = True
        return

    # Good as Gold check for status moves that target a Pokémon.
    if _good_as_gold_blocks(target, move):
        return

    # Status moves with explicit effects we care about.
    lowered_moves = move.name.lower()
    if move.category is MoveCategory.STATUS:
        if lowered_moves == "tailwind":
            field.tailwind_turns[user.team_index] = 4
            return
        if lowered_moves == "nasty plot":
            user.stat_stages["spa"] += 2
            return
        if lowered_moves == "aurora veil":
            duration = 8 if user.pokemon.item and user.pokemon.item.name.lower() == "light clay" else 5
            field.screens.setdefault(user.team_index, {})["aurora_veil"] = duration
            return
        # Other status moves are ignored for now.
        return

    # Damage-dealing moves.
    if target.is_fainted():
        return

    # Respect Protect.
    if target.protect_active:
        return

    damage = calculate_damage(user, target, move, type_chart, field, allies)

    # Apply secondary stat changes for specific moves.
    if move.name.lower() == "make it rain":
        user.stat_stages["spa"] -= 1


def advance_field(field: FieldState) -> None:
    # Tick down Tailwind and screens.
    for key in list(field.tailwind_turns.keys()):
        if field.tailwind_turns[key] > 0:
            field.tailwind_turns[key] -= 1
        if field.tailwind_turns[key] <= 0:
            field.tailwind_turns.pop(key, None)

    for team_idx, screen_map in list(field.screens.items()):
        for screen, turns in list(screen_map.items()):
            screen_map[screen] = turns - 1
            if screen_map[screen] <= 0:
                screen_map.pop(screen)
        if not screen_map:
            field.screens.pop(team_idx, None)


# ----- Battle driver ---------------------------------------------------------------------


@dataclass
class Battle:
    team_a: List[BattlePokemon]
    team_b: List[BattlePokemon]
    type_chart: TypeChart
    field: FieldState = field(default_factory=FieldState)

    def all_pokemon(self) -> List[BattlePokemon]:
        return self.team_a + self.team_b

    def living_team(self, team_index: int) -> List[BattlePokemon]:
        team = self.team_a if team_index == 0 else self.team_b
        return [mon for mon in team if not mon.is_fainted()]

    def opponents(self, mon: BattlePokemon) -> List[BattlePokemon]:
        return self.team_b if mon.team_index == 0 else self.team_a

    def allies(self, mon: BattlePokemon) -> List[BattlePokemon]:
        return self.team_a if mon.team_index == 0 else self.team_b

    def is_battle_over(self) -> bool:
        return not self.living_team(0) or not self.living_team(1)

    def turn_order(self, actions: List[Action]) -> List[Action]:
        def sort_key(action: Action):
            move_priority = action.move.priority
            speed = action.actor.effective_speed(self.field)
            return (-move_priority, -speed, random.random())

        return sorted(actions, key=sort_key)

    def execute_turn(self, actions: List[Action]) -> None:
        # Reset Protect each turn.
        for mon in self.all_pokemon():
            mon.protect_active = False

        for action in self.turn_order(actions):
            if self.is_battle_over():
                break
            if action.actor.is_fainted():
                continue
            apply_move(action, self.opponents(action.actor), self.allies(action.actor), self.type_chart, self.field)

        advance_field(self.field)


def build_battle(team_a: Sequence[Pokemon], team_b: Sequence[Pokemon], type_chart: TypeChart) -> Battle:
    if len(team_a) != 2 or len(team_b) != 2:
        raise ValueError("Double battles require exactly two Pokémon per side.")
    mons_a = [BattlePokemon.from_pokemon(p, team_index=0, slot=i) for i, p in enumerate(team_a)]
    mons_b = [BattlePokemon.from_pokemon(p, team_index=1, slot=i) for i, p in enumerate(team_b)]

    # Handle entry abilities that set field.
    field = FieldState()
    for mon in mons_a + mons_b:
        ability_name = mon.pokemon.ability.name.lower() if mon.pokemon.ability else ""
        if ability_name == "grassy surge":
            field.terrain = "grassy"
        if ability_name == "snow warning":
            field.weather = "snow"

    return Battle(team_a=mons_a, team_b=mons_b, type_chart=type_chart, field=field)


# ----- Example usage ---------------------------------------------------------------------


def pick_action(attacker: BattlePokemon, battle: Battle) -> Action:
    """
    Naive action chooser: pick the first available move and target the first living foe.
    Replace this with smarter selection or UI hooks as needed.
    """
    move = attacker.pokemon.moves[0]
    target_candidates = [foe for foe in battle.opponents(attacker) if not foe.is_fainted()]
    target = target_candidates[0]
    return Action(actor=attacker, move=move, target=target)


def simulate_battle(team_a: Sequence[Pokemon], team_b: Sequence[Pokemon], type_chart: TypeChart, max_turns: int = 10) -> int:
    battle = build_battle(team_a, team_b, type_chart)

    for turn in range(1, max_turns + 1):
        if battle.is_battle_over():
            break
        actions: List[Action] = []
        for mon in battle.all_pokemon():
            if mon.is_fainted():
                continue
            actions.append(pick_action(mon, battle))
        battle.execute_turn(actions)

    if not battle.living_team(0):
        return 1  # Team B wins
    if not battle.living_team(1):
        return 0  # Team A wins
    return -1  # Tie / max turns reached


__all__ = [
    "Battle",
    "BattlePokemon",
    "FieldState",
    "Action",
    "simulate_battle",
    "build_battle",
]
