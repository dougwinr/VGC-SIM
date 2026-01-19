from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Item:
    """Held item used during battle (e.g. Choice Specs)."""

    name: str
    description: str
    consumable: bool = False
    category: str | None = None

    def to_dict(self) -> dict[str, object | None]:
        return {
            "name": self.name,
            "description": self.description,
            "consumable": self.consumable,
            "category": self.category,
        }

    def __str__(self) -> str:
        return self.name
