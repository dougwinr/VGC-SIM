"""Loader for Pokemon item data from Showdown TypeScript format.

This module parses the items_data.ts file and creates ItemData objects
for all items.
"""
import re
from pathlib import Path
from typing import Any, Dict, Optional

from .items import (
    ItemData,
    ItemFlag,
    ITEM_REGISTRY,
    ITEM_BY_NAME,
    register_item,
)
from .types import Type, TYPE_BY_NAME


def _parse_type(type_name: str) -> Optional[Type]:
    """Parse a type name string to Type enum."""
    if not type_name:
        return None
    normalized = type_name.lower()
    return TYPE_BY_NAME.get(normalized)


def _parse_item_flags(data: Dict[str, Any]) -> ItemFlag:
    """Parse item flags from data dict."""
    flags = ItemFlag.NONE

    if data.get("isBerry"):
        flags |= ItemFlag.CONSUMABLE | ItemFlag.BERRY
    if data.get("isGem"):
        flags |= ItemFlag.CONSUMABLE | ItemFlag.GEM
    if data.get("onPlate"):
        flags |= ItemFlag.PLATE
    if data.get("onDrive"):
        flags |= ItemFlag.DRIVE
    if data.get("onMemory"):
        flags |= ItemFlag.MEMORY
    if data.get("megaStone"):
        flags |= ItemFlag.MEGA_STONE
    if data.get("zMove"):
        flags |= ItemFlag.Z_CRYSTAL

    name = data.get("name", "").lower()
    if "choice" in name and any(x in name for x in ["band", "specs", "scarf"]):
        flags |= ItemFlag.CHOICE

    return flags


def parse_ts_items(ts_content: str) -> Dict[str, Dict[str, Any]]:
    """Parse TypeScript items data into a dictionary.

    Args:
        ts_content: The TypeScript file content

    Returns:
        Dictionary mapping item keys to their data
    """
    result = {}

    # Find all top-level entries: lines starting with \t followed by identifier: {
    entry_starts = list(re.finditer(r'^\t(\w+):\s*\{', ts_content, re.MULTILINE))

    for i, match in enumerate(entry_starts):
        key = match.group(1)
        start_pos = match.start()

        if i + 1 < len(entry_starts):
            end_pos = entry_starts[i + 1].start()
        else:
            end_pos = len(ts_content)

        obj_content = ts_content[start_pos:end_pos]
        obj = _extract_item_fields(obj_content)
        if obj and obj.get("num") is not None:
            result[key] = obj

    return result


def _extract_item_fields(obj_content: str) -> Dict[str, Any]:
    """Extract item fields using regex patterns."""
    result = {}

    # Extract num
    num_match = re.search(r'^\t\tnum:\s*(\d+)', obj_content, re.MULTILINE)
    if num_match:
        result["num"] = int(num_match.group(1))

    # Extract name
    name_match = re.search(r'^\t\tname:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1)

    # Extract shortDesc
    desc_match = re.search(r'^\t\tshortDesc:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if desc_match:
        result["shortDesc"] = desc_match.group(1)

    # Extract desc
    full_desc_match = re.search(r'^\t\tdesc:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if full_desc_match:
        result["desc"] = full_desc_match.group(1)

    # Extract fling basePower
    fling_match = re.search(r'fling:\s*\{[^}]*basePower:\s*(\d+)', obj_content)
    if fling_match:
        result["fling"] = {"basePower": int(fling_match.group(1))}

    # Extract gen
    gen_match = re.search(r'^\t\tgen:\s*(\d+)', obj_content, re.MULTILINE)
    if gen_match:
        result["gen"] = int(gen_match.group(1))

    # Extract isBerry
    if re.search(r'^\t\tisBerry:\s*true', obj_content, re.MULTILINE):
        result["isBerry"] = True

    # Extract isGem
    if re.search(r'^\t\tisGem:\s*true', obj_content, re.MULTILINE):
        result["isGem"] = True

    # Extract onPlate
    plate_match = re.search(r'^\t\tonPlate:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if plate_match:
        result["onPlate"] = plate_match.group(1)

    # Extract onDrive
    drive_match = re.search(r'^\t\tonDrive:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if drive_match:
        result["onDrive"] = drive_match.group(1)

    # Extract onMemory
    memory_match = re.search(r'^\t\tonMemory:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if memory_match:
        result["onMemory"] = memory_match.group(1)

    # Check for megaStone
    if re.search(r'^\t\tmegaStone:', obj_content, re.MULTILINE):
        result["megaStone"] = True

    # Check for zMove
    if re.search(r'^\t\tzMove:', obj_content, re.MULTILINE) or \
       re.search(r'^\t\tzMoveType:', obj_content, re.MULTILINE):
        result["zMove"] = True

    # Extract isNonstandard
    nonstandard_match = re.search(r'^\t\tisNonstandard:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if nonstandard_match:
        result["isNonstandard"] = nonstandard_match.group(1)

    return result


def load_items_from_ts(ts_path: str) -> int:
    """Load item data from a TypeScript items file."""
    path = Path(ts_path)
    if not path.exists():
        raise FileNotFoundError(f"Items file not found: {ts_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    items_data = parse_ts_items(content)

    loaded_count = 0
    for key, data in items_data.items():
        # Note: parse_ts_items already filters entries without num
        item_num = data.get("num")

        name = data.get("name", key.capitalize())
        description = data.get("shortDesc", data.get("desc", ""))

        fling_data = data.get("fling", {})
        fling_power = fling_data.get("basePower", 0) if isinstance(fling_data, dict) else 0

        flags = _parse_item_flags(data)

        type_boost = None
        boost_amount = 1.0

        on_plate = data.get("onPlate")
        if on_plate:
            type_boost = _parse_type(on_plate)
            boost_amount = 1.2

        on_drive = data.get("onDrive")
        if on_drive:
            type_boost = _parse_type(on_drive)
            boost_amount = 1.0

        item = ItemData(
            id=item_num,
            name=name,
            description=description if description else "",
            fling_power=fling_power if fling_power else 0,
            flags=flags,
            type_boost=type_boost,
            boost_amount=boost_amount,
        )

        register_item(item)
        loaded_count += 1

    return loaded_count


def load_default_items() -> int:
    """Load items from the default location."""
    module_dir = Path(__file__).parent
    possible_paths = [
        module_dir / "raw" / "items_data.ts",
        module_dir.parent / "doc" / "items_data.ts",
    ]

    for path in possible_paths:
        if path.exists():
            return load_items_from_ts(str(path))

    raise FileNotFoundError(
        "Could not find items_data.ts. Looked in: " +
        ", ".join(str(p) for p in possible_paths)
    )


def ensure_items_loaded() -> None:
    """Ensure item data is loaded."""
    if len(ITEM_REGISTRY) <= 11:
        try:
            load_default_items()
        except FileNotFoundError:
            pass


def _auto_load_items() -> None:
    """Automatically load item data.

    Only loads if registry has minimal entries (just the placeholder).
    This prevents overwriting hardcoded items when the module is imported.
    """
    # Only auto-load if registry is essentially empty (just "No Item" placeholder)
    # The <= 1 threshold ensures we don't overwrite the hardcoded common items
    if len(ITEM_REGISTRY) <= 1:
        try:
            load_default_items()
        except (FileNotFoundError, Exception):
            pass


# Don't auto-load on import - let the main registry use hardcoded data
# and call load_default_items() explicitly if more data is needed
# _auto_load_items()
