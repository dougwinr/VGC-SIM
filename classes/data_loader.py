from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .ability import Ability
from .item import Item
from .move import Move, MoveCategory
from .pokemon import PokemonSpecies, Stats
from .type import TypeChart


DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "silver"


def _load_json(path: Path) -> Mapping:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _slug(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def load_type_chart(path: Path | None = None) -> TypeChart:
    chart_path = path or DATA_ROOT / "typechart_data.json"
    raw_chart = _load_json(chart_path)
    return TypeChart.from_showdown_chart(raw_chart)


def load_abilities(path: Path | None = None) -> dict[str, Ability]:
    abilities_path = path or DATA_ROOT / "abilities_text.json"
    raw = _load_json(abilities_path)
    abilities: dict[str, Ability] = {}
    for key, entry in raw.items():
        name = entry.get("name", key)
        desc = entry.get("shortDesc") or entry.get("desc") or ""
        abilities[key] = Ability(name=name, description=desc)
    return abilities


def load_items(data_path: Path | None = None, text_path: Path | None = None) -> dict[str, Item]:
    items_path = data_path or DATA_ROOT / "items_data.json"
    text_items_path = text_path or DATA_ROOT / "items_text.json"
    data = _load_json(items_path)
    text = _load_json(text_items_path)

    items: dict[str, Item] = {}
    for key, entry in data.items():
        text_entry = text.get(key, {})
        description = text_entry.get("shortDesc", "")
        category = "mega-stone" if "megaStone" in entry else entry.get("isNonstandard")
        items[key] = Item(
            name=entry.get("name", key),
            description=description,
            consumable=bool(entry.get("isBerry")) or bool(entry.get("consumable")),
            category=category,
        )
    return items


def load_moves(
    chart: TypeChart, data_path: Path | None = None, text_path: Path | None = None
) -> dict[str, Move]:
    moves_data_path = data_path or DATA_ROOT / "moves_data.json"
    moves_text_path = text_path or DATA_ROOT / "moves_text.json"
    data = _load_json(moves_data_path)
    text = _load_json(moves_text_path)

    moves: dict[str, Move] = {}
    for key, entry in data.items():
        category = MoveCategory(entry["category"].lower())
        accuracy = entry.get("accuracy")
        if accuracy is True:
            accuracy_value = None
        elif isinstance(accuracy, int):
            accuracy_value = accuracy
        else:
            accuracy_value = None

        base_power = entry.get("basePower")
        if category is MoveCategory.STATUS:
            base_power = None

        desc_entry = text.get(key, {})
        description = desc_entry.get("shortDesc") or desc_entry.get("desc")

        moves[key] = Move(
            name=entry.get("name", key),
            move_type=chart.resolve(entry["type"]),
            category=category,
            power=base_power if isinstance(base_power, int) else None,
            accuracy=accuracy_value,
            pp=entry.get("pp"),
            priority=entry.get("priority", 0),
            makes_contact=bool(entry.get("flags", {}).get("contact")),
            description=description,
        )
    return moves


def load_species(
    chart: TypeChart, abilities: Mapping[str, Ability], pokedex_path: Path | None = None
) -> dict[str, PokemonSpecies]:
    pokedex_data_path = pokedex_path or DATA_ROOT / "pokedex_data.json"
    pokedex = _load_json(pokedex_data_path)

    ability_by_slug = { _slug(ability.name): ability for ability in abilities.values() }

    def resolve_ability(name: str | None, *, hidden: bool = False) -> Ability | None:
        if not name:
            return None
        found = ability_by_slug.get(_slug(name))
        if found:
            if hidden and not found.is_hidden:
                return Ability(name=found.name, description=found.description, is_hidden=True)
            return found
        return Ability(name=name, description="", is_hidden=hidden)

    species: dict[str, PokemonSpecies] = {}
    for key, entry in pokedex.items():
        if "num" not in entry:
            # Skip aux entries like defaults or headers.
            continue
        ability_slots = entry.get("abilities", {})
        base_abilities = [
            resolve_ability(ability_slots.get(slot))
            for slot in ("0", "1")
            if ability_slots.get(slot)
        ]
        filtered_base = tuple(a for a in base_abilities if a is not None)
        hidden_ability = resolve_ability(ability_slots.get("H"), hidden=True)

        if not filtered_base and hidden_ability:
            filtered_base = (hidden_ability,)
            hidden_ability = None

        try:
            resolved_types = tuple(chart.resolve(t) for t in entry["types"])
        except KeyError:
            # Skip species that reference non-standard types (e.g. old placeholders like Bird).
            continue

        species[key] = PokemonSpecies(
            name=entry.get("name", key),
            national_dex=entry["num"],
            types=resolved_types,
            base_stats=Stats.from_mapping(entry["baseStats"]),
            abilities=filtered_base,
            hidden_ability=hidden_ability,
            weight_kg=entry.get("weightkg"),
            height_m=entry.get("heightm"),
            color=entry.get("color"),
            gender_ratio=entry.get("genderRatio"),
            egg_groups=tuple(entry.get("eggGroups", [])) or None,
            base_species=entry.get("baseSpecies"),
            forme=entry.get("forme"),
            other_formes=tuple(entry.get("otherFormes", [])) or None,
        )

    return species


@dataclass(slots=True)
class GameData:
    type_chart: TypeChart
    abilities: dict[str, Ability]
    items: dict[str, Item]
    moves: dict[str, Move]
    species: dict[str, PokemonSpecies]


def load_game_data(data_root: Path | None = None) -> GameData:
    root = data_root or DATA_ROOT
    type_chart = load_type_chart(root / "typechart_data.json")
    abilities = load_abilities(root / "abilities_text.json")
    items = load_items(root / "items_data.json", root / "items_text.json")
    moves = load_moves(type_chart, root / "moves_data.json", root / "moves_text.json")
    species = load_species(type_chart, abilities, root / "pokedex_data.json")
    return GameData(type_chart=type_chart, abilities=abilities, items=items, moves=moves, species=species)
