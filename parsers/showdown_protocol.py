"""Pokemon Showdown protocol implementation.

This module provides:
- Protocol message parsing (pipe-delimited format)
- Protocol message emission (for compatibility output)
- Choice parsing and formatting
- Battle replay from protocol logs

Based on:
- SIM-PROTOCOL.md: Message format specification
- SIMULATOR.md: Battle stream API
"""
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Iterator
from enum import Enum, auto


# =============================================================================
# Protocol Message Types
# =============================================================================

class MessageType(Enum):
    """All message types defined in SIM-PROTOCOL.md."""
    # Battle initialization
    PLAYER = "player"
    TEAMSIZE = "teamsize"
    GAMETYPE = "gametype"
    GEN = "gen"
    TIER = "tier"
    RATED = "rated"
    RULE = "rule"
    CLEARPOKE = "clearpoke"
    POKE = "poke"
    TEAMPREVIEW = "teampreview"
    START = "start"

    # Battle progress
    EMPTY = ""  # Spacer
    REQUEST = "request"
    INACTIVE = "inactive"
    INACTIVEOFF = "inactiveoff"
    UPKEEP = "upkeep"
    TURN = "turn"
    WIN = "win"
    TIE = "tie"
    TIMESTAMP = "t:"

    # Major actions
    MOVE = "move"
    SWITCH = "switch"
    DRAG = "drag"
    DETAILSCHANGE = "detailschange"
    FORMECHANGE = "-formechange"
    REPLACE = "replace"
    SWAP = "swap"
    CANT = "cant"
    FAINT = "faint"

    # Minor actions (prefixed with -)
    FAIL = "-fail"
    BLOCK = "-block"
    NOTARGET = "-notarget"
    MISS = "-miss"
    DAMAGE = "-damage"
    HEAL = "-heal"
    SETHP = "-sethp"
    STATUS = "-status"
    CURESTATUS = "-curestatus"
    CURETEAM = "-cureteam"
    BOOST = "-boost"
    UNBOOST = "-unboost"
    SETBOOST = "-setboost"
    SWAPBOOST = "-swapboost"
    INVERTBOOST = "-invertboost"
    CLEARBOOST = "-clearboost"
    CLEARALLBOOST = "-clearallboost"
    CLEARPOSITIVEBOOST = "-clearpositiveboost"
    CLEARNEGATIVEBOOST = "-clearnegativeboost"
    COPYBOOST = "-copyboost"
    WEATHER = "-weather"
    FIELDSTART = "-fieldstart"
    FIELDEND = "-fieldend"
    SIDESTART = "-sidestart"
    SIDEEND = "-sideend"
    SWAPSIDECONDITIONS = "-swapsideconditions"
    VOLSTART = "-start"
    VOLEND = "-end"
    CRIT = "-crit"
    SUPEREFFECTIVE = "-supereffective"
    RESISTED = "-resisted"
    IMMUNE = "-immune"
    ITEM = "-item"
    ENDITEM = "-enditem"
    ABILITY = "-ability"
    ENDABILITY = "-endability"
    TRANSFORM = "-transform"
    MEGA = "-mega"
    PRIMAL = "-primal"
    BURST = "-burst"
    ZPOWER = "-zpower"
    ZBROKEN = "-zbroken"
    TERASTALLIZE = "-terastallize"
    ACTIVATE = "-activate"
    HINT = "-hint"
    CENTER = "-center"
    MESSAGE = "-message"
    COMBINE = "-combine"
    WAITING = "-waiting"
    PREPARE = "-prepare"
    MUSTRECHARGE = "-mustrecharge"
    NOTHING = "-nothing"
    HITCOUNT = "-hitcount"
    SINGLEMOVE = "-singlemove"
    SINGLETURN = "-singleturn"

    # Comments and unknown
    COMMENT = "c"
    CHAT = "c:"
    JOIN = "j"
    LEAVE = "l"
    RAW = "raw"
    UNKNOWN = "unknown"


# =============================================================================
# Protocol Message
# =============================================================================

