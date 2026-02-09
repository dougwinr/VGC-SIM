"""Loader for Limitless VGC tournament data.

This module provides functions to load tournament standings and team data
from limitlessvgc.com.

Usage:
    # Load tournament with all team details
    tournament = load_tournament(418)

    # Load just the standings (faster, less detail)
    tournament = load_tournament_standings(418)

    # Load a specific team
    team = load_team(5591)
"""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from tournament.model import Player, Team, Tournament, Division


# Base URL for Limitless VGC
BASE_URL = "https://limitlessvgc.com"


@dataclass
class PokemonData:
    """Detailed Pokemon data from a team."""
    species: str
    item: Optional[str] = None
    ability: Optional[str] = None
    tera_type: Optional[str] = None
    moves: List[str] = field(default_factory=list)
    nature: Optional[str] = None
    evs: Dict[str, int] = field(default_factory=dict)
    ivs: Dict[str, int] = field(default_factory=dict)


@dataclass
class TeamData:
    """Full team data from Limitless."""
    team_id: int
    player_name: str
    player_id: Optional[int] = None
    tournament_name: str = ""
    placement: str = ""
    pokemon: List[PokemonData] = field(default_factory=list)


@dataclass
class TournamentStanding:
    """A player's standing in a Limitless tournament."""
    rank: int
    name: str
    country: str = ""
    team_id: Optional[int] = None
    pokemon_names: List[str] = field(default_factory=list)


@dataclass
class TournamentInfo:
    """Tournament metadata from Limitless."""
    tournament_id: int
    name: str
    date: str = ""
    format: str = ""
    player_count: int = 0
    country: str = ""
    standings: List[TournamentStanding] = field(default_factory=list)


def _fetch_url(url: str, timeout: int = 30) -> str:
    """Fetch URL content."""
    try:
        import requests
    except ImportError:
        raise ImportError("requests is required. Install with: pip install requests")

    response = requests.get(url, timeout=timeout, headers={
        "User-Agent": "Pokemon-Sim-Tournament-Loader/1.0"
    })
    response.raise_for_status()
    return response.text


def _decode_html_entities(text: str) -> str:
    """Decode HTML entities in text."""
    import html
    return html.unescape(text)


def _parse_pokemon_name(raw_name: str) -> str:
    """Normalize Pokemon name from various formats."""
    # Handle common form variations
    name = raw_name.strip()

    # Convert URL-style names to display names
    replacements = {
        "urshifu-rapid-strike": "Urshifu-Rapid-Strike",
        "urshifu-single-strike": "Urshifu-Single-Strike",
        "zoroark-hisui": "Zoroark-Hisui",
        "ogerpon-hearthflame": "Ogerpon-Hearthflame",
        "ogerpon-wellspring": "Ogerpon-Wellspring",
        "ogerpon-cornerstone": "Ogerpon-Cornerstone",
        "flutter-mane": "Flutter Mane",
        "raging-bolt": "Raging Bolt",
        "iron-hands": "Iron Hands",
        "iron-bundle": "Iron Bundle",
        "calyrex-shadow": "Calyrex-Shadow",
        "calyrex-ice": "Calyrex-Ice",
    }

    name_lower = name.lower().replace(" ", "-")
    if name_lower in replacements:
        return replacements[name_lower]

    # Title case with hyphen handling
    return name.title()


