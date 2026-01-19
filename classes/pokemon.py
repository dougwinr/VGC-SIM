from __future__ import annotations

from dataclasses import dataclass, field
from math import floor
from typing import Iterable, Sequence

from .ability import Ability
from .item import Item
from .move import Move
from .type import Type, TypeChart


@dataclass(frozen=True, slots=True)
class Stats:
    """Container for the six battle stats."""

    hp: int
    atk: int
    defense: int
    spa: int
    spd: int
    spe: int

    def values(self) -> tuple[int, ...]:
        return (self.hp, self.atk, self.defense, self.spa, self.spd, self.spe)

    def to_dict(self) -> dict[str, int]:
        return {
            "hp": self.hp,
            "atk": self.atk,
            "defense": self.defense,
            "spa": self.spa,
            "spd": self.spd,
            "spe": self.spe,
        }

    @classmethod
    def from_mapping(cls, raw: dict[str, int]) -> Stats:
        """Build stats from the showdown-style dict in the JSON data."""
        return cls(
            hp=int(raw.get("hp", 0)),
            atk=int(raw.get("atk", 0)),
            defense=int(raw.get("def", raw.get("defense", 0))),
            spa=int(raw.get("spa", 0)),
            spd=int(raw.get("spd", 0)),
            spe=int(raw.get("spe", raw.get("speed", 0))),
        )

    @property
    def attack(self) -> int:
        return self.atk

    @property
    def sp_attack(self) -> int:
        return self.spa

    @property
    def sp_defense(self) -> int:
        return self.spd

    @property
    def speed(self) -> int:
        return self.spe

@dataclass(frozen=True, slots=True)
class PokemonSpecies:
    """Species template (e.g. Gengar) independent from player configuration."""

    name: str
    national_dex: int
    types: tuple[Type, ...]
    base_stats: Stats
    abilities: tuple[Ability, ...]
    hidden_ability: Ability | None = None
    weight_kg: float | None = None
    height_m: float | None = None
    color: str | None = None
    gender_ratio: dict[str, float] | None = None
    egg_groups: tuple[str, ...] | None = None
    base_species: str | None = None
    forme: str | None = None
    other_formes: tuple[str, ...] | None = None


def _default_ivs() -> Stats:
    return Stats(31, 31, 31, 31, 31, 31)


def _empty_evs() -> Stats:
    return Stats(0, 0, 0, 0, 0, 0)


@dataclass(slots=True)
class Pokemon:
    """Player-configured Pokémon ready to drop into a team."""

    species: PokemonSpecies
    level: int = 50
    ability: Ability | None = None
    moves: Sequence[Move] = field(default_factory=list)
    item: Item | None = None
    evs: Stats = field(default_factory=_empty_evs)
    ivs: Stats = field(default_factory=_default_ivs)
    nature_modifiers: dict[str, float] = field(default_factory=dict)
    tera_type: Type | None = None

    def __post_init__(self) -> None:
        # Default to the first listed ability if none supplied.
        if self.ability is None:
            self.ability = self.species.abilities[0]
        if len(self.moves) > 4:
            raise ValueError("A Pokémon cannot know more than four moves.")
        self._validate_evs()

    @property
    def active_types(self) -> tuple[Type, ...]:
        return (self.tera_type,) if self.tera_type else self.species.types

    def _validate_evs(self) -> None:
        total = sum(self.evs.values())
        if total > 510:
            raise ValueError("Total EVs may not exceed 510.")
        for value in self.evs.values():
            if value < 0 or value > 252:
                raise ValueError("EVs must be between 0 and 252.")

    def _calc_hp(self, base: int, iv: int, ev: int) -> int:
        return floor(((2 * base + iv + ev // 4) * self.level) / 100) + self.level + 10

    def _calc_other(self, base: int, iv: int, ev: int, nature: float) -> int:
        stat = floor(((2 * base + iv + ev // 4) * self.level) / 100) + 5
        return floor(stat * nature)

    def battle_stats(self) -> Stats:
        """Calculate the in-battle stats for this configuration."""
        nature = self.nature_modifiers
        base = self.species.base_stats

        def nat(key_long: str, key_short: str) -> float:
            return nature.get(key_long, nature.get(key_short, 1.0))

        return Stats(
            hp=self._calc_hp(base.hp, self.ivs.hp, self.evs.hp),
            atk=self._calc_other(base.atk, self.ivs.atk, self.evs.atk, nat("atk", "attack")),
            defense=self._calc_other(base.defense, self.ivs.defense, self.evs.defense, nat("defense", "def")),
            spa=self._calc_other(base.spa, self.ivs.spa, self.evs.spa, nat("spa", "sp_attack")),
            spd=self._calc_other(base.spd, self.ivs.spd, self.evs.spd, nat("spd", "sp_defense")),
            spe=self._calc_other(base.spe, self.ivs.spe, self.evs.spe, nat("spe", "speed")),
        )

    def type_multiplier_from(self, attack_type: Type | str, chart: TypeChart) -> float:
        """Helper to query damage taken given the active types and a chart."""
        return chart.damage_multiplier(attack_type, self.active_types)
