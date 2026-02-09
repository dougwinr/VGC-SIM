"""Loader for Pokemon ability data from Showdown TypeScript format.

This module parses the abilities_data.ts file and creates AbilityData objects
for all abilities.
"""
import re
from pathlib import Path
from typing import Any, Dict, Optional

from .abilities import (
    AbilityData,
    AbilityFlag,
    ABILITY_REGISTRY,
    ABILITY_BY_NAME,
    register_ability,
)


def _parse_ability_flags(data: Dict[str, Any]) -> AbilityFlag:
    """Parse ability flags from data dict."""
    flags = AbilityFlag.BREAKABLE  # Default: most abilities are breakable

    # Check for specific non-breakable conditions
    if data.get("isPermanent"):
        flags = AbilityFlag.CANTSUPPRESS

    return flags


def parse_ts_abilities(ts_content: str) -> Dict[str, Dict[str, Any]]:
    """Parse TypeScript abilities data into a dictionary.

    Uses regex to find each top-level entry and extract key fields.

    Args:
        ts_content: The TypeScript file content

    Returns:
        Dictionary mapping ability keys to their data
    """
    result = {}

    # Find all top-level entries: lines starting with \t followed by identifier: {
    entry_starts = list(re.finditer(r'^\t(\w+):\s*\{', ts_content, re.MULTILINE))

    for i, match in enumerate(entry_starts):
        key = match.group(1)
        start_pos = match.start()

        # Find the end of this entry
        if i + 1 < len(entry_starts):
            end_pos = entry_starts[i + 1].start()
        else:
            end_pos = len(ts_content)

        obj_content = ts_content[start_pos:end_pos]

        # Extract key fields from the object content
        obj = _extract_ability_fields(obj_content)
        if obj and obj.get("num") is not None:
            result[key] = obj

    return result


def _extract_ability_fields(obj_content: str) -> Dict[str, Any]:
    """Extract ability fields using regex patterns."""
    result = {}

    # Extract num (at double-tab indent level)
    num_match = re.search(r'^\t\tnum:\s*(\d+)', obj_content, re.MULTILINE)
    if num_match:
        result["num"] = int(num_match.group(1))

    # Extract name
    name_match = re.search(r'^\t\tname:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1)

    # Extract rating
    rating_match = re.search(r'^\t\trating:\s*([\d.-]+)', obj_content, re.MULTILINE)
    if rating_match:
        result["rating"] = float(rating_match.group(1))

    # Extract shortDesc
    desc_match = re.search(r'^\t\tshortDesc:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if desc_match:
        result["shortDesc"] = desc_match.group(1)

    # Extract desc (full description)
    full_desc_match = re.search(r'^\t\tdesc:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if full_desc_match:
        result["desc"] = full_desc_match.group(1)

    # Extract isPermanent
    if re.search(r'^\t\tisPermanent:\s*true', obj_content, re.MULTILINE):
        result["isPermanent"] = True

    # Extract isNonstandard
    nonstandard_match = re.search(r'^\t\tisNonstandard:\s*"([^"]+)"', obj_content, re.MULTILINE)
    if nonstandard_match:
        result["isNonstandard"] = nonstandard_match.group(1)

    return result


def load_abilities_from_ts(ts_path: str) -> int:
    """Load ability data from a TypeScript abilities file.

    Args:
        ts_path: Path to the abilities_data.ts file

    Returns:
        Number of abilities loaded
    """
    path = Path(ts_path)
    if not path.exists():
        raise FileNotFoundError(f"Abilities file not found: {ts_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    abilities_data = parse_ts_abilities(content)

    loaded_count = 0
    for key, data in abilities_data.items():
        # Note: parse_ts_abilities already filters entries without num
        ability_num = data.get("num")

        name = data.get("name", key.capitalize())
        description = data.get("shortDesc", data.get("desc", ""))
        rating = data.get("rating")
        if rating is None:
            rating = 3.0

        flags = _parse_ability_flags(data)

        ability = AbilityData(
            id=ability_num,
            name=name,
            description=description if description else "",
            rating=float(rating),
            flags=flags,
        )

        register_ability(ability)
        loaded_count += 1

    return loaded_count


def load_default_abilities() -> int:
    """Load abilities from the default location."""
    module_dir = Path(__file__).parent
    possible_paths = [
        module_dir / "raw" / "abilities_data.ts",
        module_dir.parent / "doc" / "abilities_data.ts",
    ]

    for path in possible_paths:
        if path.exists():
            return load_abilities_from_ts(str(path))

    raise FileNotFoundError(
        "Could not find abilities_data.ts. Looked in: " +
        ", ".join(str(p) for p in possible_paths)
    )


def ensure_abilities_loaded() -> None:
    """Ensure ability data is loaded."""
    if len(ABILITY_REGISTRY) <= 11:
        try:
            load_default_abilities()
        except FileNotFoundError:
            pass


def _auto_load_abilities() -> None:
    """Automatically load ability data.

    Only loads if registry has minimal entries (just the placeholder).
    This prevents overwriting hardcoded abilities when the module is imported.
    """
    # Only auto-load if registry is essentially empty (just "No Ability" placeholder)
    # The <= 1 threshold ensures we don't overwrite the hardcoded common abilities
    if len(ABILITY_REGISTRY) <= 1:
        try:
            load_default_abilities()
        except (FileNotFoundError, Exception):
            pass


# Don't auto-load on import - let the main registry use hardcoded data
# and call load_default_abilities() explicitly if more data is needed
# _auto_load_abilities()