@dataclass
class ProtocolMessage:
    """A single protocol message."""
    msg_type: MessageType
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)
    raw: str = ""

    def __str__(self) -> str:
        """Convert to protocol format."""
        if self.msg_type == MessageType.EMPTY:
            return "|"
        parts = [self.msg_type.value] + self.args
        result = "|" + "|".join(parts)
        for key, value in self.kwargs.items():
            result += f"|[{key}] {value}"
        return result


# =============================================================================
# Protocol Parser
# =============================================================================

class ProtocolParser:
    """Parses Pokemon Showdown protocol messages."""

    # Regex for parsing kwargs like [from] or [of]
    KWARG_PATTERN = re.compile(r'\[(\w+)\]\s*(.+)?')

    def parse_line(self, line: str) -> ProtocolMessage:
        """Parse a single protocol line.

        Args:
            line: A line like "|move|p1a: Pikachu|Thunderbolt|p2a: Charizard"

        Returns:
            Parsed ProtocolMessage
        """
        if not line.startswith("|"):
            return ProtocolMessage(MessageType.UNKNOWN, raw=line)

        parts = line[1:].split("|")
        if not parts:
            return ProtocolMessage(MessageType.EMPTY, raw=line)

        # Get message type
        type_str = parts[0]
        try:
            msg_type = MessageType(type_str)
        except ValueError:
            # Handle - prefix for minor actions
            if type_str.startswith("-"):
                try:
                    msg_type = MessageType(type_str)
                except ValueError:
                    msg_type = MessageType.UNKNOWN
            else:
                msg_type = MessageType.UNKNOWN

        # Parse args and kwargs
        args = []
        kwargs = {}

        for part in parts[1:]:
            match = self.KWARG_PATTERN.match(part)
            if match:
                key = match.group(1)
                value = match.group(2) or ""
                kwargs[key] = value
            else:
                args.append(part)

        return ProtocolMessage(msg_type, args, kwargs, raw=line)

    def parse_log(self, log_content: str) -> List[ProtocolMessage]:
        """Parse a full battle log.

        Args:
            log_content: Full log content with newline-separated messages

        Returns:
            List of parsed messages
        """
        messages = []
        for line in log_content.strip().split("\n"):
            line = line.strip()
            if line:
                messages.append(self.parse_line(line))
        return messages

    def parse_pokemon_id(self, pokemon_id: str) -> Tuple[str, str, str]:
        """Parse a Pokemon ID like "p1a: Pikachu".

        Returns:
            (player, position, nickname) tuple
        """
        if ": " in pokemon_id:
            position, nickname = pokemon_id.split(": ", 1)
        else:
            position = pokemon_id
            nickname = ""

        # Extract player (p1, p2) and slot (a, b)
        player = position[:2] if len(position) >= 2 else position
        slot = position[2:] if len(position) > 2 else ""

        return player, slot, nickname

    def parse_details(self, details: str) -> Dict[str, Any]:
        """Parse Pokemon details string.

        Args:
            details: String like "Pikachu, L50, M, shiny, tera:Electric"

        Returns:
            Dict with species, level, gender, shiny, tera_type
        """
        result = {
            "species": "",
            "level": 100,
            "gender": None,
            "shiny": False,
            "tera_type": None,
        }

        parts = [p.strip() for p in details.split(",")]
        if not parts:
            return result

        result["species"] = parts[0]

        for part in parts[1:]:
            if part.startswith("L"):
                try:
                    result["level"] = int(part[1:])
                except ValueError:
                    pass
            elif part == "M":
                result["gender"] = "M"
            elif part == "F":
                result["gender"] = "F"
            elif part == "shiny":
                result["shiny"] = True
            elif part.startswith("tera:"):
                result["tera_type"] = part[5:]

        return result

    def parse_hp_status(self, hp_status: str) -> Tuple[int, int, Optional[str]]:
        """Parse HP and status string.

        Args:
            hp_status: String like "75/100 psn" or "0 fnt"

        Returns:
            (current_hp, max_hp, status) tuple
        """
        hp_status = hp_status.replace("\\/", "/")  # Handle escaped slashes

        parts = hp_status.split()
        hp_part = parts[0] if parts else "100/100"
        status = parts[1] if len(parts) > 1 else None

        if "/" in hp_part:
            current, max_hp = hp_part.split("/")
            try:
                return int(current), int(max_hp), status
            except ValueError:
                return 100, 100, status
        else:
            # Just a number (percentage or 0)
            try:
                val = int(hp_part)
                return val, 100, status
            except ValueError:
                return 100, 100, status


