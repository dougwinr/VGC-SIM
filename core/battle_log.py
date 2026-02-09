"""Battle logging and replay system for Pokemon battle simulator.

This module provides:
- BattleLog: Structured battle log with event storage
- Serialization: Save/load battle logs as JSON
- Replay: Reconstruct battle from CHOICE events
"""
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Iterator
from pathlib import Path

from .events import (
    EventType,
    BattleEvent,
    create_choice_event,
    create_switch_event,
    create_move_event,
    create_damage_event,
    create_faint_event,
    create_win_event,
)
from .battle import BattleEngine, Choice, ActionType


@dataclass
class BattleLogMetadata:
    """Metadata about a battle log."""
    format: str = ""
    gen: int = 9
    gametype: str = "doubles"
    seed: int = 0
    players: Dict[str, str] = field(default_factory=dict)
    teams: Dict[str, List[Dict]] = field(default_factory=dict)
    winner: Optional[str] = None
    winner_side: int = -1
    total_turns: int = 0


@dataclass
class BattleLog:
    """Complete log of a Pokemon battle.

    Stores all events that occurred during a battle, supporting:
    - Event storage and retrieval
    - Serialization to/from JSON
    - Replay from CHOICE events
    - Event filtering by type, turn, side
    """
    metadata: BattleLogMetadata = field(default_factory=BattleLogMetadata)
    events: List[BattleEvent] = field(default_factory=list)
    _event_counter: int = 0

    def add_event(self, event: BattleEvent) -> None:
        """Add an event to the log."""
        event.timestamp = self._event_counter
        self._event_counter += 1
        self.events.append(event)

    def add_choice(
        self,
        turn: int,
        side: int,
        slot: int,
        choice: Choice,
    ) -> None:
        """Add a player choice event."""
        event = create_choice_event(
            turn=turn,
            side=side,
            slot=slot,
            choice_type=choice.choice_type,
            move_slot=choice.move_slot,
            target=choice.target,
            switch_to=choice.switch_to,
        )
        self.add_event(event)

    def get_events(
        self,
        event_type: Optional[EventType] = None,
        turn: Optional[int] = None,
        side: Optional[int] = None,
    ) -> List[BattleEvent]:
        """Get events matching the given criteria."""
        result = self.events

        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]

        if turn is not None:
            result = [e for e in result if e.turn == turn]

        if side is not None:
            result = [e for e in result if e.side == side]

        return result

    def get_choice_events(self) -> List[BattleEvent]:
        """Get all CHOICE events for replay."""
        choice_types = {
            EventType.CHOICE_MOVE,
            EventType.CHOICE_SWITCH,
            EventType.CHOICE_PASS,
        }
        return [e for e in self.events if e.event_type in choice_types]

    def get_choices_for_turn(self, turn: int) -> Dict[int, List[Choice]]:
        """Get player choices for a specific turn.

        Returns:
            Dict mapping side index to list of Choices
        """
        choices: Dict[int, List[Choice]] = {0: [], 1: []}

        for event in self.events:
            if event.turn != turn:
                continue

            if event.event_type == EventType.CHOICE_MOVE:
                choices[event.side].append(Choice(
                    choice_type='move',
                    slot=event.slot,
                    move_slot=event.data.get("move_slot", 0),
                    target=event.data.get("target", 0),
                ))
            elif event.event_type == EventType.CHOICE_SWITCH:
                choices[event.side].append(Choice(
                    choice_type='switch',
                    slot=event.slot,
                    switch_to=event.data.get("switch_to", 0),
                ))
            elif event.event_type == EventType.CHOICE_PASS:
                choices[event.side].append(Choice(
                    choice_type='pass',
                    slot=event.slot,
                ))

        return choices

    def iter_turns(self) -> Iterator[Tuple[int, List[BattleEvent]]]:
        """Iterate over events grouped by turn."""
        if not self.events:
            return

        current_turn = -1
        current_events: List[BattleEvent] = []

        for event in self.events:
            if event.turn != current_turn:
                if current_events:
                    yield current_turn, current_events
                current_turn = event.turn
                current_events = []
            current_events.append(event)

        if current_events:
            yield current_turn, current_events

    def to_dict(self) -> Dict[str, Any]:
        """Convert battle log to dictionary for serialization."""
        return {
            "metadata": {
                "format": self.metadata.format,
                "gen": self.metadata.gen,
                "gametype": self.metadata.gametype,
                "seed": self.metadata.seed,
                "players": self.metadata.players,
                "teams": self.metadata.teams,
                "winner": self.metadata.winner,
                "winner_side": self.metadata.winner_side,
                "total_turns": self.metadata.total_turns,
            },
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BattleLog":
        """Create battle log from dictionary."""
        meta_dict = d.get("metadata", {})
        metadata = BattleLogMetadata(
            format=meta_dict.get("format", ""),
            gen=meta_dict.get("gen", 9),
            gametype=meta_dict.get("gametype", "doubles"),
            seed=meta_dict.get("seed", 0),
            players=meta_dict.get("players", {}),
            teams=meta_dict.get("teams", {}),
            winner=meta_dict.get("winner"),
            winner_side=meta_dict.get("winner_side", -1),
            total_turns=meta_dict.get("total_turns", 0),
        )

        events = [
            BattleEvent.from_dict(e)
            for e in d.get("events", [])
        ]

        log = cls(metadata=metadata, events=events)
        log._event_counter = len(events)
        return log

    def to_json(self, indent: int = 2) -> str:
        """Serialize battle log to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "BattleLog":
        """Deserialize battle log from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: str) -> None:
        """Save battle log to file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "BattleLog":
        """Load battle log from file."""
        with open(path, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())

    def __len__(self) -> int:
        """Number of events in the log."""
        return len(self.events)


# =============================================================================
# Battle Recording
# =============================================================================

class BattleRecorder:
    """Records battle events from a BattleEngine.

    Usage:
        recorder = BattleRecorder(engine)
        recorder.start()

        # Play battle...
        while not engine.ended:
            choices = get_choices()
            recorder.record_turn(choices)
            engine.step(choices)

        log = recorder.finish()
    """

    def __init__(self, engine: BattleEngine, metadata: Optional[BattleLogMetadata] = None):
        """Initialize recorder.

        Args:
            engine: BattleEngine to record
            metadata: Optional metadata about the battle
        """
        self.engine = engine
        self.log = BattleLog()

        if metadata:
            self.log.metadata = metadata
        else:
            self.log.metadata.seed = engine.state.prng.get_initial_seed()
            self.log.metadata.gametype = "doubles"
            self.log.metadata.gen = 9

    def start(self) -> None:
        """Record battle start."""
        self.log.add_event(BattleEvent(
            event_type=EventType.BATTLE_START,
            turn=0,
        ))

        # Record initial switches
        for side in range(2):
            for slot in range(self.engine.state.active_slots):
                team_slot = self.engine.state.active[side, slot]
                if team_slot >= 0:
                    pokemon = self.engine.state.get_pokemon(side, team_slot)
                    if not pokemon.is_fainted:
                        hp_percent = int(pokemon.hp_fraction * 100)
                        self.log.add_event(create_switch_event(
                            turn=0,
                            side=side,
                            slot=slot,
                            species=str(pokemon.data[0]),  # Species ID
                            hp_percent=hp_percent,
                        ))

    def record_turn(self, choices: Dict[int, List[Choice]]) -> None:
        """Record choices for a turn."""
        turn = self.engine.turn

        for side, side_choices in choices.items():
            for choice in side_choices:
                self.log.add_choice(turn, side, choice.slot, choice)

    def record_event(self, event: BattleEvent) -> None:
        """Record a custom event."""
        self.log.add_event(event)

    def finish(self) -> BattleLog:
        """Finish recording and return the log."""
        self.log.metadata.total_turns = self.engine.turn
        self.log.metadata.winner_side = self.engine.winner if self.engine.winner is not None else -1

        if self.engine.winner is not None:
            self.log.add_event(create_win_event(
                turn=self.engine.turn,
                winner_side=self.engine.winner,
            ))

        return self.log


# =============================================================================
# Battle Replay
# =============================================================================

def replay_from_choices(
    initial_state: "BattleState",
    battle_log: BattleLog,
    move_registry: Dict[int, Any],
) -> "BattleState":
    """Replay a battle from recorded choices.

    Args:
        initial_state: Initial battle state (will be copied)
        battle_log: Battle log containing CHOICE events
        move_registry: Move data registry

    Returns:
        Final battle state after replay
    """
    from .battle_state import BattleState

    # Clone the initial state
    state = initial_state.copy()

    # Create engine with same seed
    engine = BattleEngine(state, move_registry)

    # Get turn range from log
    choice_events = battle_log.get_choice_events()
    if not choice_events:
        return engine.state

    min_turn = min(e.turn for e in choice_events)
    max_turn = max(e.turn for e in choice_events)

    # Replay each turn (start from min_turn which may be 0)
    for turn in range(min_turn, max_turn + 1):
        if engine.ended:
            break

        choices = battle_log.get_choices_for_turn(turn)

        # Skip if no choices for this turn
        if not choices[0] and not choices[1]:
            continue

        engine.step(choices)

    return engine.state


def compare_states(state1: "BattleState", state2: "BattleState") -> Dict[str, Any]:
    """Compare two battle states and return differences.

    Args:
        state1: First battle state
        state2: Second battle state

    Returns:
        Dict with comparison results
    """
    import numpy as np

    differences = {
        "match": True,
        "pokemon_hp": [],
        "field": [],
        "side_conditions": [],
    }

    # Compare Pokemon HP
    for side in range(2):
        for slot in range(state1.team_size):
            hp1 = state1.pokemons[side, slot, 14]  # P_CURRENT_HP
            hp2 = state2.pokemons[side, slot, 14]
            if hp1 != hp2:
                differences["match"] = False
                differences["pokemon_hp"].append({
                    "side": side,
                    "slot": slot,
                    "hp1": int(hp1),
                    "hp2": int(hp2),
                })

    # Compare field state
    if not np.array_equal(state1.field, state2.field):
        differences["match"] = False
        for i in range(len(state1.field)):
            if state1.field[i] != state2.field[i]:
                differences["field"].append({
                    "index": i,
                    "val1": int(state1.field[i]),
                    "val2": int(state2.field[i]),
                })

    # Compare side conditions
    if not np.array_equal(state1.side_conditions, state2.side_conditions):
        differences["match"] = False
        for side in range(2):
            for i in range(state1.side_conditions.shape[1]):
                v1 = state1.side_conditions[side, i]
                v2 = state2.side_conditions[side, i]
                if v1 != v2:
                    differences["side_conditions"].append({
                        "side": side,
                        "index": i,
                        "val1": int(v1),
                        "val2": int(v2),
                    })

    return differences


def verify_replay_determinism(
    state: "BattleState",
    battle_log: BattleLog,
    move_registry: Dict[int, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """Verify that replaying a battle produces the same result.

    Args:
        state: Original final battle state
        battle_log: Battle log with choices
        move_registry: Move data registry

    Returns:
        Tuple of (is_deterministic, differences_dict)
    """
    from .battle_state import BattleState

    # Create fresh state with same seed
    replay_state = BattleState(seed=battle_log.metadata.seed)

    # Copy initial Pokemon data
    replay_state.pokemons[:] = state.pokemons.copy()
    replay_state.active[:] = state.active.copy()

    # Replay the battle
    final_state = replay_from_choices(replay_state, battle_log, move_registry)

    # Compare states
    differences = compare_states(state, final_state)

    return differences["match"], differences
