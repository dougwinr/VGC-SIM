from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .type import Type


class MoveCategory(str, Enum):
    PHYSICAL = "physical"
    SPECIAL = "special"
    STATUS = "status"


@dataclass(slots=True)
class Move:
    """A move known by a Pokémon."""

    name: str
    move_type: Type
    category: MoveCategory
    power: Optional[int] = None
    accuracy: Optional[int] = None  # Percent; None represents always hitting.
    pp: Optional[int] = None
    priority: int = 0
    makes_contact: bool = False
    description: str | None = None

    def is_status(self) -> bool:
        return self.category is MoveCategory.STATUS

    def accuracy_chance(self) -> float:
        """Return accuracy as a 0-1 value; status moves often omit accuracy."""
        if self.accuracy is None:
            return 1.0
        return self.accuracy / 100

    def to_dict(self) -> dict[str, object | None]:
        return {
            "name": self.name,
            "type": self.move_type.name,
            "category": self.category.value,
            "power": self.power,
            "accuracy": self.accuracy,
            "pp": self.pp,
            "priority": self.priority,
            "makes_contact": self.makes_contact,
            "description": self.description,
        }