# =============================================================================
# Protocol Emitter
# =============================================================================

class ProtocolEmitter:
    """Emits Pokemon Showdown protocol messages."""

    def __init__(self):
        self.messages: List[str] = []

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []

    def emit(self, msg: str) -> None:
        """Add a message to the output."""
        self.messages.append(msg)

    def get_output(self) -> str:
        """Get all messages as a string."""
        return "\n".join(self.messages)

    # Battle initialization
    def player(self, player_id: str, name: str, avatar: str = "", rating: int = 0) -> None:
        """Emit |player| message."""
        self.emit(f"|player|{player_id}|{name}|{avatar}|{rating if rating else ''}")

    def teamsize(self, player_id: str, size: int) -> None:
        """Emit |teamsize| message."""
        self.emit(f"|teamsize|{player_id}|{size}")

    def gametype(self, gametype: str) -> None:
        """Emit |gametype| message."""
        self.emit(f"|gametype|{gametype}")

    def gen(self, gen: int) -> None:
        """Emit |gen| message."""
        self.emit(f"|gen|{gen}")

    def tier(self, tier: str) -> None:
        """Emit |tier| message."""
        self.emit(f"|tier|{tier}")

    def rule(self, rule: str) -> None:
        """Emit |rule| message."""
        self.emit(f"|rule|{rule}")

    def clearpoke(self) -> None:
        """Emit |clearpoke| message."""
        self.emit("|clearpoke")

    def poke(self, player_id: str, details: str, has_item: bool = False) -> None:
        """Emit |poke| message."""
        item_str = "item" if has_item else ""
        self.emit(f"|poke|{player_id}|{details}|{item_str}")

    def teampreview(self, count: Optional[int] = None) -> None:
        """Emit |teampreview| message."""
        if count:
            self.emit(f"|teampreview|{count}")
        else:
            self.emit("|teampreview")

    def start(self) -> None:
        """Emit |start| message."""
        self.emit("|start")

    # Battle progress
    def spacer(self) -> None:
        """Emit empty line (spacer)."""
        self.emit("|")

    def turn(self, turn_number: int) -> None:
        """Emit |turn| message."""
        self.emit(f"|turn|{turn_number}")

    def upkeep(self) -> None:
        """Emit |upkeep| message."""
        self.emit("|upkeep")

    def win(self, player_name: str) -> None:
        """Emit |win| message."""
        self.emit(f"|win|{player_name}")

    def tie(self) -> None:
        """Emit |tie| message."""
        self.emit("|tie")

    # Major actions
    def switch(self, pokemon_id: str, details: str, hp_status: str) -> None:
        """Emit |switch| message."""
        self.emit(f"|switch|{pokemon_id}|{details}|{hp_status}")

    def drag(self, pokemon_id: str, details: str, hp_status: str) -> None:
        """Emit |drag| message."""
        self.emit(f"|drag|{pokemon_id}|{details}|{hp_status}")

    def move(self, pokemon_id: str, move_name: str, target_id: str = "",
             miss: bool = False, spread: bool = False) -> None:
        """Emit |move| message."""
        msg = f"|move|{pokemon_id}|{move_name}|{target_id}"
        if spread:
            msg += "|[spread]"
        if miss:
            msg += "|[miss]"
        self.emit(msg)

    def cant(self, pokemon_id: str, reason: str, move: str = "") -> None:
        """Emit |cant| message."""
        if move:
            self.emit(f"|cant|{pokemon_id}|{reason}|{move}")
        else:
            self.emit(f"|cant|{pokemon_id}|{reason}")

    def faint(self, pokemon_id: str) -> None:
        """Emit |faint| message."""
        self.emit(f"|faint|{pokemon_id}")

    # Minor actions (damage/HP)
    def damage(self, pokemon_id: str, hp_status: str, source: str = "",
               of_pokemon: str = "") -> None:
        """Emit |-damage| message."""
        msg = f"|-damage|{pokemon_id}|{hp_status}"
        if source:
            msg += f"|[from] {source}"
        if of_pokemon:
            msg += f"|[of] {of_pokemon}"
        self.emit(msg)

    def heal(self, pokemon_id: str, hp_status: str, source: str = "",
             of_pokemon: str = "") -> None:
        """Emit |-heal| message."""
        msg = f"|-heal|{pokemon_id}|{hp_status}"
        if source:
            msg += f"|[from] {source}"
        if of_pokemon:
            msg += f"|[of] {of_pokemon}"
        self.emit(msg)

    # Status
    def status(self, pokemon_id: str, status: str, source: str = "",
               of_pokemon: str = "") -> None:
        """Emit |-status| message."""
        msg = f"|-status|{pokemon_id}|{status}"
        if source:
            msg += f"|[from] {source}"
        if of_pokemon:
            msg += f"|[of] {of_pokemon}"
        self.emit(msg)

    def curestatus(self, pokemon_id: str, status: str, source: str = "") -> None:
        """Emit |-curestatus| message."""
        msg = f"|-curestatus|{pokemon_id}|{status}"
        if source:
            msg += f"|[from] {source}"
        self.emit(msg)

    # Stat changes
    def boost(self, pokemon_id: str, stat: str, amount: int) -> None:
        """Emit |-boost| message."""
        self.emit(f"|-boost|{pokemon_id}|{stat}|{amount}")

    def unboost(self, pokemon_id: str, stat: str, amount: int) -> None:
        """Emit |-unboost| message."""
        self.emit(f"|-unboost|{pokemon_id}|{stat}|{amount}")

    def clearboost(self, pokemon_id: str) -> None:
        """Emit |-clearboost| message."""
        self.emit(f"|-clearboost|{pokemon_id}")

    # Field effects
    def weather(self, weather: str, source: str = "", upkeep: bool = False) -> None:
        """Emit |-weather| message."""
        msg = f"|-weather|{weather}"
        if upkeep:
            msg += "|[upkeep]"
        if source:
            msg += f"|[from] {source}"
        self.emit(msg)

    def fieldstart(self, condition: str, source: str = "", of_pokemon: str = "") -> None:
        """Emit |-fieldstart| message."""
        msg = f"|-fieldstart|{condition}"
        if source:
            msg += f"|[from] {source}"
        if of_pokemon:
            msg += f"|[of] {of_pokemon}"
        self.emit(msg)

    def fieldend(self, condition: str) -> None:
        """Emit |-fieldend| message."""
        self.emit(f"|-fieldend|{condition}")

    def sidestart(self, side: str, condition: str) -> None:
        """Emit |-sidestart| message."""
        self.emit(f"|-sidestart|{side}|{condition}")

    def sideend(self, side: str, condition: str) -> None:
        """Emit |-sideend| message."""
        self.emit(f"|-sideend|{side}|{condition}")

    # Type effectiveness
    def supereffective(self, pokemon_id: str) -> None:
        """Emit |-supereffective| message."""
        self.emit(f"|-supereffective|{pokemon_id}")

    def resisted(self, pokemon_id: str) -> None:
        """Emit |-resisted| message."""
        self.emit(f"|-resisted|{pokemon_id}")

    def immune(self, pokemon_id: str) -> None:
        """Emit |-immune| message."""
        self.emit(f"|-immune|{pokemon_id}")

    def crit(self, pokemon_id: str) -> None:
        """Emit |-crit| message."""
        self.emit(f"|-crit|{pokemon_id}")

    # Abilities and items
    def ability(self, pokemon_id: str, ability: str, source: str = "",
                of_pokemon: str = "") -> None:
        """Emit |-ability| message."""
        msg = f"|-ability|{pokemon_id}|{ability}"
        if source:
            msg += f"|[from] {source}"
        if of_pokemon:
            msg += f"|[of] {of_pokemon}"
        self.emit(msg)

    def item(self, pokemon_id: str, item: str, source: str = "") -> None:
        """Emit |-item| message."""
        msg = f"|-item|{pokemon_id}|{item}"
        if source:
            msg += f"|[from] {source}"
        self.emit(msg)

    def enditem(self, pokemon_id: str, item: str, source: str = "") -> None:
        """Emit |-enditem| message."""
        msg = f"|-enditem|{pokemon_id}|{item}"
        if source:
            msg += f"|[from] {source}"
        self.emit(msg)

    # Volatile status
    def start_volatile(self, pokemon_id: str, effect: str, source: str = "",
                       of_pokemon: str = "") -> None:
        """Emit |-start| message for volatile status."""
        msg = f"|-start|{pokemon_id}|{effect}"
        if source:
            msg += f"|[from] {source}"
        if of_pokemon:
            msg += f"|[of] {of_pokemon}"
        self.emit(msg)

    def end_volatile(self, pokemon_id: str, effect: str) -> None:
        """Emit |-end| message for volatile status."""
        self.emit(f"|-end|{pokemon_id}|{effect}")

    # Protection
    def activate(self, pokemon_id: str, effect: str) -> None:
        """Emit |-activate| message."""
        self.emit(f"|-activate|{pokemon_id}|{effect}")

    def singleturn(self, pokemon_id: str, move: str, of_pokemon: str = "") -> None:
        """Emit |-singleturn| message."""
        msg = f"|-singleturn|{pokemon_id}|{move}"
        if of_pokemon:
            msg += f"|[of] {of_pokemon}"
        self.emit(msg)

    # Terastallization
    def terastallize(self, pokemon_id: str, tera_type: str) -> None:
        """Emit |-terastallize| message."""
        self.emit(f"|-terastallize|{pokemon_id}|{tera_type}")

    # Misc
    def fail(self, pokemon_id: str, action: str = "") -> None:
        """Emit |-fail| message."""
        if action:
            self.emit(f"|-fail|{pokemon_id}|{action}")
        else:
            self.emit(f"|-fail|{pokemon_id}")

    def miss(self, source_id: str, target_id: str = "") -> None:
        """Emit |-miss| message."""
        if target_id:
            self.emit(f"|-miss|{source_id}|{target_id}")
        else:
            self.emit(f"|-miss|{source_id}")

    def hitcount(self, pokemon_id: str, count: int) -> None:
        """Emit |-hitcount| message."""
        self.emit(f"|-hitcount|{pokemon_id}|{count}")


