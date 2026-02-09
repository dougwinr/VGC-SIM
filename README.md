# Pokemon Battle Simulator

High-performance, deterministic Pokemon battle simulator optimized for reinforcement learning. Features a complete VGC tournament system with real tournament data integration from Limitless VGC and pokedata.ovh.

## Features

- **Deterministic Battle Engine**: All randomness flows through a single PRNG for perfect replay capability
- **Data-Oriented Design**: NumPy arrays for speed and batchability
- **VGC Tournament System**: Full Swiss pairings, top cut brackets, and scoring
- **Real Tournament Data**: Load teams and standings from Limitless VGC and pokedata.ovh
- **AI Agents**: Random, Heuristic, and extensible agent framework
- **Pokemon Showdown Compatible**: Parse and replay Showdown battle logs

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Battle Engine](#battle-engine)
- [Tournament System](#tournament-system)
- [Loading Tournament Data](#loading-tournament-data)
- [AI Agents](#ai-agents)
- [Running Tests](#running-tests)
- [API Reference](#api-reference)

## Installation

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone or navigate to the project directory
cd pokemon

# Install the package in development mode
pip install -e .

# Install dependencies
pip install pytest numpy requests
```

## Quick Start

### Run a Simple Battle

```python
from core.battle_state import BattleState
from core.battle import BattleEngine
from tournament.runner import create_random_team

# Create two random teams
team1 = create_random_team("team1", seed=42)
team2 = create_random_team("team2", seed=43)

print(f"Team 1: {[p['name'] for p in team1.pokemon]}")
print(f"Team 2: {[p['name'] for p in team2.pokemon]}")
```

### Simulate a Tournament

```python
from tournament import Tournament, Division, Player
from tournament.runner import simulate_tournament, create_random_team, TournamentConfig
from tournament.regulation import VGC_2024

# Create tournament
tournament = Tournament(id="my_tournament", name="My VGC Tournament", best_of=3)
division = Division(id="main", name="Main", total_swiss_rounds=5)
tournament.divisions.append(division)

# Add players with random teams
for i in range(16):
    team = create_random_team(f"team_{i}", seed=i)
    tournament.add_team(team)

    player = Player(id=f"player_{i}", name=f"Player {i+1}", team_id=team.id)
    tournament.players[player.id] = player
    division.add_player(player.id)

# Run tournament
config = TournamentConfig(verbose=True)
result = simulate_tournament(tournament, VGC_2024, config=config, seed=42)

print(f"Tournament complete! Winner determined after {division.total_swiss_rounds} rounds.")
```

### Load Real Tournament Data

```python
from tournament import load_limitless_tournament, get_top_pokemon, get_top_items

# Load tournament from Limitless VGC
tournament = load_limitless_tournament(418, load_teams=True, max_teams=40)

print(f"Tournament: {tournament.name}")
print(f"Players: {tournament.player_count}")

# Analyze team compositions
print("\nTop 10 Pokemon:")
for pokemon, count in get_top_pokemon(tournament, top_n=10):
    print(f"  {pokemon}: {count}")

print("\nTop 10 Items:")
for item, count in get_top_items(tournament, top_n=10):
    print(f"  {item}: {count}")
```

## Project Structure

```
pokemon/
├── core/                    # Battle engine
│   ├── layout.py           # Packed array indices
│   ├── pokemon.py          # Pokemon class & stat calculation
│   ├── battle_state.py     # BattleState with NumPy arrays
│   ├── battle.py           # BattleEngine & turn execution
│   ├── damage.py           # Damage formula
│   ├── events.py           # Event system
│   └── battle_log.py       # Battle logging & replay
│
├── data/                    # Static game data
│   ├── types.py            # 19 Pokemon types
│   ├── natures.py          # 25 natures with stat modifiers
│   ├── moves.py            # Move definitions
│   ├── abilities.py        # Ability registry
│   ├── items.py            # Item registry
│   ├── species.py          # Species data & base stats
│   └── *_loader.py         # Data loaders
│
├── tournament/              # Tournament system
│   ├── model.py            # Tournament, Player, Team, Match, Standing
│   ├── pairings.py         # Swiss pairings algorithm
│   ├── scoring.py          # Scoring profiles & tiebreakers
│   ├── regulation.py       # VGC/Smogon regulations
│   ├── runner.py           # Tournament simulation
│   ├── limitless_loader.py # Limitless VGC data loader
│   └── pokedata_loader.py  # pokedata.ovh data loader
│
├── agents/                  # AI agents
│   ├── base.py             # Agent base class
│   ├── random_agent.py     # Random move selection
│   └── heuristic_agent.py  # Heuristic-based decisions
│
├── parsers/                 # Log parsers
│   ├── showdown_log_parser.py  # Parse Showdown logs
│   └── showdown_protocol.py    # SIM-PROTOCOL.md implementation
│
├── ai/                      # RL environment
│   └── env.py              # Gym-compatible environment
│
├── cli/                     # Command-line interface
│   └── main.py             # CLI entry point
│
└── tests/                   # Test suite (1500+ tests)
```

## Battle Engine

### Core Concepts

**Packed Array Layout**: All Pokemon data is stored in dense NumPy arrays for performance:

```python
from core.layout import (
    P_SPECIES, P_LEVEL, P_CURRENT_HP,
    P_STAT_HP, P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_MOVE1, P_MOVE2, P_MOVE3, P_MOVE4,
)

# Access Pokemon data
species_id = state.pokemons[side, slot, P_SPECIES]
current_hp = state.pokemons[side, slot, P_CURRENT_HP]
```

**BattleState Arrays**:
- `pokemons`: `[num_sides, team_size, P]` - all Pokemon data
- `active`: `[num_sides, active_slots]` - indices of active Pokemon
- `pp`: `[num_sides, team_size, 4]` - PP per move slot
- `side_cond`: `[num_sides, S]` - side conditions (Reflect, Light Screen, etc.)
- `field`: `[F]` - field state (Weather, Terrain, Trick Room)

**Deterministic RNG**: All randomness uses a seeded PRNG:

```python
state = BattleState(seed=42)  # Reproducible battles
```

### Running a Battle

```python
from core.battle_state import BattleState
from core.battle import BattleEngine, Choice

# Create battle state
state = BattleState(
    num_sides=2,
    team_size=6,
    active_slots=2,  # Doubles
    seed=42,
)

# Set up teams...
state.start_battle()

# Create engine
engine = BattleEngine(state)

# Execute turn
choices = {
    0: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
    1: [Choice(choice_type='move', slot=0, move_slot=0, target=-1)],
}
engine.step(choices)

# Check for winner
if engine.ended:
    print(f"Winner: Side {engine.winner}")
```

## Tournament System

### Tournament Models

```python
from tournament import (
    Tournament,      # Main tournament container
    Division,        # Division within tournament (Masters, Seniors, etc.)
    Player,          # Tournament participant
    Team,            # Player's team of Pokemon
    Match,           # Single match between players
    Standing,        # Player's current standing
    MatchResult,     # WIN, LOSS, DRAW, NOT_PLAYED
    TournamentPhase, # REGISTRATION, SWISS, TOP_CUT, FINALS, COMPLETE
)
```

### Swiss Pairings

```python
from tournament.pairings import generate_swiss_pairings
from tournament.scoring import VGC_SCORING, calculate_standings

# Generate pairings for a round
matches = generate_swiss_pairings(
    standings=division.standings,
    past_matches=division.matches,
    round_number=1,
    best_of=3,
)

# After matches complete, update standings
calculate_standings(division.standings, matches, VGC_SCORING)
```

### Team Validation

```python
from tournament import validate_team
from tournament.regulation import VGC_2024, SMOGON_OU

errors = validate_team(team, VGC_2024)
if errors:
    print("Team is invalid:")
    for error in errors:
        print(f"  - {error}")
```

### Pre-defined Regulations

| Regulation | Game Type | Team Size | Level Cap | Item Clause | Species Clause |
|------------|-----------|-----------|-----------|-------------|----------------|
| `VGC_2024` | Doubles | 6 | 50 | Yes | Yes |
| `SMOGON_OU` | Singles | 6 | 100 | No | Yes |
| `OPEN_DOUBLES` | Doubles | 6 | 50 | No | No |

### Scoring Profiles

```python
from tournament.scoring import VGC_SCORING, SWISS_SCORING

# VGC: 3 for win, 0 for loss, 1 for draw
# SWISS: 1 for win, 0 for loss, 0 for draw
```

## Loading Tournament Data

### From Limitless VGC

```python
from tournament import (
    load_limitless_tournament,
    load_limitless_team,
    load_limitless_info,
    get_top_pokemon,
    get_top_items,
    get_pokemon_item_pairs,
)

# Load tournament with full team details
tournament = load_limitless_tournament(
    tournament_id=418,       # Tournament ID from URL
    load_teams=True,         # Fetch detailed team data
    max_teams=40,            # Limit teams to load (None = all)
    team_delay=0.5,          # Delay between requests
)

# Load just tournament info (faster)
info = load_limitless_info(418)
print(f"Name: {info.name}")
print(f"Date: {info.date}")
print(f"Players: {info.player_count}")

# Load a specific team
team = load_limitless_team(5591)
for pokemon in team.pokemon:
    print(f"{pokemon.species} @ {pokemon.item}")
    print(f"  Ability: {pokemon.ability}")
    print(f"  Tera: {pokemon.tera_type}")
    print(f"  Moves: {', '.join(pokemon.moves)}")

# Analytics
print("Most used Pokemon:")
for pokemon, count in get_top_pokemon(tournament, top_n=10):
    print(f"  {pokemon}: {count}")

print("Items commonly used with Incineroar:")
for item, count in get_pokemon_item_pairs(tournament, "Incineroar"):
    print(f"  {item}: {count}")
```

### From pokedata.ovh

Since pokedata.ovh uses JavaScript rendering, you have two options:

```python
from tournament import (
    load_from_pokedata_json,
    load_from_pokedata_html,
)

# Option 1: From exported JSON (recommended)
tournament = load_from_pokedata_json("standings.json")

# Option 2: From saved HTML file
tournament = load_from_pokedata_html("saved_page.html")
```

### Sample JSON Format

```json
{
  "tournament": "Regional Sydney",
  "id": "0000164",
  "division": "masters",
  "standings": [
    {
      "rank": 1,
      "name": "Player Name",
      "record": "8-1-0",
      "country": "US",
      "team": [
        {
          "species": "Flutter Mane",
          "item": "Choice Specs",
          "ability": "Protosynthesis",
          "tera_type": "Fairy"
        }
      ]
    }
  ]
}
```

## AI Agents

### Available Agents

```python
from agents import RandomAgent, HeuristicAgent

# Random agent - picks random legal moves
agent = RandomAgent(seed=42)

# Heuristic agent - uses damage estimation
agent = HeuristicAgent(seed=42)

# Use in battle
action = agent.act(observation, legal_actions, info)
```

### Creating Custom Agents

```python
from agents import Agent, Action, ActionKind

class MyAgent(Agent):
    def act(self, observation, legal_actions, info):
        # Your logic here
        # Return an Action object
        return Action.move(slot=0, move_slot=0, target_side=1, target_slot=0)
```

### Action Types

```python
from agents import Action

# Move action
action = Action.move(slot=0, move_slot=2, target_side=1, target_slot=0)

# Switch action
action = Action.switch(slot=0, switch_to=3)

# Pass action (forced switch pending)
action = Action.pass_action(slot=0)
```

## Running Tests

### Run All Tests

```bash
pytest -q
# Expected: 1500+ passed
```

### Run Tournament Tests

```bash
# All tournament tests
pytest tests/test_tournament.py tests/test_tournament_stress.py -v

# Data loader tests
pytest tests/test_pokedata_loader.py tests/test_limitless_loader.py -v
```

### Run Stress Tests

```bash
# Large tournament simulations (32-256 players)
pytest tests/test_tournament_stress.py -v
```

### Run by Category

```bash
# Core engine
pytest tests/test_battle.py tests/test_damage.py tests/test_battle_state.py -v

# Data layer
pytest tests/test_data_*.py -v

# Showdown compatibility
pytest tests/test_showdown_*.py -v

# Agents
pytest tests/test_agents.py tests/test_agent_battles.py -v
```

### Test Coverage

```bash
pip install pytest-cov
pytest --cov=core --cov=data --cov=tournament --cov=parsers tests/ --cov-report=term-missing
```

## API Reference

### Tournament Module

| Function | Description |
|----------|-------------|
| `load_limitless_tournament(id)` | Load tournament from Limitless VGC |
| `load_limitless_team(id)` | Load single team from Limitless VGC |
| `load_from_pokedata_json(path)` | Load tournament from JSON file |
| `simulate_tournament(tournament, regulation)` | Simulate entire tournament |
| `simulate_match(match, tournament, regulation)` | Simulate single match |
| `generate_swiss_pairings(standings, matches, round)` | Generate pairings |
| `generate_top_cut_bracket(standings, size)` | Generate top cut bracket |
| `calculate_standings(standings, matches, scoring)` | Update standings |
| `validate_team(team, regulation)` | Validate team against rules |
| `get_top_pokemon(tournament, n)` | Get most used Pokemon |
| `get_top_items(tournament, n)` | Get most used items |
| `get_pokemon_item_pairs(tournament, pokemon)` | Get items for specific Pokemon |

### Core Module

| Class | Description |
|-------|-------------|
| `BattleState` | Battle state container with NumPy arrays |
| `BattleEngine` | Turn execution and action resolution |
| `Choice` | Player's choice (move, switch, pass) |
| `BattleLog` | Battle event recording |
| `BattleRecorder` | Automatic battle logging |

### Parser Module

| Class | Description |
|-------|-------------|
| `ProtocolParser` | Parse Showdown protocol messages |
| `ProtocolEmitter` | Emit Showdown protocol output |
| `ChoiceParser` | Parse player choice strings |
| `ProtocolReplayer` | Replay battles from logs |

## Performance

Benchmarks on typical hardware:

| Operation | Performance |
|-----------|-------------|
| Single battle simulation | ~50ms |
| 32-player tournament (5 rounds) | ~2s |
| 256-player tournament (8 rounds) | ~35s |
| Parse 500 player standings | <100ms |
| Analytics on 1000 players | <500ms |

## License

This project is for educational and research purposes. Pokemon is a trademark of Nintendo/Game Freak/The Pokemon Company.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest -q`
4. Submit a pull request

## Acknowledgments

- [Pokemon Showdown](https://pokemonshowdown.com/) for the battle mechanics reference
- [Limitless VGC](https://limitlessvgc.com/) for tournament data
- [pokedata.ovh](https://pokedata.ovh/) for tournament standings
