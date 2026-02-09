"""Heuristic-based agent for Pokemon battles.

This module provides agents that use hand-coded rules and scoring functions
to select actions. Useful as baselines, training opponents, or simple bots.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from .base import Agent, Action, ActionKind


class HeuristicAgent(Agent):
    """Agent that uses scoring heuristics to select actions.

    Scores each legal action based on configurable criteria and selects
    the highest-scoring action (with optional randomization for ties).

    This class provides a framework for heuristic-based decision making.
    Override score_action() for custom scoring logic.
    """

    def __init__(
        self,
        name: str = "Heuristic",
        score_func: Optional[Callable[[Action, Any, Dict], float]] = None,
        tie_break: str = "first",  # "first", "random", "last"
        seed: Optional[int] = None,
    ):
        """Initialize heuristic agent.

        Args:
            name: Agent name
            score_func: Custom scoring function (action, obs, info) -> score
            tie_break: How to break ties ("first", "random", "last")
            seed: Random seed for tie-breaking
        """
        super().__init__(name)
        self._score_func = score_func
        self.tie_break = tie_break
        self._rng = np.random.default_rng(seed)

    def score_action(
        self,
        action: Action,
        observation: Any,
        info: Dict,
    ) -> float:
        """Score an action based on heuristics.

        Override this method for custom scoring logic.

        Args:
            action: The action to score
            observation: Current battle state
            info: Additional information

        Returns:
            Numeric score (higher = better)
        """
        if self._score_func:
            return self._score_func(action, observation, info)

        # Default: prefer moves over switches, no other preference
        if action.kind == ActionKind.MOVE:
            return 1.0
        elif action.kind == ActionKind.SWITCH:
            return 0.5
        else:  # PASS
            return 0.0

    def act(
        self,
        observation: Any,
        legal_actions: List[Action],
        info: Optional[Dict[str, Any]] = None,
    ) -> Action:
        """Select action with highest score.

        Args:
            observation: Current battle state
            legal_actions: List of legal actions
            info: Optional additional information

        Returns:
            Highest-scoring Action
        """
        if not legal_actions:
            raise ValueError("No legal actions available")

        info = info or {}

        # Score all actions
        scores = [
            (action, self.score_action(action, observation, info))
            for action in legal_actions
        ]

        # Find maximum score
        max_score = max(s for _, s in scores)

        # Get all actions with max score
        best_actions = [a for a, s in scores if s == max_score]

        # Tie-break
        if len(best_actions) == 1:
            return best_actions[0]
        elif self.tie_break == "random":
            return best_actions[self._rng.integers(0, len(best_actions))]
        elif self.tie_break == "last":
            return best_actions[-1]
        else:  # "first"
            return best_actions[0]


class TypeMatchupAgent(HeuristicAgent):
    """Heuristic agent that considers type matchups.

    Scores moves based on type effectiveness against the opponent.
    """

    # Type effectiveness chart (simplified, partial)
    # Maps (attack_type, defend_type) -> effectiveness multiplier
    TYPE_CHART = {
        # Fire
        ("fire", "grass"): 2.0,
        ("fire", "ice"): 2.0,
        ("fire", "bug"): 2.0,
        ("fire", "steel"): 2.0,
        ("fire", "water"): 0.5,
        ("fire", "rock"): 0.5,
        ("fire", "fire"): 0.5,
        ("fire", "dragon"): 0.5,
        # Water
        ("water", "fire"): 2.0,
        ("water", "ground"): 2.0,
        ("water", "rock"): 2.0,
        ("water", "water"): 0.5,
        ("water", "grass"): 0.5,
        ("water", "dragon"): 0.5,
        # Grass
        ("grass", "water"): 2.0,
        ("grass", "ground"): 2.0,
        ("grass", "rock"): 2.0,
        ("grass", "fire"): 0.5,
        ("grass", "grass"): 0.5,
        ("grass", "poison"): 0.5,
        ("grass", "flying"): 0.5,
        ("grass", "bug"): 0.5,
        ("grass", "dragon"): 0.5,
        ("grass", "steel"): 0.5,
        # Electric
        ("electric", "water"): 2.0,
        ("electric", "flying"): 2.0,
        ("electric", "electric"): 0.5,
        ("electric", "grass"): 0.5,
        ("electric", "dragon"): 0.5,
        ("electric", "ground"): 0.0,
        # Ground
        ("ground", "fire"): 2.0,
        ("ground", "electric"): 2.0,
        ("ground", "poison"): 2.0,
        ("ground", "rock"): 2.0,
        ("ground", "steel"): 2.0,
        ("ground", "grass"): 0.5,
        ("ground", "bug"): 0.5,
        ("ground", "flying"): 0.0,
        # Fighting
        ("fighting", "normal"): 2.0,
        ("fighting", "ice"): 2.0,
        ("fighting", "rock"): 2.0,
        ("fighting", "dark"): 2.0,
        ("fighting", "steel"): 2.0,
        ("fighting", "poison"): 0.5,
        ("fighting", "flying"): 0.5,
        ("fighting", "psychic"): 0.5,
        ("fighting", "bug"): 0.5,
        ("fighting", "fairy"): 0.5,
        ("fighting", "ghost"): 0.0,
        # Psychic
        ("psychic", "fighting"): 2.0,
        ("psychic", "poison"): 2.0,
        ("psychic", "psychic"): 0.5,
        ("psychic", "steel"): 0.5,
        ("psychic", "dark"): 0.0,
        # Ghost
        ("ghost", "psychic"): 2.0,
        ("ghost", "ghost"): 2.0,
        ("ghost", "dark"): 0.5,
        ("ghost", "normal"): 0.0,
        # Dragon
        ("dragon", "dragon"): 2.0,
        ("dragon", "steel"): 0.5,
        ("dragon", "fairy"): 0.0,
        # Dark
        ("dark", "psychic"): 2.0,
        ("dark", "ghost"): 2.0,
        ("dark", "fighting"): 0.5,
        ("dark", "dark"): 0.5,
        ("dark", "fairy"): 0.5,
        # Fairy
        ("fairy", "fighting"): 2.0,
        ("fairy", "dragon"): 2.0,
        ("fairy", "dark"): 2.0,
        ("fairy", "fire"): 0.5,
        ("fairy", "poison"): 0.5,
        ("fairy", "steel"): 0.5,
        # Normal
        ("normal", "rock"): 0.5,
        ("normal", "steel"): 0.5,
        ("normal", "ghost"): 0.0,
        # Ice
        ("ice", "grass"): 2.0,
        ("ice", "ground"): 2.0,
        ("ice", "flying"): 2.0,
        ("ice", "dragon"): 2.0,
        ("ice", "fire"): 0.5,
        ("ice", "water"): 0.5,
        ("ice", "ice"): 0.5,
        ("ice", "steel"): 0.5,
        # Steel
        ("steel", "ice"): 2.0,
        ("steel", "rock"): 2.0,
        ("steel", "fairy"): 2.0,
        ("steel", "fire"): 0.5,
        ("steel", "water"): 0.5,
        ("steel", "electric"): 0.5,
        ("steel", "steel"): 0.5,
    }

    def __init__(
        self,
        name: str = "TypeMatchup",
        base_power_weight: float = 0.01,
        effectiveness_weight: float = 1.0,
        switch_penalty: float = -0.3,
        **kwargs,
    ):
        """Initialize type matchup agent.

        Args:
            name: Agent name
            base_power_weight: Weight for move base power
            effectiveness_weight: Weight for type effectiveness
            switch_penalty: Penalty for switching
            **kwargs: Additional HeuristicAgent arguments
        """
        super().__init__(name=name, **kwargs)
        self.base_power_weight = base_power_weight
        self.effectiveness_weight = effectiveness_weight
        self.switch_penalty = switch_penalty

    def _get_type_effectiveness(
        self,
        attack_type: str,
        defend_type1: str,
        defend_type2: Optional[str] = None,
    ) -> float:
        """Calculate type effectiveness multiplier.

        Args:
            attack_type: Attack type (lowercase)
            defend_type1: Defender's primary type
            defend_type2: Defender's secondary type (optional)

        Returns:
            Effectiveness multiplier (0.0, 0.25, 0.5, 1.0, 2.0, or 4.0)
        """
        attack_type = attack_type.lower()
        defend_type1 = defend_type1.lower()

        mult1 = self.TYPE_CHART.get((attack_type, defend_type1), 1.0)

        if defend_type2:
            defend_type2 = defend_type2.lower()
            mult2 = self.TYPE_CHART.get((attack_type, defend_type2), 1.0)
            return mult1 * mult2

        return mult1

    def score_action(
        self,
        action: Action,
        observation: Any,
        info: Dict,
    ) -> float:
        """Score action based on type matchups.

        Args:
            action: The action to score
            observation: Battle state with type info
            info: Additional info with move data

        Returns:
            Numeric score
        """
        if action.kind == ActionKind.PASS:
            return -1.0

        if action.kind == ActionKind.SWITCH:
            return self.switch_penalty

        # MOVE action
        score = 0.0

        # Get move info
        move_info = info.get("moves", {}).get(action.slot, [])
        if action.arg < len(move_info):
            move_data = move_info[action.arg]
            move_type = move_data.get("type", "normal")
            base_power = move_data.get("power", 50)

            # Add base power contribution
            score += base_power * self.base_power_weight

            # Get opponent type info
            opponent_types = info.get("opponent_types", [("normal", None)])
            if opponent_types:
                # Use first opponent's types (or target if specified)
                target_idx = action.target_slot if action.target_slot >= 0 else 0
                if target_idx < len(opponent_types):
                    type1, type2 = opponent_types[target_idx]
                    effectiveness = self._get_type_effectiveness(move_type, type1, type2)
                    score += effectiveness * self.effectiveness_weight

        return score


class MaxDamageAgent(HeuristicAgent):
    """Heuristic agent that maximizes expected damage.

    Considers base power, STAB, type effectiveness, and stat stages.
    """

    def __init__(
        self,
        name: str = "MaxDamage",
        stab_bonus: float = 1.5,
        crit_chance: float = 0.0625,
        crit_mult: float = 1.5,
        **kwargs,
    ):
        """Initialize max damage agent.

        Args:
            name: Agent name
            stab_bonus: Same-type attack bonus multiplier
            crit_chance: Critical hit probability
            crit_mult: Critical hit multiplier
            **kwargs: Additional HeuristicAgent arguments
        """
        super().__init__(name=name, **kwargs)
        self.stab_bonus = stab_bonus
        self.crit_chance = crit_chance
        self.crit_mult = crit_mult

    def score_action(
        self,
        action: Action,
        observation: Any,
        info: Dict,
    ) -> float:
        """Score action based on expected damage.

        Args:
            action: The action to score
            observation: Battle state
            info: Move/Pokemon data

        Returns:
            Estimated damage value
        """
        if action.kind != ActionKind.MOVE:
            return 0.0

        move_info = info.get("moves", {}).get(action.slot, [])
        if action.arg >= len(move_info):
            return 0.0

        move_data = move_info[action.arg]

        # Base power
        base_power = move_data.get("power", 0)
        if base_power == 0:
            # Status move - small positive score
            return 0.1

        # STAB check
        move_type = move_data.get("type", "normal")
        user_types = info.get("user_types", [])
        stab = self.stab_bonus if move_type in user_types else 1.0

        # Type effectiveness
        opponent_types = info.get("opponent_types", [("normal", None)])
        target_idx = action.target_slot if action.target_slot >= 0 else 0
        effectiveness = 1.0
        if target_idx < len(opponent_types):
            type1, type2 = opponent_types[target_idx]
            effectiveness = TypeMatchupAgent._get_type_effectiveness(
                self, move_type, type1, type2
            )

        # Expected damage (simplified formula)
        expected_damage = base_power * stab * effectiveness

        # Account for critical hits
        expected_damage *= (1.0 + self.crit_chance * (self.crit_mult - 1.0))

        return expected_damage


class DefensiveAgent(HeuristicAgent):
    """Heuristic agent that prioritizes survival.

    Prefers defensive moves, switches when HP is low, and avoids bad matchups.
    """

    def __init__(
        self,
        name: str = "Defensive",
        hp_threshold: float = 0.3,
        switch_bonus: float = 0.5,
        heal_bonus: float = 2.0,
        protect_bonus: float = 0.8,
        **kwargs,
    ):
        """Initialize defensive agent.

        Args:
            name: Agent name
            hp_threshold: HP ratio below which to consider switching
            switch_bonus: Bonus for switching when HP is low
            heal_bonus: Bonus for healing moves
            protect_bonus: Bonus for protection moves
            **kwargs: Additional HeuristicAgent arguments
        """
        super().__init__(name=name, **kwargs)
        self.hp_threshold = hp_threshold
        self.switch_bonus = switch_bonus
        self.heal_bonus = heal_bonus
        self.protect_bonus = protect_bonus

    def score_action(
        self,
        action: Action,
        observation: Any,
        info: Dict,
    ) -> float:
        """Score action with defensive priorities.

        Args:
            action: The action to score
            observation: Battle state
            info: Move/Pokemon data

        Returns:
            Defensive score
        """
        score = 0.0

        # Get current HP ratio
        hp_ratio = info.get("hp_ratio", 1.0)

        if action.kind == ActionKind.SWITCH:
            # Switching is better when HP is low
            if hp_ratio < self.hp_threshold:
                score += self.switch_bonus * (1.0 - hp_ratio)
            else:
                score -= 0.2  # Small penalty for unnecessary switches

        elif action.kind == ActionKind.MOVE:
            move_info = info.get("moves", {}).get(action.slot, [])
            if action.arg < len(move_info):
                move_data = move_info[action.arg]
                flags = move_data.get("flags", [])

                # Bonus for healing moves
                if "heal" in flags or move_data.get("drain", 0) > 0:
                    score += self.heal_bonus * (1.0 - hp_ratio)

                # Bonus for protection moves
                if "protect" in flags:
                    score += self.protect_bonus

                # Small bonus for damaging moves
                if move_data.get("power", 0) > 0:
                    score += 0.3

        return score


class CompositeAgent(HeuristicAgent):
    """Agent that combines multiple scoring strategies.

    Useful for creating balanced agents that consider multiple factors.
    """

    def __init__(
        self,
        agents: List[Tuple[Agent, float]],
        name: str = "Composite",
        **kwargs,
    ):
        """Initialize composite agent.

        Args:
            agents: List of (agent, weight) tuples
            name: Agent name
            **kwargs: Additional HeuristicAgent arguments
        """
        super().__init__(name=name, **kwargs)
        self.sub_agents = agents

    def score_action(
        self,
        action: Action,
        observation: Any,
        info: Dict,
    ) -> float:
        """Score action using weighted combination of sub-agents.

        Args:
            action: The action to score
            observation: Battle state
            info: Additional info

        Returns:
            Weighted average score
        """
        total_score = 0.0
        total_weight = 0.0

        for agent, weight in self.sub_agents:
            if isinstance(agent, HeuristicAgent):
                score = agent.score_action(action, observation, info)
                total_score += score * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0
