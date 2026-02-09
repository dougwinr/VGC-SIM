"""Base agent interface for Pokemon battle agents.

This module defines the common Agent interface that all player types implement,
along with the Action dataclass used to represent player choices.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional


class ActionKind(IntEnum):
    """Types of actions a player can take."""
    MOVE = 0       # Use a move
    SWITCH = 1     # Switch Pokemon
    PASS = 2       # Pass/do nothing (forced by game state)


@dataclass(frozen=True, slots=True)
class Action:
    """A player action for a single active Pokemon.

    This is the agent-facing action representation, distinct from the
    internal core.Action used by the battle engine.

    Attributes:
        kind: The type of action (MOVE, SWITCH, PASS)
        slot: Active slot index (0 for singles, 0-1 for doubles)
        arg: Context-dependent argument:
            - For MOVE: move slot index (0-3)
            - For SWITCH: team slot to switch to (0-5)
            - For PASS: unused (0)
        target_side: Target side index for moves (0 or 1, -1 for self/no target)
        target_slot: Target's active slot for moves (0-1, -1 for no specific target)
    """
    kind: int
    slot: int
    arg: int = 0
    target_side: int = -1
    target_slot: int = -1

    @classmethod
    def move(cls, slot: int, move_slot: int, target_side: int = -1, target_slot: int = -1) -> "Action":
        """Create a move action.

        Args:
            slot: Active slot index
            move_slot: Move slot to use (0-3)
            target_side: Side of target (-1 for no specific target)
            target_slot: Active slot of target (-1 for no specific target)
        """
        return cls(
            kind=ActionKind.MOVE,
            slot=slot,
            arg=move_slot,
            target_side=target_side,
            target_slot=target_slot,
        )

    @classmethod
    def switch(cls, slot: int, switch_to: int) -> "Action":
        """Create a switch action.

        Args:
            slot: Active slot index of the Pokemon switching out
            switch_to: Team slot index to switch to (0-5)
        """
        return cls(
            kind=ActionKind.SWITCH,
            slot=slot,
            arg=switch_to,
        )

    @classmethod
    def pass_action(cls, slot: int) -> "Action":
        """Create a pass action.

        Args:
            slot: Active slot index
        """
        return cls(
            kind=ActionKind.PASS,
            slot=slot,
        )


class Agent(ABC):
    """Abstract base class for battle agents.

    All player types (human, RL, LLM, heuristic) implement this interface.
    The agent receives observations and legal actions, and returns a chosen action.
    """

    def __init__(self, name: str = "Agent"):
        """Initialize the agent.

        Args:
            name: A name for this agent (for logging/display)
        """
        self.name = name

    @abstractmethod
    def act(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> Action:
        """Select an action given the current state.

        Args:
            observation: The current battle observation (format depends on env config)
            legal_actions: List of legal Action objects the agent can choose from
            info: Optional additional information (e.g., side index, turn number)

        Returns:
            A single Action from legal_actions
        """
        pass

    def reset(self) -> None:
        """Reset agent state for a new battle.

        Called at the start of each new battle. Override to clear any
        episode-specific state (e.g., conversation history for LLM agents).
        """
        pass

    def on_battle_end(self, winner: int, info: Dict[str, Any]) -> None:
        """Called when a battle ends.

        Args:
            winner: Index of winning side (-1 for draw)
            info: Additional end-of-battle information

        Override to perform any end-of-battle processing (e.g., logging,
        updating statistics, learning from outcome).
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
