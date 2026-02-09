# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

High-performance, deterministic Pokémon battle simulator optimized for reinforcement learning. Uses data-oriented design with NumPy arrays for speed and batchability.

## Commands

```bash
# Install dependencies
pip install -e .
pip install pytest numpy

# Run tests
pytest -q

# Convert TypeScript data to JSON (requires Node.js)
node scripts/ts_to_json.mjs
```

## Architecture

### Core Design Principles

- **Integer IDs everywhere**: Species/moves/items/abilities/types resolved once at load time. Core simulation never uses string lookups.
- **Function registry pattern**: Abilities/items/effects use `id -> event -> handler` registries instead of inheritance hierarchies.
- **Deterministic RNG**: All randomness flows through a single PRNG in BattleState. Replay via seed + action sequence produces identical outcomes.
- **Frozen dataclasses**: Static game data (MoveData, SpeciesData, etc.) is immutable, loaded once at startup.

### Project Structure

```
pokemon_sim/
├── data/           # Static data loading and registries
│   ├── raw/        # Upstream TypeScript data sources
│   ├── compiled/   # Converted JSON (from TS)
│   ├── models.py   # Frozen dataclasses: MoveData, SpeciesData, AbilityData, ItemData
│   ├── registry.py # Global registries + ID maps (sorted for determinism)
│   └── loaders.py  # Raw → registries conversion
├── core/           # Battle runtime (no strings, only int IDs)
│   ├── layout.py   # Packed array indices (single source of truth)
│   ├── pokemon.py  # Stat calculation + packing
│   ├── state.py    # BattleState (NumPy arrays + RNG state)
│   ├── damage.py   # Damage formula
│   └── engine.py   # BattleEngine.step(), ordering, effects
├── effects/        # Effect handlers (function registries)
│   ├── abilities.py
│   ├── items.py
│   └── move_effects.py
├── io/             # Parsing (team_format.py for Showdown-style text)
├── ai/             # RL environment wrapper (env.py)
└── tests/          # pytest suite
```

### Packed Pokémon Layout (core/layout.py)

All Pokémon data stored in dense NumPy arrays. Key indices:
- 0-7: Species, Level, Nature, Ability, Item, Type1, Type2, Tera Type
- 8-13: Stats (HP, Atk, Def, SpA, SpD, Spe)
- 14-16: Current HP, Status, Status Counter
- 17-21: Stat stages (Atk, Def, SpA, SpD, Spe)
- 22-25: Move slot IDs
- 26+: Volatile flags (Protect, Encore, Taunt, etc.)

### BattleState Arrays

- `pokemons`: `[num_sides, team_size, P]` - all Pokémon data
- `active`: `[num_sides, active_slots]` - indices of active Pokémon
- `pp`: `[num_sides, team_size, 4]` - PP per move slot
- `side_cond`: `[num_sides, S]` - side conditions (Reflect, Light Screen, etc.)
- `field`: `[F]` - field state (Weather, Terrain, Trick Room, Tailwind)

### Data Flow

```
data/raw/*.ts → (Node script) → data/compiled/*.json → Python loaders → ID registries
```

ID maps are built by sorting canonical keys for deterministic, stable IDs across machines.

## Battle Format

- Doubles (2 active per side), team size 6
- Win condition: all Pokémon on one side fainted

## Test Strategy

Tests use hardcoded Team A vs Team B fixtures that exercise all implemented mechanics:
- `test_data_loading.py` - verify all entities resolve via ID maps
- `test_stats_and_natures.py` - stat calculation with nature multipliers
- `test_damage_core.py` - damage formula invariants
- `test_effects_abilities_items.py` - ability/item interactions
- `test_battle_teamA_vs_teamB.py` - full integration test
- `test_replay_determinism.py` - replay from CHOICE log matches original
- `test_perf_smoke.py` - baseline: >50 battles/sec
