from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ability:
    """Battle ability such as Cursed Body or Levitate."""

    name: str
    description: str
    is_hidden: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "is_hidden": self.is_hidden,
        }

    def __str__(self) -> str:
        return self.name
