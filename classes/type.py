from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class Type:
    """Represents a Pokémon typing with offensive matchups baked in."""

    name: str
    weaknesses: frozenset[str] = field(default_factory=frozenset)
    resistances: frozenset[str] = field(default_factory=frozenset)
    immunities: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        # Canonicalize to lowercase to keep comparisons simple.
        object.__setattr__(self, "name", self.name.lower())
        object.__setattr__(self, "weaknesses", frozenset(map(str.lower, self.weaknesses)))
        object.__setattr__(self, "resistances", frozenset(map(str.lower, self.resistances)))
        object.__setattr__(self, "immunities", frozenset(map(str.lower, self.immunities)))

    def multiplier_from(self, attack_type: Type | str) -> float:
        """Return the damage multiplier when hit by an attack of the given type."""
        attacking_name = attack_type.name if isinstance(attack_type, Type) else str(attack_type)
        attacking_name = attacking_name.lower()

        if attacking_name in self.immunities:
            return 0.0
        if attacking_name in self.weaknesses:
            return 2.0
        if attacking_name in self.resistances:
            return 0.5
        return 1.0

    def to_dict(self) -> dict[str, object]:
        """Serialize the type so it can be easily stored or sent over the wire."""
        return {
            "name": self.name,
            "weaknesses": sorted(self.weaknesses),
            "resistances": sorted(self.resistances),
            "immunities": sorted(self.immunities),
        }


class TypeChart:
    """Registry to keep types consistent and answer matchup questions."""

    def __init__(self, types: Iterable[Type] | None = None) -> None:
        self._types: dict[str, Type] = {}
        for type_ in types or []:
            self.register(type_)

    def register(self, type_: Type) -> None:
        self._types[type_.name] = type_

    def get(self, name: str) -> Type:
        return self._types[name.lower()]

    def resolve(self, ref: Type | str) -> Type:
        return ref if isinstance(ref, Type) else self.get(ref)

    def damage_multiplier(self, attack_type: Type | str, defenders: Iterable[Type | str]) -> float:
        attack = self.resolve(attack_type)
        multiplier = 1.0
        for defender in defenders:
            multiplier *= self.resolve(defender).multiplier_from(attack)
        return multiplier

    @classmethod
    def from_showdown_chart(cls, chart_data: Mapping[str, Mapping]) -> TypeChart:
        """Build a TypeChart from the Showdown-style damageTaken map found in the JSON/TS data."""
        instance = cls()
        # Only consider actual type keys to avoid entries like "powder", "prankster", etc.
        valid_types = {name.lower() for name in chart_data.keys()}

        for type_name, payload in chart_data.items():
            damage_taken = payload.get("damageTaken", {})
            weaknesses: set[str] = set()
            resistances: set[str] = set()
            immunities: set[str] = set()

            for attacker, code in damage_taken.items():
                attacker_name = attacker.lower()
                if attacker_name not in valid_types:
                    continue
                if code == 1:
                    weaknesses.add(attacker_name)
                elif code == 2:
                    resistances.add(attacker_name)
                elif code == 3:
                    immunities.add(attacker_name)

            instance.register(Type(name=type_name, weaknesses=weaknesses, resistances=resistances, immunities=immunities))

        return instance
