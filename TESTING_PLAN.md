# Pokemon Battle Simulator - Comprehensive Testing Plan

## Overview

This document outlines a testing strategy for the Pokemon battle simulator, covering:
1. Automated testing with random/AI agents
2. Interactive testing with human players
3. Integration and regression testing
4. Performance benchmarking

---

## 1. Automated Agent Testing

### 1.1 Agent vs Agent Battle Tests

**Purpose**: Verify battles complete correctly with various agent combinations.

```python
# tests/test_agent_battles.py

class TestAgentBattles:
    """Automated battles between different agent types."""

    @pytest.mark.parametrize("agent1_type,agent2_type", [
        ("random", "random"),
        ("random", "heuristic"),
        ("heuristic", "heuristic"),
        ("heuristic", "defensive"),
        ("defensive", "type"),
        ("random", "defensive"),
    ])
    def test_battle_completes(self, agent1_type, agent2_type):
        """Test that battles between agents complete without hanging."""

    @pytest.mark.parametrize("format", ["singles", "doubles"])
    def test_battle_formats(self, format):
        """Test both singles and doubles formats."""

    @pytest.mark.parametrize("seed", [42, 123, 456, 789, 1000])
    def test_deterministic_replay(self, seed):
        """Test that battles are deterministic with same seed."""
```

### 1.2 Mass Battle Simulation

**Purpose**: Run many battles to find edge cases and verify statistical properties.

```python
# tests/test_mass_battles.py

class TestMassBattles:
    """Run large numbers of battles for statistical testing."""

    def test_1000_random_battles(self):
        """Run 1000 random vs random battles."""
        wins = {0: 0, 1: 0}
        for seed in range(1000):
            winner = run_battle(RandomAgent(), RandomAgent(), seed=seed)
            wins[winner] += 1
        # Should be roughly 50/50
        assert 400 < wins[0] < 600

    def test_heuristic_beats_random(self):
        """Heuristic agent should beat random agent >60% of the time."""
        wins = run_many_battles(HeuristicAgent(), RandomAgent(), n=100)
        assert wins[0] > 60  # Heuristic should win majority

    def test_no_infinite_loops(self):
        """Verify no battles hang (timeout after 100 turns)."""
        for seed in range(100):
            battle = run_battle_with_timeout(seed, max_turns=100)
            assert battle.ended or battle.turn >= 100
```

### 1.3 Edge Case Testing

**Purpose**: Test specific battle scenarios that might cause issues.

```python
# tests/test_edge_cases.py

class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_all_pokemon_fainted_one_side(self):
        """Battle ends correctly when one side loses all Pokemon."""

    def test_simultaneous_faints(self):
        """Handle both active Pokemon fainting same turn."""

    def test_last_pokemon_vs_last_pokemon(self):
        """1v1 scenario with last Pokemon each."""

    def test_no_pp_left(self):
        """Pokemon with no PP can still act (Struggle)."""

    def test_all_moves_fail(self):
        """Handle scenario where all moves fail (immune, miss, etc.)."""

    def test_switch_only_one_pokemon_left(self):
        """Can't switch when only one Pokemon remains."""
```

---

## 2. Human Player Testing

### 2.1 Interactive CLI Test Script

**Purpose**: Guided manual testing with specific scenarios.

```python
# scripts/test_interactive.py

def run_interactive_test(scenario: str):
    """Run an interactive test scenario."""
    scenarios = {
        "basic": BasicBattleScenario(),
        "forced_switch": ForcedSwitchScenario(),
        "win_condition": WinConditionScenario(),
        "all_moves": AllMovesScenario(),
    }
    scenario = scenarios[scenario]
    scenario.setup()
    scenario.run_interactive()
    scenario.verify()
```

### 2.2 Test Scenarios for Manual Testing

| Scenario | Description | Expected Behavior |
|----------|-------------|-------------------|
| Basic Battle | Play 5 turns, use moves | Damage applied, HP decreases |
| Forced Switch | KO opponent, force switch | Opponent sends replacement |
| Win Game | KO all opponent Pokemon | Victory screen displayed |
| All Switches | Switch all Pokemon | Switches work correctly |
| Status Moves | Apply burn/paralysis | Status shown, effects applied |

### 2.3 CLI Validation Checklist

```
[ ] Game starts without errors
[ ] Teams are generated with valid Pokemon
[ ] All moves have valid PP
[ ] Moves deal damage correctly
[ ] Status conditions display properly
[ ] HP bars update after actions
[ ] Forced switches prompt correctly
[ ] Battle ends with winner message
[ ] Can quit with 'q' at any time
[ ] Invalid input handled gracefully
```

