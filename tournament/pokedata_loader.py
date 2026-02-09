"""Loader for pokedata.ovh tournament data.

This module provides functions to load tournament standings data from
pokedata.ovh, including player names, Pokemon teams, and items.

Usage:
    # From a locally saved HTML file
    tournament = load_from_pokedata_html("tournament_page.html")

    # From manually exported JSON/CSV
    tournament = load_from_pokedata_json("standings.json")
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from tournament.model import Player, Team, Tournament, Division


@dataclass
class PokemonEntry:
    """A Pokemon entry from pokedata standings."""
    species: str
    item: Optional[str] = None
    ability: Optional[str] = None
    tera_type: Optional[str] = None
    moves: List[str] = field(default_factory=list)


@dataclass
class PlayerStanding:
    """A player's standing from pokedata."""
    rank: int
    name: str
    record: str  # e.g., "8-1-0" (W-L-T)
    country: str = ""
    pokemon: List[PokemonEntry] = field(default_factory=list)
    resistance: float = 0.0


def _parse_pokemon_from_html_row(row_html: str) -> List[PokemonEntry]:
    """Parse Pokemon from an HTML row containing Pokemon sprites/icons."""
    pokemon = []

    # Pattern for Pokemon sprite images
    # pokedata typically uses img tags with Pokemon names in alt or data attributes
    sprite_patterns = [
        r'<img[^>]*?alt=["\']([^"\']+)["\'][^>]*?>',
        r'<img[^>]*?data-pokemon=["\']([^"\']+)["\'][^>]*?>',
        r'class="pokemon-icon[^"]*"[^>]*data-name=["\']([^"\']+)["\']',
        r'/sprites/[^/]+/([a-zA-Z0-9-]+)\.(?:png|gif)',
    ]

    for pattern in sprite_patterns:
        matches = re.findall(pattern, row_html, re.IGNORECASE)
        if matches:
            for name in matches:
                # Clean up the Pokemon name
                name = name.strip().replace('-', '').replace('_', '')
                if name and name.lower() not in ('none', 'unknown', ''):
                    pokemon.append(PokemonEntry(species=name))
            break

    # Try to find items associated with Pokemon
    item_pattern = r'(?:item|held)["\s:=]+["\']?([a-zA-Z0-9\s-]+)["\']?'
    item_matches = re.findall(item_pattern, row_html, re.IGNORECASE)

    for i, item in enumerate(item_matches):
        if i < len(pokemon):
            pokemon[i].item = item.strip()

    return pokemon


def _parse_record(record_str: str) -> Tuple[int, int, int]:
    """Parse a W-L-T record string into (wins, losses, ties)."""
    parts = record_str.strip().split('-')
    if len(parts) >= 3:
        try:
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            pass
    elif len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1]), 0
        except ValueError:
            pass
    return 0, 0, 0


