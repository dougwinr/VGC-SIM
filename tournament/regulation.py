"""Tournament regulations and team validation.

Defines rules for team composition and validates teams against regulations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from tournament.model import Team


@dataclass
class Regulation:
    """Tournament regulation rules.

    Defines constraints on team composition including species restrictions,
    level caps, item rules, and various clauses.

    Attributes:
        name: Regulation name (e.g., "VGC 2024", "OU Singles")
        game_type: Battle format ("singles" or "doubles")
        team_size: Required team size (usually 6)
        bring_size: Pokemon brought to battle (e.g., 4 for VGC)
        level_cap: Maximum Pokemon level
        min_level: Minimum Pokemon level (usually 1)
        allowed_species: Set of allowed species IDs (empty = all allowed)
        banned_species: Set of banned species IDs
        allowed_items: Set of allowed item IDs (empty = all allowed)
        banned_items: Set of banned item IDs
        item_clause: Whether each Pokemon must have a unique item
        species_clause: Whether each Pokemon must be a different species
        allow_mega: Whether Mega Evolution is allowed
        allow_zmoves: Whether Z-Moves are allowed
        allow_dynamax: Whether Dynamax is allowed
        allow_tera: Whether Terastallization is allowed
        restricted_species: Species with limited count per team
        restricted_count: Max number of restricted species per team
        metadata: Additional regulation data
    """
    name: str = "Standard"
    game_type: str = "doubles"
    team_size: int = 6
    bring_size: int = 4
    level_cap: int = 50
    min_level: int = 1
    allowed_species: Set[int] = field(default_factory=set)
    banned_species: Set[int] = field(default_factory=set)
    allowed_items: Set[int] = field(default_factory=set)
    banned_items: Set[int] = field(default_factory=set)
    item_clause: bool = True
    species_clause: bool = True
    allow_mega: bool = False
    allow_zmoves: bool = False
    allow_dynamax: bool = False
    allow_tera: bool = True
    restricted_species: Set[int] = field(default_factory=set)
    restricted_count: int = 2
    metadata: Dict[str, Any] = field(default_factory=dict)


def validate_team(team: Team, regulation: Regulation) -> List[str]:
    """Validate a team against a regulation.

    Args:
        team: Team to validate
        regulation: Regulation rules to check against

    Returns:
        List of validation error messages. Empty list means team is valid.
    """
    errors = []

    # Check team size
    if team.size != regulation.team_size:
        errors.append(
            f"Team has {team.size} Pokemon, requires {regulation.team_size}"
        )

    if not team.pokemon:
        errors.append("Team has no Pokemon data")
        return errors

    # Track species and items for clause checking
    seen_species: Set[int] = set()
    seen_items: Set[int] = set()
    restricted_count = 0

    for i, pokemon in enumerate(team.pokemon):
        pokemon_name = pokemon.get("name", f"Pokemon {i + 1}")
        species_id = pokemon.get("species_id", 0)
        item_id = pokemon.get("item_id", 0)
        level = pokemon.get("level", regulation.level_cap)

        # Check level
        if level > regulation.level_cap:
            errors.append(
                f"{pokemon_name}: Level {level} exceeds cap of {regulation.level_cap}"
            )
        if level < regulation.min_level:
            errors.append(
                f"{pokemon_name}: Level {level} below minimum of {regulation.min_level}"
            )

        # Check species restrictions
        if regulation.allowed_species and species_id not in regulation.allowed_species:
            errors.append(f"{pokemon_name}: Species not allowed in this format")

        if species_id in regulation.banned_species:
            errors.append(f"{pokemon_name}: Species is banned in this format")

        # Check restricted species count
        if species_id in regulation.restricted_species:
            restricted_count += 1

        # Species clause
        if regulation.species_clause:
            if species_id in seen_species:
                errors.append(f"{pokemon_name}: Duplicate species (Species Clause)")
            seen_species.add(species_id)

        # Check item restrictions
        if item_id > 0:
            if regulation.allowed_items and item_id not in regulation.allowed_items:
                errors.append(f"{pokemon_name}: Item not allowed in this format")

            if item_id in regulation.banned_items:
                errors.append(f"{pokemon_name}: Item is banned in this format")

            # Item clause
            if regulation.item_clause:
                if item_id in seen_items:
                    errors.append(f"{pokemon_name}: Duplicate item (Item Clause)")
                seen_items.add(item_id)

    # Check restricted species limit
    if restricted_count > regulation.restricted_count:
        errors.append(
            f"Team has {restricted_count} restricted Pokemon, "
            f"maximum is {regulation.restricted_count}"
        )

    return errors


# Pre-defined regulations
VGC_2024 = Regulation(
    name="VGC 2024 Regulation G",
    game_type="doubles",
    team_size=6,
    bring_size=4,
    level_cap=50,
    item_clause=True,
    species_clause=True,
    allow_mega=False,
    allow_zmoves=False,
    allow_dynamax=False,
    allow_tera=True,
    restricted_count=2,
)

SMOGON_OU = Regulation(
    name="Smogon OU",
    game_type="singles",
    team_size=6,
    bring_size=6,
    level_cap=100,
    item_clause=False,
    species_clause=True,
    allow_mega=True,
    allow_zmoves=False,
    allow_dynamax=False,
    allow_tera=True,
)

OPEN_DOUBLES = Regulation(
    name="Open Doubles",
    game_type="doubles",
    team_size=6,
    bring_size=4,
    level_cap=50,
    item_clause=False,
    species_clause=False,
    allow_mega=True,
    allow_zmoves=True,
    allow_dynamax=True,
    allow_tera=True,
)
