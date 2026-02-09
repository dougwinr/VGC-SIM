"""Loader for Pokemon move data from Showdown TypeScript format.

This module parses the moves_data.ts file and creates MoveData objects
for all moves.
"""
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .moves import (
    MoveData,
    MoveCategory,
    MoveTarget,
    MoveFlag,
    SecondaryEffect,
    TARGET_BY_NAME,
    CATEGORY_BY_NAME,
    FLAG_BY_NAME,
)
from .types import Type, TYPE_BY_NAME


# Move registry
MOVE_REGISTRY: Dict[int, MoveData] = {}
MOVE_BY_NAME: Dict[str, int] = {}


def _parse_type(type_name: str) -> Optional[Type]:
    """Parse a type name string to Type enum."""
    if not type_name:
        return None
    normalized = type_name.lower()
    return TYPE_BY_NAME.get(normalized)


def _parse_category(category_name: str) -> MoveCategory:
    """Parse category string to MoveCategory enum."""
    if not category_name:
        return MoveCategory.STATUS
    return CATEGORY_BY_NAME.get(category_name.lower(), MoveCategory.STATUS)


def _parse_target(target_name: str) -> MoveTarget:
    """Parse target string to MoveTarget enum."""
    if not target_name:
        return MoveTarget.NORMAL
    return TARGET_BY_NAME.get(target_name, MoveTarget.NORMAL)


def _parse_flags(flags_dict: Dict[str, Any]) -> MoveFlag:
    """Parse flags dict to MoveFlag bitflags."""
    flags = MoveFlag.NONE
    for flag_name, value in flags_dict.items():
        if value:
            flag = FLAG_BY_NAME.get(flag_name.lower())
            if flag:
                flags |= flag
    return flags


def parse_ts_moves(ts_content: str) -> Dict[str, Dict[str, Any]]:
    """Parse TypeScript moves data into a dictionary.

    Args:
        ts_content: The TypeScript file content

    Returns:
        Dictionary mapping move keys to their data
    """
    result = {}

    # Find entries - can be unquoted identifiers or quoted strings
    # Pattern for unquoted: ^\t(\w+):\s*\{
    # Pattern for quoted: ^\t"([^"]+)":\s*\{
    unquoted_starts = list(re.finditer(r'^\t(\w+):\s*\{', ts_content, re.MULTILINE))
    quoted_starts = list(re.finditer(r'^\t"([^"]+)":\s*\{', ts_content, re.MULTILINE))

    # Combine and sort by position
    all_entries = [(m.start(), m.group(1), m) for m in unquoted_starts]
    all_entries += [(m.start(), m.group(1), m) for m in quoted_starts]
    all_entries.sort(key=lambda x: x[0])

    for i, (start_pos, key, match) in enumerate(all_entries):
        if i + 1 < len(all_entries):
            end_pos = all_entries[i + 1][0]
        else:
            end_pos = len(ts_content)

        obj_content = ts_content[start_pos:end_pos]
        obj = _extract_move_fields(obj_content)
        if obj and obj.get("num") is not None:
            result[key] = obj

    return result


