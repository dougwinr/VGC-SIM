"""Evaluation utilities for comparing agents and computing metrics.

This module provides tools for:
- Running evaluation matches between agents
- Computing win rates and confidence intervals
- Tracking and comparing agent performance over time
- Statistical significance testing
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
from collections import defaultdict

from agents.base import Agent
from .env import BattleEnv, EnvConfig


@dataclass
class MatchResult:
    """Result of a single match between two agents."""
    winner: int  # -1 for draw, 0 or 1 for winner side
    turns: int
    total_reward: Dict[int, float] = field(default_factory=dict)
    seed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Aggregated results from an evaluation run."""
    agent_names: Tuple[str, str]
    num_matches: int
    wins: Tuple[int, int]  # (side_0_wins, side_1_wins)
    draws: int
    win_rates: Tuple[float, float]
    avg_turns: float
    avg_rewards: Tuple[float, float]
    std_rewards: Tuple[float, float]
    match_results: List[MatchResult] = field(default_factory=list)

    @property
    def win_rate_0(self) -> float:
        """Win rate for side 0."""
        return self.win_rates[0]

    @property
    def win_rate_1(self) -> float:
        """Win rate for side 1."""
        return self.win_rates[1]

    def confidence_interval(
        self,
        side: int,
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        """Compute confidence interval for win rate.

        Uses Wilson score interval for binomial proportion.

        Args:
            side: Side index (0 or 1)
            confidence: Confidence level (default 0.95)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        from scipy import stats

        n = self.num_matches
        if n == 0:
            return (0.0, 1.0)

        p = self.win_rates[side]
        z = stats.norm.ppf(1 - (1 - confidence) / 2)

        # Wilson score interval
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator

        return (max(0, center - margin), min(1, center + margin))

    def summary(self) -> str:
        """Generate a summary string."""
        lines = [
            f"Evaluation: {self.agent_names[0]} vs {self.agent_names[1]}",
            f"Matches: {self.num_matches}",
            f"Results: {self.wins[0]}-{self.wins[1]}-{self.draws} (W-L-D for {self.agent_names[0]})",
            f"Win rates: {self.win_rates[0]:.1%} vs {self.win_rates[1]:.1%}",
            f"Avg turns: {self.avg_turns:.1f}",
            f"Avg rewards: {self.avg_rewards[0]:.3f} vs {self.avg_rewards[1]:.3f}",
        ]
        return "\n".join(lines)


class Evaluator:
    """Runs evaluation matches between agents.

    Handles:
    - Running multiple matches with different seeds
    - Swapping sides for fairness
    - Computing aggregate statistics
    - Progress callbacks
    """

    def __init__(
        self,
        config: Optional[EnvConfig] = None,
        move_registry: Optional[Dict[int, Any]] = None,
        team_generator: Optional[Callable[[int], Any]] = None,
    ):
        """Initialize evaluator.

        Args:
            config: Environment configuration
            move_registry: Move data registry
            team_generator: Team generation function
        """
        self.config = config or EnvConfig()
        self._move_registry = move_registry
        self._team_generator = team_generator

    def evaluate(
        self,
        agent_0: Agent,
        agent_1: Agent,
        num_matches: int = 100,
        swap_sides: bool = True,
        seeds: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        verbose: bool = False,
    ) -> EvaluationResult:
        """Run evaluation matches between two agents.

        Args:
            agent_0: First agent
            agent_1: Second agent
            num_matches: Number of matches to run
            swap_sides: If True, play half matches with swapped sides
            seeds: Optional list of seeds (will generate if None)
            progress_callback: Optional callback(completed, total)
            verbose: Print progress

        Returns:
            EvaluationResult with aggregated statistics
        """
        if seeds is None:
            rng = np.random.default_rng()
            seeds = [int(rng.integers(0, 2**31)) for _ in range(num_matches)]

        results: List[MatchResult] = []

        for i in range(num_matches):
            seed = seeds[i % len(seeds)]

            # Determine side assignment
            if swap_sides and i >= num_matches // 2:
                # Swap sides for second half
                player_map = {0: agent_1, 1: agent_0}
                swapped = True
            else:
                player_map = {0: agent_0, 1: agent_1}
                swapped = False

            # Create environment and run match
            env = BattleEnv(
                player_map=player_map,
                config=self.config,
                move_registry=self._move_registry,
                team_generator=self._team_generator,
            )

            winner, battle_log = env.run_battle(seed=seed)

            # Adjust winner for swapped sides
            if swapped and winner >= 0:
                winner = 1 - winner

            # Collect rewards
            total_rewards = {0: 0.0, 1: 0.0}
            # Note: Would need to track rewards during battle for accurate totals

            result = MatchResult(
                winner=winner,
                turns=env._turn,
                total_reward=total_rewards,
                seed=seed,
                metadata={"swapped": swapped},
            )
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, num_matches)

            if verbose and (i + 1) % 10 == 0:
                print(f"Completed {i + 1}/{num_matches} matches")

        return self._aggregate_results(agent_0.name, agent_1.name, results)

    def _aggregate_results(
        self,
        name_0: str,
        name_1: str,
        results: List[MatchResult],
    ) -> EvaluationResult:
        """Aggregate match results into statistics."""
        num_matches = len(results)

        wins_0 = sum(1 for r in results if r.winner == 0)
        wins_1 = sum(1 for r in results if r.winner == 1)
        draws = sum(1 for r in results if r.winner < 0)

        win_rate_0 = wins_0 / num_matches if num_matches > 0 else 0
        win_rate_1 = wins_1 / num_matches if num_matches > 0 else 0

        turns = [r.turns for r in results]
        avg_turns = np.mean(turns) if turns else 0

        rewards_0 = [r.total_reward.get(0, 0) for r in results]
        rewards_1 = [r.total_reward.get(1, 0) for r in results]

        return EvaluationResult(
            agent_names=(name_0, name_1),
            num_matches=num_matches,
            wins=(wins_0, wins_1),
            draws=draws,
            win_rates=(win_rate_0, win_rate_1),
            avg_turns=avg_turns,
            avg_rewards=(np.mean(rewards_0), np.mean(rewards_1)),
            std_rewards=(np.std(rewards_0), np.std(rewards_1)),
            match_results=results,
        )

    def round_robin(
        self,
        agents: List[Agent],
        matches_per_pair: int = 20,
        **kwargs,
    ) -> Dict[Tuple[str, str], EvaluationResult]:
        """Run round-robin tournament between multiple agents.

        Args:
            agents: List of agents to compete
            matches_per_pair: Matches between each pair
            **kwargs: Additional arguments for evaluate()

        Returns:
            Dict mapping (agent_0_name, agent_1_name) -> EvaluationResult
        """
        results = {}

        for i, agent_0 in enumerate(agents):
            for agent_1 in agents[i + 1:]:
                result = self.evaluate(
                    agent_0, agent_1,
                    num_matches=matches_per_pair,
                    **kwargs,
                )
                results[(agent_0.name, agent_1.name)] = result

        return results

    def compute_elo(
        self,
        results: Dict[Tuple[str, str], EvaluationResult],
        initial_elo: float = 1500,
        k_factor: float = 32,
    ) -> Dict[str, float]:
        """Compute Elo ratings from round-robin results.

        Args:
            results: Round-robin results dict
            initial_elo: Starting Elo rating
            k_factor: Elo K-factor

        Returns:
            Dict mapping agent name -> Elo rating
        """
        # Collect all agent names
        agents = set()
        for (a, b) in results.keys():
            agents.add(a)
            agents.add(b)

        elo = {name: initial_elo for name in agents}

        # Process each match result
        for (name_0, name_1), result in results.items():
            for match in result.match_results:
                if match.winner < 0:
                    score_0, score_1 = 0.5, 0.5
                elif match.winner == 0:
                    score_0, score_1 = 1.0, 0.0
                else:
                    score_0, score_1 = 0.0, 1.0

                # Expected scores
                exp_0 = 1 / (1 + 10 ** ((elo[name_1] - elo[name_0]) / 400))
                exp_1 = 1 - exp_0

                # Update ratings
                elo[name_0] += k_factor * (score_0 - exp_0)
                elo[name_1] += k_factor * (score_1 - exp_1)

        return elo


class PerformanceTracker:
    """Tracks agent performance over time.

    Useful for monitoring training progress and detecting regressions.
    """

    def __init__(self):
        """Initialize tracker."""
        self._history: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        self._step = 0

    def record(
        self,
        agent_name: str,
        metric: str,
        value: float,
        step: Optional[int] = None,
    ) -> None:
        """Record a metric value.

        Args:
            agent_name: Name of the agent
            metric: Metric name (e.g., "win_rate", "avg_reward")
            value: Metric value
            step: Optional step number (uses internal counter if None)
        """
        if step is None:
            step = self._step
            self._step += 1

        key = f"{agent_name}/{metric}"
        self._history[key].append((step, value))

    def get_history(
        self,
        agent_name: str,
        metric: str,
    ) -> List[Tuple[int, float]]:
        """Get history for a metric.

        Args:
            agent_name: Agent name
            metric: Metric name

        Returns:
            List of (step, value) tuples
        """
        key = f"{agent_name}/{metric}"
        return list(self._history[key])

    def get_latest(
        self,
        agent_name: str,
        metric: str,
    ) -> Optional[float]:
        """Get most recent value for a metric.

        Args:
            agent_name: Agent name
            metric: Metric name

        Returns:
            Latest value, or None if no history
        """
        history = self.get_history(agent_name, metric)
        return history[-1][1] if history else None

    def get_moving_average(
        self,
        agent_name: str,
        metric: str,
        window: int = 10,
    ) -> Optional[float]:
        """Compute moving average of recent values.

        Args:
            agent_name: Agent name
            metric: Metric name
            window: Number of recent values to average

        Returns:
            Moving average, or None if insufficient history
        """
        history = self.get_history(agent_name, metric)
        if len(history) < window:
            return None

        recent = [v for _, v in history[-window:]]
        return np.mean(recent)

    def summary(self, agent_name: str) -> Dict[str, Any]:
        """Get summary of all metrics for an agent.

        Args:
            agent_name: Agent name

        Returns:
            Dict of metric summaries
        """
        summary = {}
        prefix = f"{agent_name}/"

        for key, values in self._history.items():
            if key.startswith(prefix):
                metric = key[len(prefix):]
                vals = [v for _, v in values]
                summary[metric] = {
                    "latest": vals[-1] if vals else None,
                    "mean": np.mean(vals) if vals else None,
                    "std": np.std(vals) if vals else None,
                    "min": np.min(vals) if vals else None,
                    "max": np.max(vals) if vals else None,
                    "count": len(vals),
                }

        return summary


def binomial_test(
    wins_a: int,
    wins_b: int,
    draws: int = 0,
) -> float:
    """Test if agent A is significantly better than agent B.

    Uses binomial test on wins (excluding draws).

    Args:
        wins_a: Number of wins for agent A
        wins_b: Number of wins for agent B
        draws: Number of draws (excluded from test)

    Returns:
        p-value for null hypothesis that agents are equal
    """
    from scipy import stats

    total = wins_a + wins_b
    if total == 0:
        return 1.0

    # Two-sided binomial test
    result = stats.binomtest(wins_a, total, p=0.5, alternative='two-sided')
    return result.pvalue


def is_significantly_better(
    result: EvaluationResult,
    side: int = 0,
    alpha: float = 0.05,
) -> bool:
    """Check if side is significantly better.

    Args:
        result: Evaluation result
        side: Side to check (0 or 1)
        alpha: Significance level

    Returns:
        True if side has significantly higher win rate
    """
    other = 1 - side
    p_value = binomial_test(result.wins[side], result.wins[other], result.draws)

    # One-sided: check if this side wins more
    return p_value / 2 < alpha and result.wins[side] > result.wins[other]
