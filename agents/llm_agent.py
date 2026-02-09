"""LLM-based agent for Pokemon battles.

This module provides an agent that uses a Large Language Model to make decisions.
It converts observations and legal actions into text prompts and parses LLM responses.
"""
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple
import json
import re

from .base import Agent, Action, ActionKind


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients.

    Any LLM client that implements this protocol can be used with LLMAgent.
    """

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        ...


class LLMAgent(Agent):
    """Agent that uses an LLM to select actions.

    Handles:
    - Converting observations and legal actions to text prompts
    - Calling the LLM with the prompt
    - Parsing LLM output to extract action choice
    - Fallback handling for invalid/unclear responses

    The agent stores conversation history and can return reasoning
    for analysis and training data collection.
    """

    def __init__(
        self,
        llm_client: Callable[[str], str],
        name: str = "LLMAgent",
        observation_formatter: Optional[Callable[[Any, Dict], str]] = None,
        action_formatter: Optional[Callable[[List[Action], Dict], str]] = None,
        response_parser: Optional[Callable[[str, List[Action]], Tuple[Action, str]]] = None,
        system_prompt: Optional[str] = None,
        include_reasoning: bool = True,
        max_retries: int = 2,
        fallback_to_first: bool = True,
    ):
        """Initialize the LLM agent.

        Args:
            llm_client: Function that takes prompt and returns LLM response
            name: Agent name
            observation_formatter: Custom function to format observations as text
            action_formatter: Custom function to format actions as text
            response_parser: Custom function to parse LLM response to (Action, reasoning)
            system_prompt: Optional system prompt for the LLM
            include_reasoning: Whether to request reasoning in responses
            max_retries: Maximum retries on parse failure
            fallback_to_first: If True, fall back to first legal action on failure
        """
        super().__init__(name)
        self.llm_client = llm_client
        self._format_obs = observation_formatter or self._default_format_observation
        self._format_actions = action_formatter or self._default_format_actions
        self._parse_response = response_parser or self._default_parse_response
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.include_reasoning = include_reasoning
        self.max_retries = max_retries
        self.fallback_to_first = fallback_to_first

        # Conversation history for context
        self._history: List[Dict[str, str]] = []
        # Last reasoning for analysis
        self._last_reasoning: str = ""
        # Statistics
        self._total_calls = 0
        self._parse_failures = 0
        self._fallbacks = 0

    def _default_system_prompt(self) -> str:
        """Default system prompt for the LLM."""
        return """You are an expert Pokemon battle strategist. Your goal is to win battles by making optimal decisions.

When asked to choose an action:
1. Analyze the current battle state
2. Consider type matchups, stat changes, and field conditions
3. Choose the best action from the available options