# =============================================================================
# Choice Parser
# =============================================================================

@dataclass
class Choice:
    """A player choice for a single Pokemon."""
    choice_type: str  # "move", "switch", "pass", "default"
    slot: int = 0
    move_slot: int = -1  # 1-4 for moves
    move_name: str = ""
    target: int = 0  # Target slot (+1, +2, -1, -2)
    switch_to: int = -1  # 1-6 for team slot
    switch_name: str = ""
    mega: bool = False
    zmove: bool = False
    dynamax: bool = False
    terastallize: bool = False


class ChoiceParser:
    """Parses player choice commands."""

    def parse_choice(self, choice_str: str) -> List[Choice]:
        """Parse a choice string like "move 1 +2, switch 3".

        Args:
            choice_str: Choice string from protocol

        Returns:
            List of Choice objects (one per active Pokemon)
        """
        choices = []

        # Split by comma for doubles/triples
        parts = [p.strip() for p in choice_str.split(",")]

        for i, part in enumerate(parts):
            choice = self._parse_single_choice(part, slot=i)
            choices.append(choice)

        return choices

    def _parse_single_choice(self, choice_str: str, slot: int = 0) -> Choice:
        """Parse a single Pokemon's choice."""
        tokens = choice_str.strip().split()
        if not tokens:
            return Choice("pass", slot=slot)

        action = tokens[0].lower()

        if action == "pass":
            return Choice("pass", slot=slot)

        if action == "default":
            return Choice("default", slot=slot)

        if action == "move":
            return self._parse_move_choice(tokens[1:], slot)

        if action == "switch":
            return self._parse_switch_choice(tokens[1:], slot)

        # Unknown choice type
        return Choice("pass", slot=slot)

    def _parse_move_choice(self, tokens: List[str], slot: int) -> Choice:
        """Parse move choice tokens."""
        choice = Choice("move", slot=slot)

        if not tokens:
            return choice

        # First token is move slot/name
        move_spec = tokens[0]
        try:
            choice.move_slot = int(move_spec)
        except ValueError:
            choice.move_name = move_spec

        # Parse remaining tokens
        i = 1
        while i < len(tokens):
            token = tokens[i].lower()

            if token == "mega":
                choice.mega = True
            elif token == "zmove":
                choice.zmove = True
            elif token == "max":
                choice.dynamax = True
            elif token == "terastallize":
                choice.terastallize = True
            elif token.startswith("+") or token.startswith("-"):
                # Target specification
                try:
                    choice.target = int(token)
                except ValueError:
                    pass
            else:
                # Could be target number without sign
                try:
                    choice.target = int(token)
                except ValueError:
                    pass

            i += 1

        return choice

    def _parse_switch_choice(self, tokens: List[str], slot: int) -> Choice:
        """Parse switch choice tokens."""
        choice = Choice("switch", slot=slot)

        if not tokens:
            return choice

        # First token is switch target
        switch_spec = tokens[0]
        try:
            choice.switch_to = int(switch_spec)
        except ValueError:
            choice.switch_name = switch_spec

        return choice

    def format_choice(self, choices: List[Choice]) -> str:
        """Format choices back to protocol string."""
        parts = []

        for choice in choices:
            if choice.choice_type == "pass":
                parts.append("pass")
            elif choice.choice_type == "default":
                parts.append("default")
            elif choice.choice_type == "move":
                move_str = f"move {choice.move_slot if choice.move_slot > 0 else choice.move_name}"
                if choice.target != 0:
                    sign = "+" if choice.target > 0 else ""
                    move_str += f" {sign}{choice.target}"
                if choice.mega:
                    move_str += " mega"
                if choice.zmove:
                    move_str += " zmove"
                if choice.dynamax:
                    move_str += " max"
                if choice.terastallize:
                    move_str += " terastallize"
                parts.append(move_str)
            elif choice.choice_type == "switch":
                switch_str = f"switch {choice.switch_to if choice.switch_to > 0 else choice.switch_name}"
                parts.append(switch_str)

        return ", ".join(parts)