def parse_tournament_page(html: str, tournament_id: int) -> TournamentInfo:
    """Parse tournament info and standings from HTML.

    Args:
        html: Raw HTML content
        tournament_id: Tournament ID

    Returns:
        TournamentInfo with standings
    """
    info = TournamentInfo(tournament_id=tournament_id, name="Unknown Tournament")

    # Extract tournament name from title
    # Format: "Regional Sydney – Limitless VGC" (em-dash or hyphen separator)
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if title_match:
        title = title_match.group(1).strip()
        # Split on em-dash (–), en-dash (–), or hyphen followed by "Limitless"
        name = re.split(r'\s*[–—-]\s*(?=Limitless)', title)[0]
        info.name = name.strip()
    else:
        # Fallback to h1
        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if name_match:
            info.name = name_match.group(1).strip()

    # Extract date
    date_match = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', html)
    if date_match:
        info.date = date_match.group(1)

    # Extract format
    format_match = re.search(r'(Scarlet\s*&?\s*Violet[^<]*Regulation\s*\w+)', html, re.IGNORECASE)
    if format_match:
        info.format = format_match.group(1).strip()

    # Extract player count
    count_match = re.search(r'(\d+)\s*(?:players?|participants?)', html, re.IGNORECASE)
    if count_match:
        info.player_count = int(count_match.group(1))

    # Extract country
    country_match = re.search(r'country["\s:=]+["\']?([A-Z]{2})["\']?', html, re.IGNORECASE)
    if country_match:
        info.country = country_match.group(1)

    # Extract standings - look for table rows with rank/player/team info
    # Pattern for rows in standings table
    standings_patterns = [
        # Pattern 1: table rows with rank, name, team
        r'<tr[^>]*>.*?(\d+)(?:st|nd|rd|th)?.*?'
        r'(?:href="/teams/(\d+)"[^>]*>)?.*?'
        r'class="[^"]*(?:player|name)[^"]*"[^>]*>([^<]+)<.*?'
        r'(?:country|flag)[^>]*>.*?([A-Z]{2}).*?</tr>',
    ]

    # Simpler approach: find all team links and associated data
    team_pattern = r'href="/teams/(\d+)"'
    team_ids = re.findall(team_pattern, html)

    # Find player names near team links
    player_pattern = r'<a[^>]*href="/teams/\d+"[^>]*>([^<]+)</a>'
    # Or in table cells
    row_pattern = r'<tr[^>]*>(.*?)</tr>'

    rows = re.findall(row_pattern, html, re.DOTALL)

    rank = 0
    for row in rows:
        # Check if this row has a team link
        team_match = re.search(r'href="/teams/(\d+)"', row)
        if not team_match:
            continue

        rank += 1
        team_id = int(team_match.group(1))

        # Extract player name
        name = "Unknown"
        name_patterns = [
            r'class="[^"]*(?:player|name)[^"]*"[^>]*>([^<]+)<',
            r'<td[^>]*>([A-Z][a-z]+\s+[A-Z][a-z]+)</td>',
            r'>([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)</a>',
        ]
        for np in name_patterns:
            nm = re.search(np, row)
            if nm:
                name = nm.group(1).strip()
                break

        # Extract country
        country = ""
        country_match = re.search(r'flag-icon-([a-z]{2})', row, re.IGNORECASE)
        if country_match:
            country = country_match.group(1).upper()
        else:
            country_match = re.search(r'>([A-Z]{2})<', row)
            if country_match:
                country = country_match.group(1)

        # Extract Pokemon names from sprites/images
        pokemon_names = []
        pokemon_patterns = [
            r'/sprites/[^/]+/([a-zA-Z0-9-]+)\.(?:png|gif)',
            r'alt="([^"]+)"[^>]*class="[^"]*pokemon',
            r'data-pokemon="([^"]+)"',
        ]
        for pp in pokemon_patterns:
            matches = re.findall(pp, row, re.IGNORECASE)
            if matches:
                pokemon_names = [_parse_pokemon_name(m) for m in matches[:6]]
                break

        info.standings.append(TournamentStanding(
            rank=rank,
            name=name,
            country=country,
            team_id=team_id,
            pokemon_names=pokemon_names,
        ))

    return info


def parse_team_page(html: str, team_id: int) -> TeamData:
    """Parse detailed team data from a team page.

    Args:
        html: Raw HTML content
        team_id: Team ID

    Returns:
        TeamData with full Pokemon details
    """
    team = TeamData(team_id=team_id, player_name="Unknown")

    # Extract player name from meta description
    # "Teamlist by Drew Bliss - 1st Place Regional Sydney"
    meta_match = re.search(r'Teamlist by ([^-]+)\s*-', html)
    if meta_match:
        team.player_name = meta_match.group(1).strip()
    else:
        # Fallback to h1 tag
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if h1_match:
            team.player_name = h1_match.group(1).strip()

    # Extract player ID
    player_id_match = re.search(r'/players/(\d+)', html)
    if player_id_match:
        team.player_id = int(player_id_match.group(1))

    # Extract tournament name from title or meta
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if title_match:
        title = title_match.group(1)
        # "1st Place Regional Sydney – Limitless VGC"
        tournament_match = re.search(r'(?:\d+\w+\s+Place\s+)?([^–-]+?)(?:\s*–|\s*-|\s*$)', title)
        if tournament_match:
            team.tournament_name = tournament_match.group(1).strip()

    # Extract placement
    placement_match = re.search(r'(\d+(?:st|nd|rd|th)\s*[Pp]lace)', html)
    if placement_match:
        team.placement = placement_match.group(1)

    # Parse Pokemon data using Limitless-specific structure
    # Split by <div class="pkmn" data-id="...">
    pkmn_sections = re.split(r'<div class="pkmn" data-id="', html)[1:]

    for section in pkmn_sections:
        pokemon = _parse_limitless_pokemon(section)
        if pokemon:
            team.pokemon.append(pokemon)

    return team


