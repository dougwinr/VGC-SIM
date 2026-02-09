"""Human agent for interactive Pokemon battles.

This module provides an agent that bridges to human players via CLI/GUI/web.
It displays battle state and prompts for user input.
"""
from typing import Any, Callable, Dict, List, Optional

from .base import Agent, Action, ActionKind


def default_display_func(text: str) -> None:
    """Default display function using print."""
    print(text)


def default_input_func(prompt: str) -> str:
    """Default input function using input()."""
    return input(prompt)


class HumanAgent(Agent):
    """Agent that interacts with a human player.

    Displays observation and legal actions in human-readable format,
    waits for user input, and returns the corresponding Action.

    This agent is designed to work with various interfaces:
    - CLI: Uses default print/input
    - GUI: Can inject custom display/input callbacks
    - Web: Can use async callbacks for request/response
    """

    def __init__(
        self,
        name: str = "Human",
        display_func: Optional[Callable[[str], None]] = None,
        input_func: Optional[Callable[[str], str]] = None,
        observation_formatter: Optional[Callable[[Any], str]] = None,
    ):
        """Initialize the human agent.

        Args:
            name: Name for this player
            display_func: Function to display text (default: print)
            input_func: Function to get user input (default: input)
            observation_formatter: Optional function to format observations
        """
        super().__init__(name)
        self._display = display_func or default_display_func
        self._input = input_func or default_input_func
        self._format_obs = observation_formatter or self._default_format_observation

    def _default_format_observation(self, observation: Any) -> str:
        """Default observation formatter.

        Args:
            observation: The observation to format

        Returns:
            Human-readable string representation
        """
        # If observation is a dict with structured info, format it nicely
        if isinstance(observation, dict):
            lines = ["=== Battle State ==="]

            if "turn" in observation:
                lines.append(f"Turn: {observation['turn']}")

            if "weather" in observation:
                lines.append(f"Weather: {observation['weather']}")

            if "terrain" in observation:
                lines.append(f"Terrain: {observation['terrain']}")

            if "your_pokemon" in observation:
                lines.append("\nYour Pokemon:")
                for i, poke in enumerate(observation["your_pokemon"]):
                    active = "(active)" if poke.get("active") else ""
                    lines.append(
                        f"  {i}: {poke.get('name', '???')} "
                        f"HP: {poke.get('hp', '?')}/{poke.get('max_hp', '?')} {active}"
                    )

            if "opponent_pokemon" in observation:
                lines.append("\nOpponent Pokemon:")
                for i, poke in enumerate(observation["opponent_pokemon"]):
                    active = "(active)" if poke.get("active") else ""
                    lines.append(
                        f"  {i}: {poke.get('name', '???')} "
                        f"HP: {poke.get('hp_ratio', '?'):.0%} {active}"
                    )

            return "\n".join(lines)
        else:
            # Fallback: just use str representation
            return f"Observation: {observation}"

    def _format_action(self, action: Action, index: int, info: Optional[Dict] = None) -> str:
        """Format an action for display.

        Args:
            action: The action to format
            index: Index of this action in the list
            info: Optional info dict with move/pokemon names

        Returns:
            Human-readable action string
        """
        if action.kind == ActionKind.MOVE:
            move_name = "Move"
            if info and "move_names" in info:
                move_names = info["move_names"].get(action.slot, [])
                if action.arg < len(move_names):
                    move_name = move_names[action.arg]
            target_str = ""
            if action.target_side >= 0 and action.target_slot >= 0:
                target_str = f" -> ({action.target_side}, {action.target_slot})"
            return f"{index}: Use {move_name}{target_str}"

        elif action.kind == ActionKind.SWITCH:
            pokemon_name = f"Pokemon {action.arg}"
            if info and "team_names" in info:
                team_names = info.get("team_names", [])
                if action.arg < len(team_names):
                    pokemon_name = team_names[action.arg]
            return f"{index}: Switch to {pokemon_name}"

        else:  # PASS
            return f"{index}: Pass"

    def act(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> Action:
        """Get action from human player.

        Displays observation and legal actions, then prompts for input.

        Args:
            observation: Current battle state
            legal_actions: List of legal actions
            info: Optional info dict (may contain move/pokemon names)

        Returns:
            The chosen Action
        """
        # Display current state
        self._display(self._format_obs(observation))
        self._display("")

        # Display legal actions
        self._display("Available actions:")
        for i, action in enumerate(legal_actions):
            self._display(f"  {self._format_action(action, i, info)}")
        self._display("")

        # Get user input
        while True:
            try:
                choice_str = self._input("Enter action number: ")
                choice = int(choice_str.strip())

                if 0 <= choice < len(legal_actions):
                    return legal_actions[choice]
                else:
                    self._display(f"Invalid choice. Please enter 0-{len(legal_actions) - 1}")
            except ValueError:
                self._display("Please enter a number.")
            except KeyboardInterrupt:
                # Allow graceful exit
                self._display("\nExiting...")
                raise

    def reset(self) -> None:
        """Reset for new battle."""
        pass

    def on_battle_end(self, winner: int, info: Dict[str, Any]) -> None:
        """Display battle result."""
        if "side" in info:
            if winner == info["side"]:
                self._display("You won!")
            elif winner >= 0:
                self._display("You lost!")
            else:
                self._display("It's a draw!")


class AsyncHumanAgent(HumanAgent):
    """Asynchronous human agent for non-blocking interfaces.

    This variant uses callbacks instead of blocking input, suitable for
    web interfaces or GUIs that need async interaction.
    """

    def __init__(
        self,
        name: str = "Human",
        display_func: Optional[Callable[[str], None]] = None,
        observation_formatter: Optional[Callable[[Any], str]] = None,
    ):
        """Initialize async human agent.

        Note: input_func is not used; instead call set_response() to provide input.
        """
        super().__init__(name, display_func, lambda _: "", observation_formatter)
        self._pending_actions: Optional[List[Action]] = None
        self._response: Optional[int] = None

    def request_action(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Request an action from the human player.

        Call this to display state and options. The response will be
        provided later via set_response().

        Args:
            observation: Current battle state
            legal_actions: List of legal actions
            info: Optional info dict
        """
        self._display(self._format_obs(observation))
        self._display("")
        self._display("Available actions:")
        for i, action in enumerate(legal_actions):
            self._display(f"  {self._format_action(action, i, info)}")

        self._pending_actions = legal_actions
        self._response = None

    def set_response(self, choice: int) -> bool:
        """Set the human player's response.

        Args:
            choice: Index of chosen action

        Returns:
            True if valid, False if invalid
        """
        if self._pending_actions is None:
            return False
        if not (0 <= choice < len(self._pending_actions)):
            return False

        self._response = choice
        return True

    def get_chosen_action(self) -> Optional[Action]:
        """Get the chosen action if response has been set.

        Returns:
            The chosen Action, or None if no valid response yet
        """
        if self._response is not None and self._pending_actions is not None:
            return self._pending_actions[self._response]
        return None

    def act(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> Action:
        """Act method for async agent.

        For async usage, prefer request_action/set_response/get_chosen_action.
        This method raises an error if called without a pending response.
        """
        if self._response is not None and self._pending_actions is legal_actions:
            return legal_actions[self._response]

        raise RuntimeError(
            "AsyncHumanAgent.act() called without pending response. "
            "Use request_action() and set_response() for async interaction."
        )
