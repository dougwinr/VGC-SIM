"""Loader for Pokemon species data from Showdown TypeScript format.

This module parses the pokedex_data.ts file and creates SpeciesData objects
for all species including alternate forms.
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .types import Type, TYPE_BY_NAME
from .species import (
    BaseStats,
    EvolutionData,
    EvolutionType,
    FormData,
    FormType,
    SpeciesData,
    register_species,
    SPECIES_REGISTRY,
    SPECIES_BY_NAME,
    SPECIES_BY_DEX,
)


# Map TypeScript evoType to our EvolutionType
EVO_TYPE_MAP = {
    "levelFriendship": EvolutionType.LEVEL_FRIENDSHIP,
    "useItem": EvolutionType.USE_ITEM,
    "trade": EvolutionType.TRADE,
    "levelHold": EvolutionType.LEVEL_HOLD,
    "levelMove": EvolutionType.LEVEL_MOVE,
    "other": EvolutionType.OTHER,
}


def _parse_type(type_name: str) -> Optional[Type]:
    """Parse a type name string to Type enum."""
    if not type_name:
        return None
    normalized = type_name.lower()
    return TYPE_BY_NAME.get(normalized)


def _classify_form(forme: str, name: str, base_species: Optional[str]) -> FormType:
    """Classify a form based on its identifier and name."""
    if not forme:
        return FormType.BASE

    forme_lower = forme.lower()

    # Mega evolutions
    if forme_lower == "mega":
        return FormType.MEGA
    if forme_lower == "mega-x":
        return FormType.MEGA_X
    if forme_lower == "mega-y":
        return FormType.MEGA_Y

    # Primal
    if forme_lower == "primal":
        return FormType.PRIMAL

    # Regional variants
    if forme_lower == "alola" or "alola" in forme_lower:
        return FormType.ALOLA
    if forme_lower == "galar" or "galar" in forme_lower:
        return FormType.GALAR
    if forme_lower == "hisui" or "hisui" in forme_lower:
        return FormType.HISUI
    if forme_lower == "paldea" or "paldea" in forme_lower:
        return FormType.PALDEA

    # Gigantamax
    if forme_lower == "gmax":
        return FormType.GMAX

    # Totem
    if "totem" in forme_lower:
        return FormType.TOTEM

    return FormType.OTHER


def _parse_gender_ratio(data: Dict[str, Any]) -> Optional[float]:
    """Parse gender ratio from data dict."""
    if "gender" in data:
        gender = data["gender"]
        if gender == "N":
            return None  # Genderless
        elif gender == "F":
            return 0.0  # Female only
        elif gender == "M":
            return 1.0  # Male only

    if "genderRatio" in data:
        ratio = data["genderRatio"]
        if isinstance(ratio, dict) and "M" in ratio:
            return ratio["M"]

    return 0.5  # Default


def _parse_abilities(data: Dict[str, Any]) -> Tuple[Tuple[str, ...], Optional[str]]:
    """Parse abilities from data dict.

    Returns:
        Tuple of (regular_abilities, hidden_ability)
    """
    abilities_data = data.get("abilities", {})
    regular = []
    hidden = None

    for key, ability_name in abilities_data.items():
        if key == "H":
            hidden = ability_name
        elif key == "S":
            # Special ability (often same as another)
            continue
        else:
            regular.append(ability_name)

    return tuple(regular), hidden


def _parse_evolutions(data: Dict[str, Any]) -> Tuple[EvolutionData, ...]:
    """Parse evolution data from data dict."""
    evos = data.get("evos", [])
    if not evos:
        return ()

    evolutions = []
    for evo_target in evos:
        evo_type = EvolutionType.LEVEL
        level = data.get("evoLevel")
        item = None
        move = None
        condition = data.get("evoCondition")

        ts_evo_type = data.get("evoType")
        if ts_evo_type:
            evo_type = EVO_TYPE_MAP.get(ts_evo_type, EvolutionType.OTHER)

        if evo_type == EvolutionType.USE_ITEM or evo_type == EvolutionType.LEVEL_HOLD:
            item = data.get("evoItem")

        if evo_type == EvolutionType.LEVEL_MOVE:
            move = data.get("evoMove")

        evolutions.append(EvolutionData(
            target=evo_target,
            evo_type=evo_type,
            level=level,
            item=item,
            move=move,
            condition=condition,
        ))

    return tuple(evolutions)


def _infer_generation(dex_num: int, tags: List[str]) -> int:
    """Infer generation from Pokedex number and tags."""
    # Check tags for specific generations
    for tag in tags:
        if tag.startswith("Gen"):
            try:
                return int(tag[3:])
            except ValueError:
                pass

    # Infer from dex number
    if dex_num <= 0:
        return 0
    elif dex_num <= 151:
        return 1
    elif dex_num <= 251:
        return 2
    elif dex_num <= 386:
        return 3
    elif dex_num <= 493:
        return 4
    elif dex_num <= 649:
        return 5
    elif dex_num <= 721:
        return 6
    elif dex_num <= 809:
        return 7
    elif dex_num <= 905:
        return 8
    else:
        return 9


def _parse_tags(data: Dict[str, Any]) -> Tuple[str, ...]:
    """Parse tags from data dict."""
    tags = data.get("tags", [])
    if isinstance(tags, list):
        return tuple(tags)
    return ()


def parse_ts_pokedex(ts_content: str) -> Dict[str, Dict[str, Any]]:
    """Parse TypeScript pokedex data into a dictionary.

    This is a simplified parser that handles the Showdown TS format.

    Args:
        ts_content: The TypeScript file content

    Returns:
        Dictionary mapping species keys to their data
    """
    result = {}

    # Use regex to find each pokemon entry
    # Pattern: key: { ... }
    # We need to handle nested braces correctly

    # First, remove the export statement
    content = ts_content
    content = re.sub(r"export\s+const\s+\w+\s*:\s*[^=]+=\s*\{", "{", content)

    # Find all top-level entries using a state machine
    i = 0
    # Skip to first {
    while i < len(content) and content[i] != "{":
        i += 1
    i += 1  # Skip the opening brace

    while i < len(content):
        # Skip whitespace
        while i < len(content) and content[i] in " \t\n\r,":
            i += 1

        if i >= len(content) or content[i] == "}":
            break

        # Read the key
        key_start = i
        while i < len(content) and content[i] not in ":{}":
            i += 1

        if i >= len(content):
            break

        key = content[key_start:i].strip()

        # Skip whitespace and colon
        while i < len(content) and content[i] in " \t\n\r:":
            i += 1

        if i >= len(content) or content[i] != "{":
            continue

        # Find the matching closing brace
        brace_count = 0
        obj_start = i
        in_string = False
        string_char = None

        while i < len(content):
            char = content[i]

            if in_string:
                if char == string_char and content[i-1] != "\\":
                    in_string = False
            elif char in ('"', "'"):
                in_string = True
                string_char = char
            elif char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    break

            i += 1

        # Extract the object content
        obj_content = content[obj_start + 1:i]  # Exclude braces
        i += 1  # Move past closing brace

        # Parse the object
        try:
            obj = _parse_ts_object_simple(obj_content)
            if obj and key:
                result[key] = obj
        except Exception:
            pass

    return result


def _parse_ts_object_simple(content: str) -> Dict[str, Any]:
    """Parse a TypeScript object literal using line-by-line approach."""
    result = {}

    # Split into lines and process each
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"):
            continue

        # Remove trailing comma
        if line.endswith(","):
            line = line[:-1]

        # Find the key-value separator (first colon not in a string)
        colon_pos = -1
        in_string = False
        string_char = None
        bracket_depth = 0

        for i, char in enumerate(line):
            if in_string:
                if char == string_char and (i == 0 or line[i-1] != "\\"):
                    in_string = False
            elif char in ('"', "'"):
                in_string = True
                string_char = char
            elif char in ("{", "["):
                bracket_depth += 1
            elif char in ("}", "]"):
                bracket_depth -= 1
            elif char == ":" and bracket_depth == 0:
                colon_pos = i
                break

        if colon_pos <= 0:
            continue

        key = line[:colon_pos].strip()
        value_str = line[colon_pos + 1:].strip()

        # Parse the value
        try:
            value = _parse_ts_value(value_str)
            result[key] = value
        except Exception:
            pass

    return result


def _parse_ts_object(content: str) -> Dict[str, Any]:
    """Parse a TypeScript object literal into a Python dict."""
    result = {}
    content = content.strip()
    if not content:
        return result

    # Split by commas, respecting nested structures
    parts = []
    current = ""
    depth = 0
    in_string = False
    string_char = None

    for i, char in enumerate(content):
        if in_string:
            current += char
            if char == string_char and (i == 0 or content[i-1] != "\\"):
                in_string = False
            continue

        if char in ('"', "'"):
            in_string = True
            string_char = char
            current += char
            continue

        if char in ("{", "["):
            depth += 1
            current += char
        elif char in ("}", "]"):
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            if current.strip():
                parts.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        parts.append(current.strip())

    # Parse each key-value pair
    for part in parts:
        if ":" not in part:
            continue

        # Split at first colon
        colon_idx = part.find(":")
        key = part[:colon_idx].strip()
        value_str = part[colon_idx + 1:].strip()

        # Parse the value
        value = _parse_ts_value(value_str)
        result[key] = value

    return result


def _parse_ts_value(value_str: str) -> Any:
    """Parse a TypeScript value string into a Python value."""
    value_str = value_str.strip()

    # Handle strings
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]

    # Handle numbers
    try:
        if "." in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    # Handle booleans
    if value_str == "true":
        return True
    if value_str == "false":
        return False

    # Handle arrays
    if value_str.startswith("[") and value_str.endswith("]"):
        inner = value_str[1:-1].strip()
        if not inner:
            return []
        # Split by comma, respecting strings
        items = []
        current = ""
        in_string = False
        string_char = None
        for i, char in enumerate(inner):
            if in_string:
                current += char
                if char == string_char and (i == 0 or inner[i-1] != "\\"):
                    in_string = False
                continue
            if char in ('"', "'"):
                in_string = True
                string_char = char
                current += char
            elif char == ",":
                if current.strip():
                    items.append(_parse_ts_value(current.strip()))
                current = ""
            else:
                current += char
        if current.strip():
            items.append(_parse_ts_value(current.strip()))
        return items

    # Handle objects
    if value_str.startswith("{") and value_str.endswith("}"):
        return _parse_ts_object(value_str[1:-1])

    # Return as string if nothing else matches
    return value_str


def load_species_from_ts(ts_path: str) -> int:
    """Load species data from a TypeScript pokedex file.

    Args:
        ts_path: Path to the pokedex_data.ts file

    Returns:
        Number of species loaded
    """
    path = Path(ts_path)
    if not path.exists():
        raise FileNotFoundError(f"Pokedex file not found: {ts_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pokedex = parse_ts_pokedex(content)

    # First pass: collect all species data and assign IDs
    # IDs are assigned by sorting species keys for determinism
    species_keys = sorted(pokedex.keys())

    # We use a simple ID scheme: base species by dex number, forms get higher IDs
    # First, separate base species from forms
    base_species = []
    form_species = []

    for key in species_keys:
        data = pokedex[key]
        if "baseSpecies" in data:
            form_species.append((key, data))
        else:
            base_species.append((key, data))

    # Sort base species by dex number
    base_species.sort(key=lambda x: x[1].get("num", 0))

    # Assign IDs: base species get their dex number as ID (for common ones)
    # Forms get IDs starting from 10000
    next_form_id = 10000
    loaded_count = 0

    # Load base species
    for key, data in base_species:
        dex_num = data.get("num", 0)
        if dex_num <= 0:
            continue  # Skip invalid entries

        species = _create_species_data(key, data, dex_num, pokedex)
        if species:
            register_species(species)
            loaded_count += 1

    # Load form species
    for key, data in form_species:
        dex_num = data.get("num", 0)
        if dex_num <= 0:
            continue

        species = _create_species_data(key, data, next_form_id, pokedex)
        if species:
            register_species(species)
            loaded_count += 1
            next_form_id += 1

    return loaded_count


def _create_species_data(
    key: str,
    data: Dict[str, Any],
    species_id: int,
    all_pokedex: Dict[str, Dict[str, Any]]
) -> Optional[SpeciesData]:
    """Create a SpeciesData object from parsed data."""
    name = data.get("name", key.capitalize())
    dex_num = data.get("num", 0)

    # Parse types
    types = data.get("types", [])
    type1 = _parse_type(types[0]) if types else Type.NORMAL
    type2 = _parse_type(types[1]) if len(types) > 1 else None

    if type1 is None:
        type1 = Type.NORMAL

    # Parse base stats
    stats_data = data.get("baseStats", {})
    base_stats = BaseStats(
        hp=stats_data.get("hp", 1),
        atk=stats_data.get("atk", 1),
        defense=stats_data.get("def", 1),
        spa=stats_data.get("spa", 1),
        spd=stats_data.get("spd", 1),
        spe=stats_data.get("spe", 1),
    )

    # Parse abilities
    abilities, hidden_ability = _parse_abilities(data)

    # Parse evolution data
    evolutions = _parse_evolutions(data)

    # Parse form info
    forme = data.get("forme")
    base_forme = data.get("baseSpecies")
    form_type = _classify_form(forme, name, base_forme)

    # Parse gender
    gender_ratio = _parse_gender_ratio(data)

    # Parse tags and infer generation
    tags = _parse_tags(data)
    generation = data.get("gen", _infer_generation(dex_num, list(tags)))

    # Parse other fields
    weight = data.get("weightkg", 0.0)
    height = data.get("heightm", 0.0)
    color = data.get("color", "Gray")
    egg_groups = tuple(data.get("eggGroups", []))
    prevo = data.get("prevo")
    can_gmax = data.get("canGigantamax")

    # Check for legendary/mythical status from tags
    is_legendary = any(
        "Legendary" in tag or "legendary" in tag.lower()
        for tag in tags
    )
    is_mythical = "Mythical" in tags

    # Build other_forms for base species
    other_forms = ()
    if not base_forme:  # This is a base species
        other_formes_names = data.get("otherFormes", [])
        if other_formes_names:
            form_data_list = []
            for forme_name in other_formes_names:
                # Normalize forme name to key
                forme_key = forme_name.lower().replace("-", "").replace(" ", "")
                forme_data = all_pokedex.get(forme_key, {})
                if forme_data:
                    fd = _create_form_data(forme_data, forme_name)
                    if fd:
                        form_data_list.append(fd)
            other_forms = tuple(form_data_list)

    return SpeciesData(
        id=species_id,
        name=name,
        dex_num=dex_num,
        base_stats=base_stats,
        type1=type1,
        type2=type2,
        abilities=abilities,
        hidden_ability=hidden_ability,
        weight=weight,
        height=height,
        gender_ratio=gender_ratio,
        egg_groups=egg_groups,
        generation=generation,
        color=color,
        evolutions=evolutions,
        prevo=prevo,
        other_forms=other_forms,
        base_forme=base_forme,
        forme=forme,
        form_type=form_type,
        is_legendary=is_legendary,
        is_mythical=is_mythical,
        can_gigantamax=can_gmax,
        tags=tags,
    )


def _create_form_data(data: Dict[str, Any], name: str) -> Optional[FormData]:
    """Create a FormData object from parsed data."""
    forme = data.get("forme", "")
    if not forme:
        return None

    # Parse types
    types = data.get("types", [])
    type1 = _parse_type(types[0]) if types else None
    type2 = _parse_type(types[1]) if len(types) > 1 else None

    # Parse base stats
    stats_data = data.get("baseStats")
    base_stats = None
    if stats_data:
        base_stats = BaseStats(
            hp=stats_data.get("hp", 1),
            atk=stats_data.get("atk", 1),
            defense=stats_data.get("def", 1),
            spa=stats_data.get("spa", 1),
            spd=stats_data.get("spd", 1),
            spe=stats_data.get("spe", 1),
        )

    # Parse abilities
    abilities, hidden_ability = _parse_abilities(data)

    form_type = _classify_form(forme, name, data.get("baseSpecies"))

    is_battle_only = form_type in (FormType.MEGA, FormType.MEGA_X, FormType.MEGA_Y, FormType.GMAX)
    is_cosmetic = data.get("cosmeticFormes") is not None

    return FormData(
        name=name,
        forme=forme,
        form_type=form_type,
        base_stats=base_stats,
        type1=type1,
        type2=type2,
        abilities=abilities,
        hidden_ability=hidden_ability,
        weight=data.get("weightkg", 0.0),
        height=data.get("heightm", 0.0),
        required_item=data.get("requiredItem"),
        required_ability=data.get("requiredAbility"),
        changes_from=data.get("changesFrom"),
        is_battle_only=is_battle_only,
        is_cosmetic=is_cosmetic,
    )


def load_default_species() -> int:
    """Load species from the default location.

    Returns:
        Number of species loaded
    """
    # Try to find the pokedex file relative to this module
    module_dir = Path(__file__).parent
    possible_paths = [
        module_dir / "raw" / "pokedex_data.ts",
        module_dir.parent / "doc" / "pokedex_data.ts",
    ]

    for path in possible_paths:
        if path.exists():
            return load_species_from_ts(str(path))

    raise FileNotFoundError(
        "Could not find pokedex_data.ts. Looked in: " +
        ", ".join(str(p) for p in possible_paths)
    )


def ensure_species_loaded() -> None:
    """Ensure species data is loaded. Call this before using species registry."""
    # Check if we only have the placeholder
    if len(SPECIES_REGISTRY) <= 1:
        try:
            load_default_species()
        except FileNotFoundError:
            pass  # Will use only placeholder