def _parse_limitless_pokemon(section: str) -> Optional[PokemonData]:
    """Parse a Pokemon from Limitless VGC HTML format.

    Expected format:
    urshifu-rapid-strike">
        <div class="name"><a href="...">Rapid Strike Urshifu</a></div>
        <div class="main">
            <div class="details">
                <div class="item">Mystic Water</div>
                <div class="ability">Ability: Unseen Fist</div>
                <div class="tera">Tera Type: Fire</div>
            </div>
            <ul class="moves">
                <li>Surging Strikes</li>
                ...
            </ul>
        </div>
    """
    # Extract species from data-id (at the start of section)
    species_match = re.match(r'([^"]+)"', section)
    if not species_match:
        return None

    species_id = species_match.group(1)
    species = _parse_pokemon_name(species_id)

    pokemon = PokemonData(species=species)

    # Extract display name if different
    name_match = re.search(r'<div class="name">\s*<a[^>]*>([^<]+)</a>', section)
    if name_match:
        pokemon.species = name_match.group(1).strip()

    # Extract item
    item_match = re.search(r'<div class="item">([^<]+)</div>', section)
    if item_match:
        pokemon.item = item_match.group(1).strip()

    # Extract ability
    ability_match = re.search(r'<div class="ability">(?:Ability:\s*)?([^<]+)</div>', section)
    if ability_match:
        pokemon.ability = _decode_html_entities(ability_match.group(1).strip())

    # Extract tera type
    tera_match = re.search(r'<div class="tera">(?:Tera Type:\s*)?([^<]+)</div>', section)
    if tera_match:
        pokemon.tera_type = tera_match.group(1).strip()

    # Extract moves
    moves_section = re.search(r'<ul class="moves">(.*?)</ul>', section, re.DOTALL)
    if moves_section:
        moves = re.findall(r'<li>([^<]+)</li>', moves_section.group(1))
        pokemon.moves = [m.strip() for m in moves]

    return pokemon


