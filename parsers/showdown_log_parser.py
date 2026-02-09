"""Parser for Pokemon Showdown battle log format.

Parses the pipe-delimited battle log format used in Pokemon Showdown replays.
This can be used to extract battle data for verification testing.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum


class LogEventType(Enum):
    """Types of events in a Pokemon Showdown battle log."""
    # Setup events
    PLAYER = "player"
    TEAM_SIZE = "teamsize"
    GAMETYPE = "gametype"
    GEN = "gen"
    TIER = "tier"
    RULE = "rule"
    POKE = "poke"
    TEAM_PREVIEW = "teampreview"
    START = "start"

    # Turn events
    TURN = "turn"
    UPKEEP = "upkeep"

    # Action events
    SWITCH = "switch"
    MOVE = "move"

    # Effect events
    DAMAGE = "-damage"
    HEAL = "-heal"
    STATUS = "-status"
    CURE_STATUS = "-curestatus"
    BOOST = "-boost"
    UNBOOST = "-unboost"
    WEATHER = "-weather"
    FIELD_START = "-fieldstart"
    FIELD_END = "-fieldend"
    SIDE_START = "-sidestart"
    SIDE_END = "-sideend"
    START_EFFECT = "-start"
    END_EFFECT = "-end"
    ABILITY = "-ability"
    ITEM = "-item"
    END_ITEM = "-enditem"
    TERASTALLIZE = "-terastallize"
    ACTIVATE = "-activate"
    SINGLE_TURN = "-singleturn"

    # Result events
    FAINT = "faint"
    WIN = "win"
    TIE = "tie"

    # Other
    UNKNOWN = "unknown"


@dataclass
class BattleLogEvent:
    """A single event from a Pokemon Showdown battle log."""
    event_type: LogEventType
    raw_line: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PokemonState:
    """State of a Pokemon at a point in the battle."""
    slot: str  # e.g., "p1a", "p2b"
    species: str
    nickname: str
    level: int = 50
    hp_current: int = 100
    hp_max: int = 100
    hp_percent: int = 100
    status: Optional[str] = None
    fainted: bool = False


@dataclass
class TurnState:
    """State of the battle at a given turn."""
    turn_number: int
    pokemon_states: Dict[str, PokemonState] = field(default_factory=dict)
    weather: Optional[str] = None
    terrain: Optional[str] = None
    events: List[BattleLogEvent] = field(default_factory=list)


@dataclass
class ParsedBattleLog:
    """Complete parsed battle log."""
    format: str = ""
    gen: int = 9
    gametype: str = "doubles"
    players: Dict[str, str] = field(default_factory=dict)
    teams: Dict[str, List[Dict]] = field(default_factory=dict)
    turns: List[TurnState] = field(default_factory=list)
    winner: Optional[str] = None
    all_events: List[BattleLogEvent] = field(default_factory=list)


def parse_slot(slot_str: str) -> Tuple[str, str]:
    """Parse a slot string like 'p1a: Ursaluna' into (slot, nickname)."""
    match = re.match(r'(p[12][ab])(?:\s*:\s*(.+))?', slot_str)
    if match:
        return match.group(1), match.group(2) or ""
    return slot_str, ""


def parse_hp(hp_str: str) -> Tuple[int, int, Optional[str]]:
    """Parse HP string like '89/100 tox' into (current, max, status).

    Also handles HTML-escaped slashes (\\/) common in replay exports.
    """
    # Handle fainted
    if hp_str == "0 fnt":
        return 0, 100, None

    # Normalize escaped slashes from HTML (\\/ -> /)
    hp_str = hp_str.replace("\\/", "/")

    # Parse HP/Max format with optional status
    match = re.match(r'(\d+)/(\d+)(?:\s+(\w+))?', hp_str)
    if match:
        current = int(match.group(1))
        max_hp = int(match.group(2))
        status = match.group(3)
        return current, max_hp, status

    # Fallback for percentage-only format
    try:
        return int(hp_str), 100, None
    except ValueError:
        return 100, 100, None


def parse_species_info(species_str: str) -> Dict[str, Any]:
    """Parse species string like 'Ursaluna-Bloodmoon, L50, M' into dict."""
    result = {"species": "", "level": 50, "gender": None}

    parts = [p.strip() for p in species_str.split(",")]
    if parts:
        result["species"] = parts[0]

    for part in parts[1:]:
        if part.startswith("L"):
            try:
                result["level"] = int(part[1:])
            except ValueError:
                pass
        elif part in ("M", "F"):
            result["gender"] = part

    return result


def parse_event_line(line: str) -> Optional[BattleLogEvent]:
    """Parse a single line from the battle log."""
    if not line or not line.startswith("|"):
        return None

    parts = line[1:].split("|")
    if not parts:
        return None

    event_name = parts[0]
    data = {}

    # Map event name to type
    try:
        event_type = LogEventType(event_name)
    except ValueError:
        # Try with dash prefix for effect events
        try:
            event_type = LogEventType("-" + event_name)
        except ValueError:
            event_type = LogEventType.UNKNOWN

    # Parse event-specific data
    if event_type == LogEventType.PLAYER:
        if len(parts) >= 3:
            data["side"] = parts[1]
            data["name"] = parts[2]
            if len(parts) >= 4:
                data["avatar"] = parts[3]

    elif event_type == LogEventType.POKE:
        if len(parts) >= 3:
            data["side"] = parts[1]
            species_info = parse_species_info(parts[2])
            data.update(species_info)

    elif event_type == LogEventType.SWITCH:
        if len(parts) >= 4:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname
            species_info = parse_species_info(parts[2])
            data.update(species_info)
            hp_current, hp_max, status = parse_hp(parts[3])
            data["hp_current"] = hp_current
            data["hp_max"] = hp_max
            data["status"] = status

    elif event_type == LogEventType.MOVE:
        if len(parts) >= 3:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname
            data["move"] = parts[2]
            if len(parts) >= 4:
                target_slot, target_name = parse_slot(parts[3])
                data["target_slot"] = target_slot
                data["target_name"] = target_name
            # Check for [spread] marker
            for part in parts[4:]:
                if part.startswith("[spread]"):
                    data["spread"] = True

    elif event_type == LogEventType.DAMAGE:
        if len(parts) >= 3:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname
            hp_current, hp_max, status = parse_hp(parts[2])
            data["hp_current"] = hp_current
            data["hp_max"] = hp_max
            data["status"] = status
            # Parse source
            for part in parts[3:]:
                if part.startswith("[from]"):
                    data["source"] = part[7:].strip()
                elif part.startswith("[of]"):
                    data["source_of"] = part[5:].strip()

    elif event_type == LogEventType.HEAL:
        if len(parts) >= 3:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname
            hp_current, hp_max, status = parse_hp(parts[2])
            data["hp_current"] = hp_current
            data["hp_max"] = hp_max
            data["status"] = status
            for part in parts[3:]:
                if part.startswith("[from]"):
                    data["source"] = part[7:].strip()

    elif event_type == LogEventType.BOOST or event_type == LogEventType.UNBOOST:
        if len(parts) >= 4:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname
            data["stat"] = parts[2]
            try:
                data["stages"] = int(parts[3])
            except ValueError:
                data["stages"] = 1

    elif event_type == LogEventType.STATUS:
        if len(parts) >= 3:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname
            data["status"] = parts[2]

    elif event_type == LogEventType.WEATHER:
        if len(parts) >= 2:
            data["weather"] = parts[1]
            for part in parts[2:]:
                if part.startswith("[from]"):
                    data["source"] = part[7:].strip()
                elif part == "[upkeep]":
                    data["upkeep"] = True

    elif event_type == LogEventType.TERASTALLIZE:
        if len(parts) >= 3:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname
            data["tera_type"] = parts[2]

    elif event_type == LogEventType.FAINT:
        if len(parts) >= 2:
            slot, nickname = parse_slot(parts[1])
            data["slot"] = slot
            data["nickname"] = nickname

    elif event_type == LogEventType.WIN:
        if len(parts) >= 2:
            data["winner"] = parts[1]

    elif event_type == LogEventType.TURN:
        if len(parts) >= 2:
            try:
                data["turn"] = int(parts[1])
            except ValueError:
                data["turn"] = 0

    elif event_type == LogEventType.GAMETYPE:
        if len(parts) >= 2:
            data["gametype"] = parts[1]

    elif event_type == LogEventType.GEN:
        if len(parts) >= 2:
            try:
                data["gen"] = int(parts[1])
            except ValueError:
                data["gen"] = 9

    elif event_type == LogEventType.TIER:
        if len(parts) >= 2:
            data["tier"] = parts[1]

    return BattleLogEvent(event_type=event_type, raw_line=line, data=data)


def extract_log_data(html_content: str) -> str:
    """Extract battle log data from HTML replay file."""
    # Find the script tag with battle log data
    match = re.search(
        r'<script[^>]*class="battle-log-data"[^>]*>(.*?)</script>',
        html_content,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()

    # If no HTML wrapper, assume raw log
    return html_content


def parse_battle_log(log_content: str) -> ParsedBattleLog:
    """Parse a complete Pokemon Showdown battle log.

    Args:
        log_content: Raw battle log content (pipe-delimited format)

    Returns:
        ParsedBattleLog with all extracted data
    """
    result = ParsedBattleLog()
    current_turn = TurnState(turn_number=0)
    pokemon_states: Dict[str, PokemonState] = {}

    for line in log_content.strip().split("\n"):
        event = parse_event_line(line)
        if not event:
            continue

        result.all_events.append(event)

        # Handle setup events
        if event.event_type == LogEventType.PLAYER:
            side = event.data.get("side", "")
            name = event.data.get("name", "")
            if side and name:
                result.players[side] = name

        elif event.event_type == LogEventType.GAMETYPE:
            result.gametype = event.data.get("gametype", "doubles")

        elif event.event_type == LogEventType.GEN:
            result.gen = event.data.get("gen", 9)

        elif event.event_type == LogEventType.TIER:
            result.format = event.data.get("tier", "")

        elif event.event_type == LogEventType.POKE:
            side = event.data.get("side", "")
            if side not in result.teams:
                result.teams[side] = []
            result.teams[side].append({
                "species": event.data.get("species", ""),
                "level": event.data.get("level", 50),
                "gender": event.data.get("gender"),
            })

        # Handle turn markers
        elif event.event_type == LogEventType.TURN:
            # Save current turn
            current_turn.pokemon_states = dict(pokemon_states)
            result.turns.append(current_turn)

            # Start new turn
            turn_num = event.data.get("turn", 0)
            current_turn = TurnState(turn_number=turn_num)

        # Handle state-changing events
        elif event.event_type == LogEventType.SWITCH:
            slot = event.data.get("slot", "")
            pokemon_states[slot] = PokemonState(
                slot=slot,
                species=event.data.get("species", ""),
                nickname=event.data.get("nickname", ""),
                level=event.data.get("level", 50),
                hp_current=event.data.get("hp_current", 100),
                hp_max=event.data.get("hp_max", 100),
                hp_percent=event.data.get("hp_current", 100),
                status=event.data.get("status"),
            )
            current_turn.events.append(event)

        elif event.event_type == LogEventType.DAMAGE:
            slot = event.data.get("slot", "")
            if slot in pokemon_states:
                pokemon_states[slot].hp_current = event.data.get("hp_current", 0)
                pokemon_states[slot].hp_percent = event.data.get("hp_current", 0)
                pokemon_states[slot].status = event.data.get("status")
                if event.data.get("hp_current", 100) == 0:
                    pokemon_states[slot].fainted = True
            current_turn.events.append(event)

        elif event.event_type == LogEventType.HEAL:
            slot = event.data.get("slot", "")
            if slot in pokemon_states:
                pokemon_states[slot].hp_current = event.data.get("hp_current", 0)
                pokemon_states[slot].hp_percent = event.data.get("hp_current", 0)
                pokemon_states[slot].status = event.data.get("status")
            current_turn.events.append(event)

        elif event.event_type == LogEventType.FAINT:
            slot = event.data.get("slot", "")
            if slot in pokemon_states:
                pokemon_states[slot].hp_current = 0
                pokemon_states[slot].hp_percent = 0
                pokemon_states[slot].fainted = True
            current_turn.events.append(event)

        elif event.event_type == LogEventType.STATUS:
            slot = event.data.get("slot", "")
            if slot in pokemon_states:
                pokemon_states[slot].status = event.data.get("status")
            current_turn.events.append(event)

        elif event.event_type == LogEventType.WEATHER:
            current_turn.weather = event.data.get("weather")
            current_turn.events.append(event)

        elif event.event_type == LogEventType.WIN:
            result.winner = event.data.get("winner")

        elif event.event_type == LogEventType.MOVE:
            current_turn.events.append(event)

    # Save final turn state
    current_turn.pokemon_states = dict(pokemon_states)
    result.turns.append(current_turn)

    return result


def parse_battle_log_file(filepath: str) -> ParsedBattleLog:
    """Parse a Pokemon Showdown battle log from a file.

    Handles both raw log files and HTML replay files.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract log data if it's an HTML file
    log_data = extract_log_data(content)

    return parse_battle_log(log_data)