---

## 3. Integration Testing

### 3.1 Full System Integration

**Purpose**: Test all components working together.

```python
# tests/test_full_integration.py

class TestFullIntegration:
    """End-to-end integration tests."""

    def test_cli_to_engine_integration(self):
        """CLI correctly interfaces with battle engine."""

    def test_agent_to_env_integration(self):
        """Agents work correctly in BattleEnv."""

    def test_replay_buffer_with_battles(self):
        """Replay buffer stores and retrieves transitions."""

    def test_evaluation_with_real_battles(self):
        """Evaluator correctly runs and scores battles."""
```

### 3.2 Data Pipeline Testing

```python
# tests/test_data_pipeline.py

class TestDataPipeline:
    """Test data loading and usage in battles."""

    def test_all_moves_usable(self):
        """All moves in registry can be used in battle."""

    def test_all_species_usable(self):
        """All species can be used in teams."""

    def test_type_effectiveness_applied(self):
        """Type chart correctly affects damage."""
```

---

## 4. Performance Testing

### 4.1 Battle Speed Benchmarks

```python
# tests/test_performance.py

class TestPerformance:
    """Performance benchmarks."""

    def test_battles_per_second(self):
        """Measure battle throughput."""
        start = time.time()
        for _ in range(100):
            run_quick_battle()
        elapsed = time.time() - start
        bps = 100 / elapsed
        assert bps > 50, f"Too slow: {bps:.1f} battles/sec"

    def test_memory_usage(self):
        """Memory doesn't grow unbounded."""

    def test_parallel_battles(self):
        """Can run multiple battles in parallel."""
```

---

## 5. Regression Testing

### 5.1 Known Bug Regression Tests

```python
# tests/test_regressions.py

class TestRegressions:
    """Regression tests for fixed bugs."""

    def test_no_infinite_loop_no_targets(self):
        """Bug: Game hung when no valid targets for moves."""
        # Fixed: handle_forced_switches now handles this

    def test_damage_applied_with_move_registry(self):
        """Bug: Damage wasn't applied (empty move registry)."""
        # Fixed: BattleEngine now receives MOVE_REGISTRY

    def test_combat_stats_set_on_team_gen(self):
        """Bug: ATK/DEF/etc not set, damage was 0."""
        # Fixed: _generate_random_team sets all stats
```

---

## 6. Implementation Priority

### Phase 1: Core Automated Tests (High Priority)

1. **Agent Battle Tests** - Verify all agent combinations work
2. **Mass Battle Simulation** - Find edge cases via volume
3. **Regression Tests** - Prevent old bugs from returning

### Phase 2: Integration Tests (Medium Priority)

4. **Full System Integration** - End-to-end flows
5. **Data Pipeline Tests** - All game data works correctly

### Phase 3: Human Testing (Medium Priority)

6. **Interactive Test Script** - Guided manual testing
7. **CLI Validation** - Verify user experience

### Phase 4: Performance (Lower Priority)

8. **Benchmarks** - Speed and memory tests
9. **Stress Tests** - Many concurrent battles

---

## 7. Test Commands

```bash
# Run all tests
pytest -q

# Run specific test categories
pytest tests/test_agent_battles.py -v
pytest tests/test_mass_battles.py -v
pytest tests/test_edge_cases.py -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run performance tests
pytest tests/test_performance.py -v --benchmark

# Run interactive test
python scripts/test_interactive.py --scenario basic
```

---

## 8. Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -e . && pip install pytest
      - name: Run tests
        run: pytest -q
      - name: Run mass battles
        run: pytest tests/test_mass_battles.py -v
```

---

## 9. Test Data Requirements

### Sample Teams for Testing

```python
# tests/fixtures/test_teams.py

BALANCED_TEAM = [
    {"species": "Charizard", "moves": ["Flamethrower", "Air Slash", "Dragon Pulse", "Roost"]},
    {"species": "Blastoise", "moves": ["Surf", "Ice Beam", "Flash Cannon", "Protect"]},
    # ... 4 more Pokemon
]

OFFENSIVE_TEAM = [...]  # High attack, glass cannon
DEFENSIVE_TEAM = [...]  # Walls and tanks
GIMMICK_TEAM = [...]    # Weather/terrain focused
```

---

## 10. Success Criteria

| Metric | Target |
|--------|--------|
| All existing tests pass | 1593/1593 |
| Agent battle tests | 100% pass |
| Mass battles (1000) | 0 hangs/crashes |
| Battle speed | >50 battles/sec |
| Heuristic vs Random win rate | >55% |
| Memory leak check | No growth over 1000 battles |
