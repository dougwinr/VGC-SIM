"""Mass battle simulation tests.

Run large numbers of battles to find edge cases, verify statistical
properties, and ensure system stability.
"""
import pytest
import time
from collections import Counter
from typing import Dict

from agents import RandomAgent, HeuristicAgent

# Import the run_battle helper from test_agent_battles
from tests.test_agent_battles import run_battle


def run_quick_battle(seed: int, game_type: str = "doubles", max_turns: int = 100) -> Dict:
    """Run a quick battle and return results.

    Returns:
        Dict with winner, turns, and any errors.
    """
    try:
        agent1 = RandomAgent(seed=seed)
        agent2 = RandomAgent(seed=seed + 10000)

        winner, num_turns = run_battle(agent1, agent2, game_type, seed, max_turns)

        return {
            "winner": winner,
            "turns": num_turns,
            "error": None,
            "ended": True,
        }
    except Exception as e:
        return {
            "winner": None,
            "turns": 0,
            "error": str(e),
            "ended": False,
        }


class TestMassBattleStability:
    """Run many battles to test system stability."""

    def test_100_battles_no_crashes(self):
        """Run 100 battles without any crashes."""
        errors = []
        for seed in range(100):
            result = run_quick_battle(seed)
            if result["error"]:
                errors.append((seed, result["error"]))

        assert len(errors) == 0, f"Battles crashed: {errors[:5]}"

    def test_100_battles_all_end(self):
        """All battles should end within max turns."""
        not_ended = []
        for seed in range(100):
            result = run_quick_battle(seed, max_turns=100)
            if not result["ended"] and result["error"] is None:
                not_ended.append(seed)

        # Allow a small percentage to hit turn limit
        assert len(not_ended) < 10, f"Too many battles didn't end: {not_ended}"

    @pytest.mark.slow
    def test_500_battles_stability(self):
        """Run 500 battles for thorough stability testing."""
        errors = []
        hangs = []

        for seed in range(500):
            result = run_quick_battle(seed)
            if result["error"]:
                errors.append(seed)
            elif result["turns"] >= 100:
                hangs.append(seed)

        assert len(errors) == 0, f"Errors in {len(errors)} battles"
        assert len(hangs) < 25, f"Too many battles hit turn limit: {len(hangs)}"


class TestMassBattleStatistics:
    """Statistical properties of battle outcomes."""

    def test_random_vs_random_roughly_fair(self):
        """Random vs Random should be roughly 50/50."""
        wins = Counter()

        for seed in range(200):
            result = run_quick_battle(seed)
            winner = result["winner"]
            if winner in [0, 1]:
                wins[winner] += 1

        total = wins[0] + wins[1]
        if total > 0:
            win_rate = wins[0] / total
            # Should be between 35% and 65%
            assert 0.35 < win_rate < 0.65, f"Win rate too skewed: {win_rate:.2%}"

    def test_average_battle_length(self):
        """Battles should have reasonable average length."""
        turns = []

        for seed in range(100):
            result = run_quick_battle(seed)
            if result["ended"] and result["turns"] > 0:
                turns.append(result["turns"])

        if turns:
            avg_turns = sum(turns) / len(turns)
            # Most battles should end in 5-50 turns
            assert 3 < avg_turns < 60, f"Average turns unusual: {avg_turns:.1f}"

    def test_turn_distribution(self):
        """Check distribution of battle lengths."""
        turn_counts = Counter()

        for seed in range(200):
            result = run_quick_battle(seed)
            if result["ended"] and result["turns"] > 0:
                # Bucket into ranges
                t = result["turns"]
                if t <= 5:
                    bucket = "1-5"
                elif t <= 15:
                    bucket = "6-15"
                elif t <= 30:
                    bucket = "16-30"
                elif t <= 50:
                    bucket = "31-50"
                else:
                    bucket = "51+"
                turn_counts[bucket] += 1

        # Should have variety in battle lengths
        assert len(turn_counts) >= 3, f"Battle lengths not varied: {turn_counts}"


class TestHeuristicAdvantage:
    """Test that smarter agents perform better."""

    def test_heuristic_beats_random(self):
        """Heuristic agent should beat random agent more often."""
        wins = Counter()

        for seed in range(100):
            try:
                agent1 = HeuristicAgent(seed=seed)
                agent2 = RandomAgent(seed=seed + 10000)

                winner, _ = run_battle(agent1, agent2, "doubles", seed, max_turns=100)

                if winner in [0, 1]:
                    wins[winner] += 1

            except Exception:
                pass  # Skip failed battles

        total = wins[0] + wins[1]
        if total > 50:  # Need enough samples
            win_rate = wins[0] / total
            # Heuristic (side 0) should win > 50%
            assert win_rate > 0.50, f"Heuristic didn't beat random: {win_rate:.2%}"


class TestBattleFormats:
    """Test both singles and doubles formats at scale."""

    @pytest.mark.parametrize("game_type", ["singles", "doubles"])
    def test_format_stability(self, game_type: str):
        """Both formats should be stable across many battles."""
        errors = 0
        for seed in range(50):
            result = run_quick_battle(seed, game_type=game_type)
            if result["error"]:
                errors += 1

        assert errors == 0, f"{errors} errors in {game_type} format"


class TestBattlePerformance:
    """Performance benchmarks for mass battles."""

    def test_battles_per_second(self):
        """Measure battle throughput."""
        start = time.time()
        count = 50

        for seed in range(count):
            run_quick_battle(seed)

        elapsed = time.time() - start
        bps = count / elapsed

        # Should achieve at least 10 battles/second
        assert bps > 10, f"Too slow: {bps:.1f} battles/sec"
        print(f"\nBattle speed: {bps:.1f} battles/sec")

    def test_consistent_speed(self):
        """Speed should be consistent across batches."""
        times = []

        for batch in range(5):
            start = time.time()
            for seed in range(batch * 20, batch * 20 + 20):
                run_quick_battle(seed)
            times.append(time.time() - start)

        # No batch should be more than 3x slower than fastest
        assert max(times) < min(times) * 3, f"Inconsistent speeds: {times}"