def get_damage_events(parsed_log: ParsedBattleLog) -> List[Dict]:
    """Extract all damage events from a parsed log.

    Returns list of dicts with turn, slot, hp_before, hp_after, source.
    """
    damage_events = []
    hp_tracker: Dict[str, int] = {}

    for turn in parsed_log.turns:
        for event in turn.events:
            if event.event_type == LogEventType.SWITCH:
                slot = event.data.get("slot", "")
                hp_tracker[slot] = event.data.get("hp_current", 100)

            elif event.event_type == LogEventType.DAMAGE:
                slot = event.data.get("slot", "")
                hp_before = hp_tracker.get(slot, 100)
                hp_after = event.data.get("hp_current", 0)

                damage_events.append({
                    "turn": turn.turn_number,
                    "slot": slot,
                    "hp_before": hp_before,
                    "hp_after": hp_after,
                    "damage": hp_before - hp_after,
                    "source": event.data.get("source", ""),
                })

                hp_tracker[slot] = hp_after

            elif event.event_type == LogEventType.HEAL:
                slot = event.data.get("slot", "")
                hp_tracker[slot] = event.data.get("hp_current", 0)

    return damage_events


def get_move_events(parsed_log: ParsedBattleLog) -> List[Dict]:
    """Extract all move events from a parsed log."""
    move_events = []

    for turn in parsed_log.turns:
        for event in turn.events:
            if event.event_type == LogEventType.MOVE:
                move_events.append({
                    "turn": turn.turn_number,
                    "user_slot": event.data.get("slot", ""),
                    "user": event.data.get("nickname", ""),
                    "move": event.data.get("move", ""),
                    "target_slot": event.data.get("target_slot", ""),
                    "target": event.data.get("target_name", ""),
                    "spread": event.data.get("spread", False),
                })

    return move_events