def _extract_move_fields(obj_content: str) -> Dict[str, Any]:
    """Extract move fields using regex patterns."""
    result = {}

    # Extract num
    num_match = re.search(r'^\t\tnum:\s*(\d+)', obj_content, re.MULTILINE)
    if num_match:
        result["num"] = int(num_match.group(1))

    # Extract name
    name_match = re.search(r'^\t\tname:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1)

    # Extract type
    type_match = re.search(r'^\t\ttype:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if type_match:
        result["type"] = type_match.group(1)

    # Extract category
    cat_match = re.search(r'^\t\tcategory:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if cat_match:
        result["category"] = cat_match.group(1)

    # Extract basePower
    bp_match = re.search(r'^\t\tbasePower:\s*(\d+)', obj_content, re.MULTILINE)
    if bp_match:
        result["basePower"] = int(bp_match.group(1))

    # Extract accuracy
    acc_match = re.search(r'^\t\taccuracy:\s*(\d+|true)', obj_content, re.MULTILINE)
    if acc_match:
        val = acc_match.group(1)
        result["accuracy"] = True if val == "true" else int(val)

    # Extract pp
    pp_match = re.search(r'^\t\tpp:\s*(\d+)', obj_content, re.MULTILINE)
    if pp_match:
        result["pp"] = int(pp_match.group(1))

    # Extract priority
    pri_match = re.search(r'^\t\tpriority:\s*(-?\d+)', obj_content, re.MULTILINE)
    if pri_match:
        result["priority"] = int(pri_match.group(1))

    # Extract target
    target_match = re.search(r'^\t\ttarget:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if target_match:
        result["target"] = target_match.group(1)

    # Extract critRatio
    crit_match = re.search(r'^\t\tcritRatio:\s*(\d+)', obj_content, re.MULTILINE)
    if crit_match:
        result["critRatio"] = int(crit_match.group(1))

    # Extract drain
    drain_match = re.search(r'^\t\tdrain:\s*\[(\d+),\s*(\d+)\]', obj_content, re.MULTILINE)
    if drain_match:
        result["drain"] = [int(drain_match.group(1)), int(drain_match.group(2))]

    # Extract recoil
    recoil_match = re.search(r'^\t\trecoil:\s*\[(\d+),\s*(\d+)\]', obj_content, re.MULTILINE)
    if recoil_match:
        result["recoil"] = [int(recoil_match.group(1)), int(recoil_match.group(2))]

    # Extract multihit
    multi_match = re.search(r'^\t\tmultihit:\s*(\d+|\[[\d,\s]+\])', obj_content, re.MULTILINE)
    if multi_match:
        val = multi_match.group(1)
        if val.startswith("["):
            nums = re.findall(r'\d+', val)
            result["multihit"] = [int(n) for n in nums]
        else:
            result["multihit"] = int(val)

    # Extract flags
    flags = {}
    flags_match = re.search(r'^\t\tflags:\s*\{([^}]*)\}', obj_content, re.MULTILINE)
    if flags_match:
        flags_content = flags_match.group(1)
        for flag_name in ["contact", "protect", "mirror", "sound", "bullet", "bite",
                          "punch", "powder", "charge", "recharge", "heal", "gravity",
                          "distance", "defrost", "bypasssub", "reflectable", "snatch",
                          "nonsky", "dance", "slicing", "wind", "metronome"]:
            if re.search(rf'\b{flag_name}:\s*1', flags_content):
                flags[flag_name] = 1
    result["flags"] = flags

    # Check for isZ
    if re.search(r'^\t\tisZ:', obj_content, re.MULTILINE):
        result["isZ"] = True

    # Check for isMax
    if re.search(r'^\t\tisMax:', obj_content, re.MULTILINE):
        result["isMax"] = True

    # Extract isNonstandard
    nonstandard_match = re.search(r'^\t\tisNonstandard:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if nonstandard_match:
        result["isNonstandard"] = nonstandard_match.group(1)

    return result


def register_move(move: MoveData) -> None:
    """Register a move in the registry."""
    MOVE_REGISTRY[move.id] = move
    MOVE_BY_NAME[move.name.lower().replace(" ", "").replace("-", "").replace(",", "")] = move.id


def get_move(move_id: int) -> Optional[MoveData]:
    """Get move by ID."""
    return MOVE_REGISTRY.get(move_id)


def get_move_id(name: str) -> Optional[int]:
    """Get move ID by name."""
    normalized = name.lower().replace(" ", "").replace("-", "").replace(",", "")
    return MOVE_BY_NAME.get(normalized)


def get_move_by_name(name: str) -> Optional[MoveData]:
    """Get move by name."""
    move_id = get_move_id(name)
    if move_id is not None:
        return MOVE_REGISTRY.get(move_id)
    return None


def load_moves_from_ts(ts_path: str) -> int:
    """Load move data from a TypeScript moves file."""
    path = Path(ts_path)
    if not path.exists():
        raise FileNotFoundError(f"Moves file not found: {ts_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    moves_data = parse_ts_moves(content)

    loaded_count = 0
    for key, data in moves_data.items():
        move_num = data.get("num")
        if move_num is None:
            continue

        name = data.get("name", key.capitalize())
        move_type = _parse_type(data.get("type", "Normal"))
        if move_type is None:
            move_type = Type.NORMAL

        category = _parse_category(data.get("category", "Status"))
        base_power = data.get("basePower", 0) or 0
        accuracy = data.get("accuracy")
        if accuracy is True:
            accuracy = None
        elif accuracy is None or accuracy is False:
            accuracy = 100

        pp = data.get("pp", 5) or 5
        priority = data.get("priority", 0) or 0
        target = _parse_target(data.get("target", "normal"))
        flags = _parse_flags(data.get("flags", {}))
        crit_ratio = data.get("critRatio", 1) or 1

        drain = 0.0
        drain_data = data.get("drain")
        if drain_data and isinstance(drain_data, list) and len(drain_data) == 2:
            drain = drain_data[0] / drain_data[1]

        recoil = 0.0
        recoil_data = data.get("recoil")
        if recoil_data and isinstance(recoil_data, list) and len(recoil_data) == 2:
            recoil = recoil_data[0] / recoil_data[1]

        multi_hit = None
        multi_data = data.get("multihit")
        if multi_data:
            if isinstance(multi_data, int):
                multi_hit = (multi_data, multi_data)
            elif isinstance(multi_data, list) and len(multi_data) == 2:
                multi_hit = (multi_data[0], multi_data[1])

        is_z_move = bool(data.get("isZ"))
        is_max_move = bool(data.get("isMax"))

        move = MoveData(
            id=move_num,
            name=name,
            type=move_type,
            category=category,
            base_power=base_power,
            accuracy=accuracy,
            pp=pp,
            priority=priority,
            target=target,
            flags=flags,
            crit_ratio=crit_ratio,
            drain=drain,
            recoil=recoil,
            secondary=None,
            multi_hit=multi_hit,
            is_z_move=is_z_move,
            is_max_move=is_max_move,
        )

        register_move(move)
        loaded_count += 1

    return loaded_count


def load_default_moves() -> int:
    """Load moves from the default location."""
    module_dir = Path(__file__).parent
    possible_paths = [
        module_dir / "raw" / "moves_data.ts",
        module_dir.parent / "doc" / "moves_data.ts",
    ]

    for path in possible_paths:
        if path.exists():
            return load_moves_from_ts(str(path))

    raise FileNotFoundError(
        "Could not find moves_data.ts. Looked in: " +
        ", ".join(str(p) for p in possible_paths)
    )


def ensure_moves_loaded() -> None:
    """Ensure move data is loaded."""
    if len(MOVE_REGISTRY) == 0:
        try:
            load_default_moves()
        except FileNotFoundError:
            pass


def get_move_count() -> int:
    """Get the number of loaded moves."""
    return len(MOVE_REGISTRY)


def _auto_load_moves() -> None:
    """Automatically load move data."""
    if len(MOVE_REGISTRY) == 0:
        try:
            load_default_moves()
        except (FileNotFoundError, Exception):
            pass


_auto_load_moves()