Respond with your chosen action number and brief reasoning.
Format: ACTION: <number>
REASONING: <your reasoning>"""

    def _default_format_observation(self, observation: Any, info: Dict) -> str:
        """Format observation as text for the LLM.

        Args:
            observation: The observation (numpy array or dict)
            info: Additional info dict

        Returns:
            Text description of the battle state
        """
        lines = ["=== CURRENT BATTLE STATE ==="]

        if isinstance(observation, dict):
            if "turn" in observation:
                lines.append(f"Turn: {observation['turn']}")

            if "weather" in observation:
                lines.append(f"Weather: {observation['weather']}")

            if "terrain" in observation:
                lines.append(f"Terrain: {observation['terrain']}")

            if "your_active" in observation:
                lines.append("\nYour Active Pokemon:")
                for poke in observation["your_active"]:
                    lines.append(f"  - {poke.get('name', '???')}")
                    lines.append(f"    HP: {poke.get('hp', '?')}/{poke.get('max_hp', '?')}")
                    lines.append(f"    Type: {poke.get('type', '?')}")
                    if poke.get('status'):
                        lines.append(f"    Status: {poke['status']}")
                    if poke.get('moves'):
                        lines.append(f"    Moves: {', '.join(poke['moves'])}")

            if "opponent_active" in observation:
                lines.append("\nOpponent's Active Pokemon:")
                for poke in observation["opponent_active"]:
                    lines.append(f"  - {poke.get('name', '???')}")
                    lines.append(f"    HP: ~{poke.get('hp_ratio', 1.0):.0%}")
                    lines.append(f"    Type: {poke.get('type', '?')}")
                    if poke.get('status'):
                        lines.append(f"    Status: {poke['status']}")

            if "your_bench" in observation:
                lines.append("\nYour Bench:")
                for i, poke in enumerate(observation["your_bench"]):
                    lines.append(
                        f"  [{i}] {poke.get('name', '???')} - "
                        f"HP: {poke.get('hp', '?')}/{poke.get('max_hp', '?')}"
                    )

            if "side_conditions" in observation:
                lines.append(f"\nField Effects: {observation['side_conditions']}")

        else:
            # Fallback for numpy arrays or other formats
            lines.append(f"[Raw observation data - shape: {getattr(observation, 'shape', 'unknown')}]")

        return "\n".join(lines)

    def _default_format_actions(self, actions: List[Action], info: Dict) -> str:
        """Format actions as text for the LLM.

        Args:
            actions: List of legal actions
            info: Additional info (may contain move/pokemon names)

        Returns:
            Text listing of available actions
        """
        lines = ["=== AVAILABLE ACTIONS ==="]

        move_names = info.get("move_names", {})
        team_names = info.get("team_names", [])

        for i, action in enumerate(actions):
            if action.kind == ActionKind.MOVE:
                slot_moves = move_names.get(action.slot, [])
                move_name = slot_moves[action.arg] if action.arg < len(slot_moves) else f"Move {action.arg}"

                target_str = ""
                if action.target_side >= 0 and action.target_slot >= 0:
                    target_str = f" targeting opponent slot {action.target_slot}"

                lines.append(f"  [{i}] Use {move_name}{target_str}")

            elif action.kind == ActionKind.SWITCH:
                poke_name = team_names[action.arg] if action.arg < len(team_names) else f"Pokemon {action.arg}"
                lines.append(f"  [{i}] Switch to {poke_name}")

            else:  # PASS
                lines.append(f"  [{i}] Pass")

        return "\n".join(lines)

    def _default_parse_response(
        self,
        response: str,
        legal_actions: List[Action],
    ) -> Tuple[Action, str]:
        """Parse LLM response to extract action and reasoning.

        Args:
            response: Raw LLM response text
            legal_actions: List of legal actions

        Returns:
            Tuple of (selected Action, reasoning string)

        Raises:
            ValueError: If action cannot be parsed
        """
        reasoning = ""

        # Try to extract reasoning
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=ACTION:|$)', response, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        # Try to extract action number
        # Look for patterns like "ACTION: 2" or "[2]" or just "2" at the start
        action_patterns = [
            r'ACTION:\s*(\d+)',
            r'\[(\d+)\]',
            r'^(\d+)',
            r'choose\s+(?:option\s+)?(\d+)',
            r'select\s+(?:option\s+)?(\d+)',
        ]

        for pattern in action_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
            if match:
                action_idx = int(match.group(1))
                if 0 <= action_idx < len(legal_actions):
                    return legal_actions[action_idx], reasoning

        # If no reasoning extracted, use full response
        if not reasoning:
            reasoning = response.strip()

        raise ValueError(f"Could not parse action from response: {response[:200]}")

    def _build_prompt(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Dict,
    ) -> str:
        """Build the full prompt for the LLM.

        Args:
            observation: Current battle state
            legal_actions: List of legal actions
            info: Additional information

        Returns:
            Complete prompt string
        """
        obs_text = self._format_obs(observation, info)
        actions_text = self._format_actions(legal_actions, info)

        prompt_parts = [
            self.system_prompt,
            "",
            obs_text,
            "",
            actions_text,
            "",
        ]

        if self.include_reasoning:
            prompt_parts.append("Choose the best action. Respond with ACTION: <number> and REASONING: <explanation>")
        else:
            prompt_parts.append("Choose the best action. Respond with ACTION: <number>")

        return "\n".join(prompt_parts)

    def act(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> Action:
        """Select an action using the LLM.

        Args:
            observation: Current battle state
            legal_actions: List of legal actions
            info: Optional additional information

        Returns:
            Selected Action
        """
        if not legal_actions:
            raise ValueError("No legal actions available")

        info = info or {}
        prompt = self._build_prompt(observation, legal_actions, info)

        # Try to get valid response
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                self._total_calls += 1
                response = self.llm_client(prompt)

                action, reasoning = self._parse_response(response, legal_actions)
                self._last_reasoning = reasoning

                # Store in history
                self._history.append({
                    "prompt": prompt,
                    "response": response,
                    "reasoning": reasoning,
                    "action_idx": legal_actions.index(action) if action in legal_actions else -1,
                })

                return action

            except (ValueError, Exception) as e:
                self._parse_failures += 1
                last_error = e
                # Add error context to prompt for retry
                if attempt < self.max_retries:
                    prompt += f"\n\n[Previous response was invalid: {str(e)}. Please respond with a valid action number.]"

        # All retries failed
        if self.fallback_to_first:
            self._fallbacks += 1
            self._last_reasoning = f"Fallback due to parse failure: {last_error}"
            return legal_actions[0]
        else:
            raise ValueError(f"Failed to parse LLM response after {self.max_retries + 1} attempts: {last_error}")

    def get_last_reasoning(self) -> str:
        """Get the reasoning from the last action.

        Returns:
            Reasoning string, or empty if none
        """
        return self._last_reasoning

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history.

        Returns:
            List of prompt/response/reasoning dicts
        """
        return list(self._history)

    def reset(self) -> None:
        """Reset for new battle (clears history)."""
        self._history.clear()
        self._last_reasoning = ""

    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics.

        Returns:
            Dict with call counts and failure rates
        """
        return {
            "total_calls": self._total_calls,
            "parse_failures": self._parse_failures,
            "fallbacks": self._fallbacks,
        }


class MockLLMAgent(LLMAgent):
    """Mock LLM agent for testing.

    Returns pre-configured responses or uses simple heuristics.
    """

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        name: str = "MockLLM",
        **kwargs,
    ):
        """Initialize mock LLM agent.

        Args:
            responses: List of pre-configured responses (cycles through)
            name: Agent name
            **kwargs: Additional LLMAgent arguments
        """
        self._mock_responses = responses or []
        self._response_idx = 0

        def mock_client(prompt: str) -> str:
            if self._mock_responses:
                resp = self._mock_responses[self._response_idx % len(self._mock_responses)]
                self._response_idx += 1
                return resp
            else:
                # Default: return first action
                return "ACTION: 0\nREASONING: Default choice"

        super().__init__(llm_client=mock_client, name=name, **kwargs)