def _parse_pokemon_section(html: str) -> Optional[PokemonData]:
    """Parse a single Pokemon section from HTML."""
    pokemon = PokemonData(species="Unknown")

    # Species name
    species_patterns = [
        r'<h\d[^>]*>([^<]+)</h\d>',
        r'class="[^"]*pokemon-name[^"]*"[^>]*>([^<]+)<',
        r'species["\s:=]+["\']?([^"\'<>]+)["\']?',
    ]
    for pattern in species_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            pokemon.species = _parse_pokemon_name(match.group(1))
            break

    if pokemon.species == "Unknown":
        return None

    # Item
    item_patterns = [
        r'item["\s:=]+["\']?([^"\'<>]+)["\']?',
        r'@\s*([A-Za-z\s]+)',
        r'held[^>]*>([^<]+)<',
    ]
    for pattern in item_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            pokemon.item = match.group(1).strip()
            break

    # Ability
    ability_patterns = [
        r'ability["\s:=]+["\']?([^"\'<>]+)["\']?',
        r'Ability:\s*([A-Za-z\s]+)',
    ]
    for pattern in ability_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            pokemon.ability = match.group(1).strip()
            break

    # Tera Type
    tera_patterns = [
        r'tera["\s:=]+["\']?([^"\'<>]+)["\']?',
        r'Tera\s*Type:\s*([A-Za-z]+)',
        r'teraType["\s:=]+["\']?([^"\'<>]+)["\']?',
    ]
    for pattern in tera_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            pokemon.tera_type = match.group(1).strip()
            break

    # Moves
    move_patterns = [
        r'moves?["\s:=]+\[([^\]]+)\]',
        r'-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    for pattern in move_patterns:
        matches = re.findall(pattern, html)
        if matches:
            if len(matches) == 1 and ',' in matches[0]:
                pokemon.moves = [m.strip().strip('"\'') for m in matches[0].split(',')]
            else:
                pokemon.moves = [m.strip() for m in matches[:4]]
            break

    return pokemon


def _parse_pokemon_list(html: str) -> List[PokemonData]:
    """Parse Pokemon list from various HTML formats."""
    pokemon_list = []

    # Try to find JSON-like data in the HTML
    json_pattern = r'"pokemon":\s*"([^"]+)".*?"item":\s*"([^"]*)".*?"ability":\s*"([^"]*)".*?"teraType":\s*"([^"]*)".*?"moves":\s*\[([^\]]*)\]'
    matches = re.findall(json_pattern, html, re.DOTALL)

    for match in matches:
        species, item, ability, tera_type, moves_str = match
        moves = [m.strip().strip('"\'') for m in moves_str.split(',') if m.strip()]

        pokemon_list.append(PokemonData(
            species=_parse_pokemon_name(species),
            item=item if item else None,
            ability=ability if ability else None,
            tera_type=tera_type if tera_type else None,
            moves=moves,
        ))

    # Alternative: look for table rows with Pokemon data
    if not pokemon_list:
        # Pattern for Pokemon in a table
        row_pattern = r'<tr[^>]*>.*?</tr>'
        rows = re.findall(row_pattern, html, re.DOTALL)

        for row in rows:
            pokemon = _parse_pokemon_section(row)
            if pokemon and pokemon.species != "Unknown":
                pokemon_list.append(pokemon)

    return pokemon_list


def load_team(team_id: int) -> TeamData:
    """Load detailed team data from Limitless VGC.

    Args:
        team_id: The team ID (e.g., 5591)

    Returns:
        TeamData with full Pokemon details
    """
    url = f"{BASE_URL}/teams/{team_id}"
    html = _fetch_url(url)
    return parse_team_page(html, team_id)


def load_tournament_info(tournament_id: int) -> TournamentInfo:
    """Load tournament standings from Limitless VGC.

    Args:
        tournament_id: The tournament ID (e.g., 418)

    Returns:
        TournamentInfo with standings
    """
    url = f"{BASE_URL}/tournaments/{tournament_id}"
    html = _fetch_url(url)
    return parse_tournament_page(html, tournament_id)


def load_tournament(
    tournament_id: int,
    load_teams: bool = True,
    team_delay: float = 0.5,
    max_teams: Optional[int] = None,
) -> Tournament:
    """Load full tournament data from Limitless VGC.

    Args:
        tournament_id: The tournament ID
        load_teams: Whether to fetch detailed team data for each player
        team_delay: Delay between team requests (be nice to the server)
        max_teams: Maximum number of teams to load (None = all)

    Returns:
        Tournament object with players and teams
    """
    # Load tournament info
    info = load_tournament_info(tournament_id)

    tournament = Tournament(
        id=str(tournament_id),
        name=info.name,
        metadata={
            "source": "limitlessvgc.com",
            "date": info.date,
            "format": info.format,
            "player_count": info.player_count,
            "country": info.country,
        },
    )

    division = Division(
        id="main",
        name="Main",
    )
    tournament.divisions.append(division)

    # Process each standing
    teams_loaded = 0
    for standing in info.standings:
        # Create player ID
        player_id = re.sub(r'[^a-zA-Z0-9]', '_', standing.name.lower())

        # Load detailed team data if requested
        team_pokemon = []
        team_id = f"team_{player_id}"

        if load_teams and standing.team_id:
            if max_teams is None or teams_loaded < max_teams:
                try:
                    team_data = load_team(standing.team_id)
                    teams_loaded += 1

                    for poke in team_data.pokemon:
                        team_pokemon.append({
                            "species": poke.species,
                            "item": poke.item,
                            "ability": poke.ability,
                            "tera_type": poke.tera_type,
                            "moves": poke.moves,
                            "nature": poke.nature,
                            "evs": poke.evs,
                            "ivs": poke.ivs,
                        })

                    if team_delay > 0:
                        time.sleep(team_delay)

                except Exception as e:
                    print(f"Warning: Failed to load team {standing.team_id}: {e}")
                    # Fall back to basic Pokemon names
                    team_pokemon = [{"species": name} for name in standing.pokemon_names]
        else:
            # Use basic Pokemon names from standings
            team_pokemon = [{"species": name} for name in standing.pokemon_names]

        # Create team
        team = Team(
            id=team_id,
            name=f"{standing.name}'s Team",
            pokemon=team_pokemon,
            metadata={
                "limitless_team_id": standing.team_id,
                "player_rank": standing.rank,
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
                "country": standing.country,
                "limitless_team_id": standing.team_id,
            },
        )
        tournament.players[player.id] = player
        division.add_player(player.id)

        # Update standing
        div_standing = division.standings[player.id]
        div_standing.rank = standing.rank

    return tournament


def load_tournament_standings(tournament_id: int) -> Tournament:
    """Load tournament standings without detailed team data.

    This is faster than load_tournament() as it doesn't fetch individual
    team pages.

    Args:
        tournament_id: The tournament ID

    Returns:
        Tournament object with players and basic team info
    """
    return load_tournament(tournament_id, load_teams=False)


# Utility functions

def get_tournament_url(tournament_id: int) -> str:
    """Get the URL for a tournament."""
    return f"{BASE_URL}/tournaments/{tournament_id}"


def get_team_url(team_id: int) -> str:
    """Get the URL for a team."""
    return f"{BASE_URL}/teams/{team_id}"


def search_tournaments(query: str = "") -> List[Dict[str, Any]]:
    """Search for tournaments on Limitless VGC.

    Note: This requires parsing the tournaments list page.

    Args:
        query: Search query (optional)

    Returns:
        List of tournament info dicts
    """
    url = f"{BASE_URL}/tournaments/"
    if query:
        url += f"?q={query}"

    html = _fetch_url(url)

    tournaments = []

    # Find tournament links
    pattern = r'href="/tournaments/(\d+)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html)

    for tid, name in matches:
        tournaments.append({
            "id": int(tid),
            "name": name.strip(),
            "url": get_tournament_url(int(tid)),
        })

    return tournaments