def parse_pokedata_html(html_content: str) -> List[PlayerStanding]:
    """Parse player standings from pokedata.ovh HTML content.

    Args:
        html_content: Raw HTML from a pokedata standings page

    Returns:
        List of PlayerStanding objects
    """
    standings = []

    # pokedata.ovh typically renders standings in a table
    # Look for table rows with player data

    # Pattern for table rows containing standings
    row_patterns = [
        r'<tr[^>]*class="[^"]*(?:standing|player|row)[^"]*"[^>]*>(.*?)</tr>',
        r'<tr[^>]*>(.*?)</tr>',
    ]

    rows = []
    for pattern in row_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if matches:
            rows = matches
            break

    for row_html in rows:
        # Extract rank
        rank_match = re.search(r'(?:rank|#|position)["\s:=]*(\d+)', row_html, re.IGNORECASE)
        if not rank_match:
            rank_match = re.search(r'<td[^>]*>\s*(\d+)\s*</td>', row_html)

        if not rank_match:
            continue

        rank = int(rank_match.group(1))

        # Extract player name
        name_patterns = [
            r'(?:player|name)["\s:=]+["\']?([^"\'<>]+)["\']?',
            r'class="[^"]*(?:player-name|name)[^"]*"[^>]*>([^<]+)<',
            r'<td[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)<',
        ]

        name = None
        for pattern in name_patterns:
            match = re.search(pattern, row_html, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                break

        if not name:
            continue

        # Extract record
        record_match = re.search(r'(\d+)-(\d+)(?:-(\d+))?', row_html)
        record = "0-0-0"
        if record_match:
            w, l = record_match.group(1), record_match.group(2)
            t = record_match.group(3) or "0"
            record = f"{w}-{l}-{t}"

        # Extract country/region
        country_match = re.search(
            r'(?:country|region|flag)["\s:=]+["\']?([A-Z]{2,3})["\']?',
            row_html, re.IGNORECASE
        )
        country = country_match.group(1) if country_match else ""

        # Extract Pokemon team
        pokemon = _parse_pokemon_from_html_row(row_html)

        # Extract resistance/tiebreaker
        resistance_match = re.search(
            r'(?:resistance|opp%|omw)["\s:=]+["\']?(\d+\.?\d*)["\']?',
            row_html, re.IGNORECASE
        )
        resistance = float(resistance_match.group(1)) if resistance_match else 0.0

        standings.append(PlayerStanding(
            rank=rank,
            name=name,
            record=record,
            country=country,
            pokemon=pokemon,
            resistance=resistance,
        ))

    return standings


def parse_pokedata_json(json_data: Dict[str, Any]) -> List[PlayerStanding]:
    """Parse player standings from pokedata.ovh JSON export.

    Args:
        json_data: JSON data from pokedata export

    Returns:
        List of PlayerStanding objects
    """
    standings = []

    # Handle different JSON structures
    players_list = None

    if isinstance(json_data, list):
        players_list = json_data
    elif isinstance(json_data, dict):
        # Try common keys
        for key in ['standings', 'players', 'data', 'results']:
            if key in json_data:
                players_list = json_data[key]
                break

        if players_list is None:
            players_list = list(json_data.values())

    if not players_list:
        return standings

    for i, player_data in enumerate(players_list):
        if not isinstance(player_data, dict):
            continue

        # Extract player info with fallback keys
        rank = player_data.get('rank', player_data.get('position', i + 1))
        name = player_data.get('name', player_data.get('player', player_data.get('username', '')))

        if not name:
            continue

        # Extract record
        record = player_data.get('record', '')
        if not record:
            wins = player_data.get('wins', player_data.get('w', 0))
            losses = player_data.get('losses', player_data.get('l', 0))
            ties = player_data.get('ties', player_data.get('t', player_data.get('draws', 0)))
            record = f"{wins}-{losses}-{ties}"

        # Extract country
        country = player_data.get('country', player_data.get('region', ''))

        # Extract Pokemon team
        pokemon = []
        team_data = player_data.get('team', player_data.get('pokemon', []))

        if isinstance(team_data, list):
            for poke in team_data:
                if isinstance(poke, str):
                    pokemon.append(PokemonEntry(species=poke))
                elif isinstance(poke, dict):
                    pokemon.append(PokemonEntry(
                        species=poke.get('species', poke.get('name', '')),
                        item=poke.get('item', poke.get('held_item')),
                        ability=poke.get('ability'),
                        tera_type=poke.get('tera_type', poke.get('teraType')),
                        moves=poke.get('moves', []),
                    ))

        # Extract resistance
        resistance = float(player_data.get('resistance', player_data.get('opp_wr', 0)))

        standings.append(PlayerStanding(
            rank=rank if isinstance(rank, int) else int(rank),
            name=name,
            record=record,
            country=country,
            pokemon=pokemon,
            resistance=resistance,
        ))

    return standings


def standings_to_tournament(
    standings: List[PlayerStanding],
    tournament_id: str,
    tournament_name: str,
    division_name: str = "masters",
) -> Tournament:
    """Convert parsed standings to a Tournament object.

    Args:
        standings: List of PlayerStanding objects
        tournament_id: ID for the tournament
        tournament_name: Name of the tournament
        division_name: Division name (masters, seniors, juniors)

    Returns:
        Tournament object with players and teams populated
    """
    tournament = Tournament(
        id=tournament_id,
        name=tournament_name,
        metadata={"source": "pokedata.ovh", "division": division_name},
    )

    division = Division(
        id=division_name,
        name=division_name.title(),
    )
    tournament.divisions.append(division)

    for standing in standings:
        # Create player ID from name (normalize)
        player_id = re.sub(r'[^a-zA-Z0-9]', '_', standing.name.lower())

        # Create team
        team_id = f"team_{player_id}"
        team_pokemon = []

        for poke in standing.pokemon:
            team_pokemon.append({
                "species": poke.species,
                "item": poke.item,
                "ability": poke.ability,
                "tera_type": poke.tera_type,
                "moves": poke.moves,
            })

        team = Team(
            id=team_id,
            name=f"{standing.name}'s Team",
            pokemon=team_pokemon,
            metadata={
                "player_rank": standing.rank,
                "player_record": standing.record,
            },
        )
        tournament.add_team(team)

        # Create player
        player = Player(
            id=player_id,
            name=standing.name,
            team_id=team_id,
            metadata={
                "rank": standing.rank,
                "record": standing.record,
                "country": standing.country,
                "resistance": standing.resistance,
            },
        )
        tournament.players[player.id] = player
        division.add_player(player.id)

        # Update standing with record
        wins, losses, ties = _parse_record(standing.record)
        div_standing = division.standings[player.id]
        div_standing.match_wins = wins
        div_standing.match_losses = losses
        div_standing.match_draws = ties
        div_standing.rank = standing.rank
        div_standing.resistance = standing.resistance

    return tournament


def load_from_pokedata_html(html_path: str) -> Tournament:
    """Load tournament data from a saved pokedata.ovh HTML file.

    Args:
        html_path: Path to saved HTML file

    Returns:
        Tournament object with loaded data
    """
    path = Path(html_path)

    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    html_content = path.read_text(encoding='utf-8')

    # Try to extract tournament info from HTML
    title_match = re.search(r'<title>([^<]+)</title>', html_content, re.IGNORECASE)
    tournament_name = title_match.group(1).strip() if title_match else "Unknown Tournament"

    # Try to extract tournament ID from filename or URL in HTML
    id_match = re.search(r'/(\d{7})/', html_content) or re.search(r'(\d{7})', path.stem)
    tournament_id = id_match.group(1) if id_match else path.stem

    # Try to extract division from path or HTML
    division = "masters"
    for div in ["masters", "seniors", "juniors"]:
        if div in str(path).lower() or div in html_content.lower():
            division = div
            break

    standings = parse_pokedata_html(html_content)

    return standings_to_tournament(
        standings,
        tournament_id=tournament_id,
        tournament_name=tournament_name,
        division_name=division,
    )


def load_from_pokedata_json(json_path: str) -> Tournament:
    """Load tournament data from a pokedata.ovh JSON export.

    Args:
        json_path: Path to JSON file

    Returns:
        Tournament object with loaded data
    """
    path = Path(json_path)

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Extract metadata from JSON if available
    tournament_name = "Unknown Tournament"
    tournament_id = path.stem
    division = "masters"

    if isinstance(json_data, dict):
        tournament_name = json_data.get('tournament', json_data.get('name', tournament_name))
        tournament_id = str(json_data.get('id', json_data.get('tournament_id', tournament_id)))
        division = json_data.get('division', division)

    standings = parse_pokedata_json(json_data)

    return standings_to_tournament(
        standings,
        tournament_id=tournament_id,
        tournament_name=tournament_name,
        division_name=division,
    )


def fetch_pokedata_raw(
    tournament_id: str,
    division: str = "masters",
    format_type: str = "VGC",
) -> Optional[Dict[str, Any]]:
    """Attempt to fetch raw data from pokedata.ovh API endpoints.

    Note: pokedata.ovh doesn't have a public API, so this tries common
    endpoint patterns that may or may not work.

    Args:
        tournament_id: Tournament ID (e.g., "0000164")
        division: Division (masters, seniors, juniors)
        format_type: Format type (VGC, TCG)

    Returns:
        Raw JSON data if found, None otherwise
    """
    try:
        import requests
    except ImportError:
        return None

    base_url = "https://pokedata.ovh"

    # Try various potential API endpoints
    endpoints = [
        f"/api/standings{format_type}/{tournament_id}/{division}",
        f"/standings{format_type}/{tournament_id}/{division}/data.json",
        f"/data/standings{format_type}/{tournament_id}/{division}.json",
        f"/backend/standings{format_type}/{tournament_id}/{division}",
    ]

    for endpoint in endpoints:
        try:
            url = urljoin(base_url, endpoint)
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            continue

    return None


# Utility functions for working with loaded data

def get_top_pokemon(tournament: Tournament, top_n: int = 10) -> List[Tuple[str, int]]:
    """Get the most used Pokemon in a tournament.

    Args:
        tournament: Tournament object
        top_n: Number of top Pokemon to return

    Returns:
        List of (pokemon_name, count) tuples sorted by usage
    """
    from collections import Counter

    pokemon_counts = Counter()

    for team in tournament.teams.values():
        for poke in team.pokemon:
            species = poke.get('species', '')
            if species:
                pokemon_counts[species] += 1

    return pokemon_counts.most_common(top_n)


def get_top_items(tournament: Tournament, top_n: int = 10) -> List[Tuple[str, int]]:
    """Get the most used items in a tournament.

    Args:
        tournament: Tournament object
        top_n: Number of top items to return

    Returns:
        List of (item_name, count) tuples sorted by usage
    """
    from collections import Counter

    item_counts = Counter()

    for team in tournament.teams.values():
        for poke in team.pokemon:
            item = poke.get('item')
            if item:
                item_counts[item] += 1

    return item_counts.most_common(top_n)


def get_pokemon_item_pairs(
    tournament: Tournament,
    pokemon_name: str,
) -> List[Tuple[str, int]]:
    """Get items commonly paired with a specific Pokemon.

    Args:
        tournament: Tournament object
        pokemon_name: Name of the Pokemon

    Returns:
        List of (item_name, count) tuples sorted by frequency
    """
    from collections import Counter

    item_counts = Counter()
    pokemon_lower = pokemon_name.lower()

    for team in tournament.teams.values():
        for poke in team.pokemon:
            species = poke.get('species', '').lower()
            if species == pokemon_lower or pokemon_lower in species:
                item = poke.get('item')
                if item:
                    item_counts[item] += 1

    return item_counts.most_common()