# =============================================================================
# Battle Replay from Protocol
# =============================================================================

@dataclass
class ReplayState:
    """State tracked during replay."""
    turn: int = 0
    weather: Optional[str] = None
    terrain: Optional[str] = None
    pokemon_hp: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # slot -> (current, max)
    pokemon_status: Dict[str, Optional[str]] = field(default_factory=dict)
    pokemon_boosts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    side_conditions: Dict[str, List[str]] = field(default_factory=lambda: {"p1": [], "p2": []})
    winner: Optional[str] = None


class ProtocolReplayer:
    """Replays a battle from protocol messages."""

    def __init__(self):
        self.parser = ProtocolParser()
        self.state = ReplayState()
        self.events: List[Dict[str, Any]] = []

    def replay(self, log_content: str) -> ReplayState:
        """Replay a battle log and return final state.

        Args:
            log_content: Full battle log in protocol format

        Returns:
            Final battle state
        """
        self.state = ReplayState()
        self.events = []

        messages = self.parser.parse_log(log_content)

        for msg in messages:
            self._process_message(msg)

        return self.state

    def _process_message(self, msg: ProtocolMessage) -> None:
        """Process a single protocol message."""
        handlers = {
            MessageType.TURN: self._handle_turn,
            MessageType.SWITCH: self._handle_switch,
            MessageType.DRAG: self._handle_switch,
            MessageType.MOVE: self._handle_move,
            MessageType.DAMAGE: self._handle_damage,
            MessageType.HEAL: self._handle_heal,
            MessageType.FAINT: self._handle_faint,
            MessageType.STATUS: self._handle_status,
            MessageType.CURESTATUS: self._handle_curestatus,
            MessageType.BOOST: self._handle_boost,
            MessageType.UNBOOST: self._handle_unboost,
            MessageType.WEATHER: self._handle_weather,
            MessageType.FIELDSTART: self._handle_fieldstart,
            MessageType.FIELDEND: self._handle_fieldend,
            MessageType.SIDESTART: self._handle_sidestart,
            MessageType.SIDEEND: self._handle_sideend,
            MessageType.WIN: self._handle_win,
            MessageType.TIE: self._handle_tie,
        }

        handler = handlers.get(msg.msg_type)
        if handler:
            handler(msg)

    def _handle_turn(self, msg: ProtocolMessage) -> None:
        if msg.args:
            try:
                self.state.turn = int(msg.args[0])
            except ValueError:
                pass
        self.events.append({"type": "turn", "turn": self.state.turn})

    def _handle_switch(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 3:
            pokemon_id = msg.args[0]
            details = msg.args[1]
            hp_status = msg.args[2]

            player, slot, nickname = self.parser.parse_pokemon_id(pokemon_id)
            current_hp, max_hp, status = self.parser.parse_hp_status(hp_status)

            full_slot = f"{player}{slot}"
            self.state.pokemon_hp[full_slot] = (current_hp, max_hp)
            self.state.pokemon_status[full_slot] = status
            self.state.pokemon_boosts[full_slot] = {}

            self.events.append({
                "type": "switch",
                "slot": full_slot,
                "species": self.parser.parse_details(details)["species"],
                "hp": current_hp,
                "max_hp": max_hp,
            })

    def _handle_move(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 2:
            pokemon_id = msg.args[0]
            move_name = msg.args[1]
            target_id = msg.args[2] if len(msg.args) > 2 else ""

            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)

            self.events.append({
                "type": "move",
                "user": f"{player}{slot}",
                "move": move_name,
                "target": target_id,
                "spread": "spread" in msg.kwargs,
            })

    def _handle_damage(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 2:
            pokemon_id = msg.args[0]
            hp_status = msg.args[1]

            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)
            current_hp, max_hp, status = self.parser.parse_hp_status(hp_status)

            full_slot = f"{player}{slot}"
            old_hp = self.state.pokemon_hp.get(full_slot, (100, 100))[0]

            self.state.pokemon_hp[full_slot] = (current_hp, max_hp)
            if status:
                self.state.pokemon_status[full_slot] = status

            self.events.append({
                "type": "damage",
                "slot": full_slot,
                "hp_before": old_hp,
                "hp_after": current_hp,
                "damage": old_hp - current_hp,
                "source": msg.kwargs.get("from", ""),
            })

    def _handle_heal(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 2:
            pokemon_id = msg.args[0]
            hp_status = msg.args[1]

            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)
            current_hp, max_hp, status = self.parser.parse_hp_status(hp_status)

            full_slot = f"{player}{slot}"
            old_hp = self.state.pokemon_hp.get(full_slot, (0, 100))[0]

            self.state.pokemon_hp[full_slot] = (current_hp, max_hp)

            self.events.append({
                "type": "heal",
                "slot": full_slot,
                "hp_before": old_hp,
                "hp_after": current_hp,
                "healed": current_hp - old_hp,
                "source": msg.kwargs.get("from", ""),
            })

    def _handle_faint(self, msg: ProtocolMessage) -> None:
        if msg.args:
            pokemon_id = msg.args[0]
            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)
            full_slot = f"{player}{slot}"

            self.state.pokemon_hp[full_slot] = (0, self.state.pokemon_hp.get(full_slot, (0, 100))[1])

            self.events.append({"type": "faint", "slot": full_slot})

    def _handle_status(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 2:
            pokemon_id = msg.args[0]
            status = msg.args[1]

            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)
            full_slot = f"{player}{slot}"

            self.state.pokemon_status[full_slot] = status

            self.events.append({
                "type": "status",
                "slot": full_slot,
                "status": status,
                "source": msg.kwargs.get("from", ""),
            })

    def _handle_curestatus(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 2:
            pokemon_id = msg.args[0]

            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)
            full_slot = f"{player}{slot}"

            old_status = self.state.pokemon_status.get(full_slot)
            self.state.pokemon_status[full_slot] = None

            self.events.append({
                "type": "curestatus",
                "slot": full_slot,
                "status": old_status,
            })

    def _handle_boost(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 3:
            pokemon_id = msg.args[0]
            stat = msg.args[1]
            amount = int(msg.args[2])

            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)
            full_slot = f"{player}{slot}"

            if full_slot not in self.state.pokemon_boosts:
                self.state.pokemon_boosts[full_slot] = {}

            current = self.state.pokemon_boosts[full_slot].get(stat, 0)
            self.state.pokemon_boosts[full_slot][stat] = current + amount

            self.events.append({
                "type": "boost",
                "slot": full_slot,
                "stat": stat,
                "amount": amount,
            })

    def _handle_unboost(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 3:
            pokemon_id = msg.args[0]
            stat = msg.args[1]
            amount = int(msg.args[2])

            player, slot, _ = self.parser.parse_pokemon_id(pokemon_id)
            full_slot = f"{player}{slot}"

            if full_slot not in self.state.pokemon_boosts:
                self.state.pokemon_boosts[full_slot] = {}

            current = self.state.pokemon_boosts[full_slot].get(stat, 0)
            self.state.pokemon_boosts[full_slot][stat] = current - amount

            self.events.append({
                "type": "unboost",
                "slot": full_slot,
                "stat": stat,
                "amount": amount,
            })

    def _handle_weather(self, msg: ProtocolMessage) -> None:
        if msg.args:
            weather = msg.args[0]
            if weather == "none":
                self.state.weather = None
            else:
                self.state.weather = weather

            self.events.append({
                "type": "weather",
                "weather": self.state.weather,
                "upkeep": "upkeep" in msg.kwargs,
            })

    def _handle_fieldstart(self, msg: ProtocolMessage) -> None:
        if msg.args:
            condition = msg.args[0]

            # Extract terrain from "move: Psychic Terrain" format
            if condition.startswith("move: "):
                terrain = condition[6:]
                if "Terrain" in terrain:
                    self.state.terrain = terrain.replace(" Terrain", "").lower()

            self.events.append({
                "type": "fieldstart",
                "condition": condition,
            })

    def _handle_fieldend(self, msg: ProtocolMessage) -> None:
        if msg.args:
            condition = msg.args[0]

            if "Terrain" in condition:
                self.state.terrain = None

            self.events.append({
                "type": "fieldend",
                "condition": condition,
            })

    def _handle_sidestart(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 2:
            side = msg.args[0]
            condition = msg.args[1]

            # Extract player from "p1: PlayerName"
            player = side.split(":")[0].strip()

            if player in self.state.side_conditions:
                self.state.side_conditions[player].append(condition)

            self.events.append({
                "type": "sidestart",
                "side": player,
                "condition": condition,
            })

    def _handle_sideend(self, msg: ProtocolMessage) -> None:
        if len(msg.args) >= 2:
            side = msg.args[0]
            condition = msg.args[1]

            player = side.split(":")[0].strip()

            if player in self.state.side_conditions:
                if condition in self.state.side_conditions[player]:
                    self.state.side_conditions[player].remove(condition)

            self.events.append({
                "type": "sideend",
                "side": player,
                "condition": condition,
            })

    def _handle_win(self, msg: ProtocolMessage) -> None:
        if msg.args:
            self.state.winner = msg.args[0]
            self.events.append({"type": "win", "winner": self.state.winner})

    def _handle_tie(self, msg: ProtocolMessage) -> None:
        self.state.winner = "tie"
        self.events.append({"type": "tie"})


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "MessageType",
    "ProtocolMessage",
    "ProtocolParser",
    "ProtocolEmitter",
    "Choice",
    "ChoiceParser",
    "ReplayState",
    "ProtocolReplayer",
]
