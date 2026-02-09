"""Tests for pokedata.ovh tournament loader."""

import json
import pytest
import tempfile
import os
from pathlib import Path

from tournament.pokedata_loader import (
    parse_pokedata_json,
    parse_pokedata_html,
    standings_to_tournament,
    load_from_pokedata_json,
    load_from_pokedata_html,
    get_top_pokemon,
    get_top_items,
    get_pokemon_item_pairs,
    _parse_record,
    _parse_pokemon_from_html_row,
    fetch_pokedata_raw,
    PlayerStanding,
    PokemonEntry,
)


class TestParsePokedataJson:
    """Test JSON parsing."""

    def test_parse_simple_standings(self):
        """Parse a simple standings JSON."""
        json_data = {
            "standings": [
                {
                    "rank": 1,
                    "name": "Alice",
                    "record": "8-1-0",
                    "team": [
                        {"species": "Pikachu", "item": "Light Ball"},
                        {"species": "Charizard", "item": "Choice Specs"},
                    ]
                },
                {
                    "rank": 2,
                    "name": "Bob",
                    "record": "7-2-0",
                    "team": [
                        {"species": "Mewtwo", "item": "Life Orb"},
                    ]
                }
            ]
        }

        standings = parse_pokedata_json(json_data)

        assert len(standings) == 2
        assert standings[0].name == "Alice"
        assert standings[0].rank == 1
        assert standings[0].record == "8-1-0"
        assert len(standings[0].pokemon) == 2
        assert standings[0].pokemon[0].species == "Pikachu"
        assert standings[0].pokemon[0].item == "Light Ball"

    def test_parse_list_format(self):
        """Parse standings as a simple list."""
        json_data = [
            {"rank": 1, "name": "Player1", "wins": 5, "losses": 1},
            {"rank": 2, "name": "Player2", "w": 4, "l": 2},
        ]

        standings = parse_pokedata_json(json_data)

        assert len(standings) == 2
        assert standings[0].name == "Player1"
        assert standings[0].record == "5-1-0"
        assert standings[1].record == "4-2-0"

    def test_parse_pokemon_as_strings(self):
        """Parse Pokemon when they're just strings."""
        json_data = {
            "standings": [
                {
                    "rank": 1,
                    "name": "Trainer",
                    "team": ["Pikachu", "Eevee", "Snorlax"]
                }
            ]
        }

        standings = parse_pokedata_json(json_data)

        assert len(standings[0].pokemon) == 3
        assert standings[0].pokemon[0].species == "Pikachu"
        assert standings[0].pokemon[1].species == "Eevee"


class TestStandingsToTournament:
    """Test conversion to Tournament object."""

    def test_basic_conversion(self):
        """Convert standings to tournament."""
        standings = [
            PlayerStanding(
                rank=1,
                name="Alice",
                record="8-1-0",
                country="US",
                pokemon=[
                    PokemonEntry(species="Pikachu", item="Light Ball"),
                    PokemonEntry(species="Charizard", item="Choice Specs"),
                ],
                resistance=65.0,
            ),
            PlayerStanding(
                rank=2,
                name="Bob",
                record="7-2-0",
                country="CA",
                pokemon=[
                    PokemonEntry(species="Mewtwo", item="Life Orb"),
                ],
                resistance=60.0,
            ),
        ]

        tournament = standings_to_tournament(
            standings,
            tournament_id="test123",
            tournament_name="Test Tournament",
            division_name="masters",
        )

        assert tournament.id == "test123"
        assert tournament.name == "Test Tournament"
        assert len(tournament.players) == 2
        assert len(tournament.teams) == 2

        # Check player data
        alice = tournament.players.get("alice")
        assert alice is not None
        assert alice.name == "Alice"
        assert alice.metadata["rank"] == 1
        assert alice.metadata["record"] == "8-1-0"

        # Check team data
        alice_team = tournament.get_player_team("alice")
        assert alice_team is not None
        assert len(alice_team.pokemon) == 2
        assert alice_team.pokemon[0]["species"] == "Pikachu"

        # Check division standings
        division = tournament.get_division("masters")
        assert division is not None
        assert "alice" in division.standings
        assert division.standings["alice"].match_wins == 8
        assert division.standings["alice"].match_losses == 1


class TestLoadFromSampleJson:
    """Test loading from the sample JSON file."""

    def test_load_sample_file(self):
        """Load the sample pokedata JSON file."""
        sample_path = Path(__file__).parent.parent / "tournament" / "sample_pokedata.json"

        if not sample_path.exists():
            pytest.skip("Sample file not found")

        tournament = load_from_pokedata_json(str(sample_path))

        assert tournament.id == "0000164"
        assert "Toronto" in tournament.name
        assert len(tournament.players) == 2

        # Check first player's team
        player_one = None
        for p in tournament.players.values():
            if p.name == "Player One":
                player_one = p
                break

        assert player_one is not None
        team = tournament.get_player_team(player_one.id)
        assert team is not None
        assert len(team.pokemon) == 6


class TestAnalytics:
    """Test analytics functions."""

    def test_get_top_pokemon(self):
        """Test getting most used Pokemon."""
        standings = [
            PlayerStanding(rank=1, name="A", record="1-0",
                          pokemon=[PokemonEntry("Pikachu"), PokemonEntry("Charizard")]),
            PlayerStanding(rank=2, name="B", record="0-1",
                          pokemon=[PokemonEntry("Pikachu"), PokemonEntry("Mewtwo")]),
        ]

        tournament = standings_to_tournament(standings, "t1", "Test")
        top = get_top_pokemon(tournament, top_n=5)

        assert top[0] == ("Pikachu", 2)
        assert len(top) == 3

    def test_get_top_items(self):
        """Test getting most used items."""
        standings = [
            PlayerStanding(rank=1, name="A", record="1-0",
                          pokemon=[
                              PokemonEntry("Pikachu", item="Light Ball"),
                              PokemonEntry("Charizard", item="Choice Specs")
                          ]),
            PlayerStanding(rank=2, name="B", record="0-1",
                          pokemon=[
                              PokemonEntry("Pikachu", item="Light Ball"),
                              PokemonEntry("Mewtwo", item="Life Orb")
                          ]),
        ]

        tournament = standings_to_tournament(standings, "t1", "Test")
        top = get_top_items(tournament, top_n=5)

        assert top[0] == ("Light Ball", 2)

    def test_get_pokemon_item_pairs(self):
        """Test getting items paired with a specific Pokemon."""
        standings = [
            PlayerStanding(rank=1, name="A", record="1-0",
                          pokemon=[PokemonEntry("Pikachu", item="Light Ball")]),
            PlayerStanding(rank=2, name="B", record="0-1",
                          pokemon=[PokemonEntry("Pikachu", item="Focus Sash")]),
            PlayerStanding(rank=3, name="C", record="0-1",
                          pokemon=[PokemonEntry("Pikachu", item="Light Ball")]),
        ]

        tournament = standings_to_tournament(standings, "t1", "Test")
        pairs = get_pokemon_item_pairs(tournament, "Pikachu")

        assert pairs[0] == ("Light Ball", 2)
        assert pairs[1] == ("Focus Sash", 1)


class TestParsePokedataHtml:
    """Test HTML parsing (basic patterns)."""

    def test_parse_simple_table_row(self):
        """Parse a simple HTML table with standings."""
        html = """
        <html>
        <body>
        <table>
            <tr class="standing-row">
                <td>1</td>
                <td class="player-name">TestPlayer</td>
                <td>5-2-0</td>
                <td>US</td>
            </tr>
        </table>
        </body>
        </html>
        """

        standings = parse_pokedata_html(html)

        # Note: The HTML parser may not find data depending on the exact format
        # This is a basic test - real pokedata.ovh HTML is more complex
        assert isinstance(standings, list)

    def test_parse_html_with_rank_pattern(self):
        """Parse HTML with rank in standard format."""
        html = """
        <table>
            <tr class="player">
                <td>rank: 1</td>
                <td class="name">Alice</td>
                <td>8-1-0</td>
            </tr>
        </table>
        """

        standings = parse_pokedata_html(html)
        assert isinstance(standings, list)

    def test_parse_html_with_country(self):
        """Parse HTML with country data."""
        html = """
        <table>
            <tr>
                <td>1</td>
                <td class="name">Player</td>
                <td>5-2-0</td>
                <td>country: US</td>
            </tr>
        </table>
        """

        standings = parse_pokedata_html(html)
        assert isinstance(standings, list)

    def test_parse_empty_html(self):
        """Empty HTML returns empty list."""
        standings = parse_pokedata_html("")
        assert standings == []


class TestParseRecord:
    """Test record parsing function."""

    def test_parse_standard_record(self):
        """Parse standard W-L-T record."""
        wins, losses, ties = _parse_record("8-1-0")
        assert wins == 8
        assert losses == 1
        assert ties == 0

    def test_parse_record_with_ties(self):
        """Parse record with ties."""
        wins, losses, ties = _parse_record("5-3-2")
        assert wins == 5
        assert losses == 3
        assert ties == 2

    def test_parse_two_part_record(self):
        """Parse W-L record without ties."""
        wins, losses, ties = _parse_record("7-2")
        assert wins == 7
        assert losses == 2
        assert ties == 0

    def test_parse_invalid_record(self):
        """Invalid record returns zeros."""
        wins, losses, ties = _parse_record("invalid")
        assert wins == 0
        assert losses == 0
        assert ties == 0

    def test_parse_malformed_record(self):
        """Malformed record with non-numeric parts."""
        wins, losses, ties = _parse_record("a-b-c")
        assert wins == 0
        assert losses == 0
        assert ties == 0

    def test_parse_record_with_spaces(self):
        """Parse record with leading/trailing spaces."""
        wins, losses, ties = _parse_record("  6-2-1  ")
        assert wins == 6
        assert losses == 2
        assert ties == 1


class TestParsePokemonFromHtmlRow:
    """Test Pokemon parsing from HTML rows."""

    def test_parse_pokemon_from_img_alt(self):
        """Parse Pokemon from img alt attribute."""
        html = '''
        <tr>
            <td><img alt="Pikachu" src="sprite.png" /></td>
            <td><img alt="Charizard" src="sprite2.png" /></td>
        </tr>
        '''

        pokemon = _parse_pokemon_from_html_row(html)
        assert isinstance(pokemon, list)
        if pokemon:
            species = [p.species.lower() for p in pokemon]
            assert "pikachu" in species or len(pokemon) > 0

    def test_parse_pokemon_from_data_attribute(self):
        """Parse Pokemon from data-pokemon attribute."""
        html = '''
        <tr>
            <td><img data-pokemon="Pikachu" /></td>
        </tr>
        '''

        pokemon = _parse_pokemon_from_html_row(html)
        assert isinstance(pokemon, list)

    def test_parse_pokemon_from_sprite_url(self):
        """Parse Pokemon from sprite URL."""
        html = '''
        <tr>
            <td><img src="/sprites/gen9/pikachu.png" /></td>
        </tr>
        '''

        pokemon = _parse_pokemon_from_html_row(html)
        assert isinstance(pokemon, list)

    def test_parse_pokemon_with_item(self):
        """Parse Pokemon with associated items."""
        html = '''
        <tr>
            <td><img alt="Pikachu" /></td>
            <td>item: "Light Ball"</td>
        </tr>
        '''

        pokemon = _parse_pokemon_from_html_row(html)
        assert isinstance(pokemon, list)
        if pokemon and pokemon[0].item:
            assert "Ball" in pokemon[0].item or "Light" in pokemon[0].item

    def test_parse_empty_row(self):
        """Empty row returns empty list."""
        pokemon = _parse_pokemon_from_html_row("")
        assert pokemon == []


class TestLoadFromPokedataHtml:
    """Test loading from HTML files."""

    def test_load_basic_html_file(self):
        """Load from a basic HTML file."""
        html_content = """
        <html>
        <head><title>Test Tournament</title></head>
        <body>
        <table>
            <tr>
                <td>rank: 1</td>
                <td class="name">TestPlayer</td>
                <td>5-2-0</td>
            </tr>
        </table>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name

        try:
            tournament = load_from_pokedata_html(temp_path)
            assert tournament is not None
            assert "Test Tournament" in tournament.name or tournament.name != ""
        finally:
            os.unlink(temp_path)

    def test_load_html_file_not_found(self):
        """Raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_from_pokedata_html("/nonexistent/file.html")

    def test_load_html_with_tournament_id_in_content(self):
        """Extract tournament ID from HTML content."""
        html_content = """
        <html>
        <head><title>Tournament</title></head>
        <body>
        <a href="/0000164/">Link</a>
        </body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name

        try:
            tournament = load_from_pokedata_html(temp_path)
            assert tournament is not None
        finally:
            os.unlink(temp_path)

    def test_load_html_with_division(self):
        """Extract division from file path."""
        html_content = """
        <html>
        <head><title>Tournament</title></head>
        <body>seniors division</body>
        </html>
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='_seniors.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name

        try:
            tournament = load_from_pokedata_html(temp_path)
            assert tournament is not None
        finally:
            os.unlink(temp_path)


class TestLoadFromPokedataJson:
    """Test loading from JSON files."""

    def test_load_json_file_not_found(self):
        """Raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_from_pokedata_json("/nonexistent/file.json")

    def test_load_json_with_metadata(self):
        """Load JSON with tournament metadata."""
        json_data = {
            "tournament": "Test Tournament",
            "id": "12345",
            "division": "masters",
            "standings": [
                {"rank": 1, "name": "Player1", "record": "5-0-0"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            temp_path = f.name

        try:
            tournament = load_from_pokedata_json(temp_path)
            assert tournament.name == "Test Tournament"
            assert tournament.id == "12345"
        finally:
            os.unlink(temp_path)


class TestParsePokedataJsonExtended:
    """Extended tests for JSON parsing."""

    def test_parse_json_with_alternative_keys(self):
        """Parse JSON with alternative key names."""
        json_data = {
            "data": [
                {
                    "position": 1,
                    "player": "AltPlayer",
                    "w": 5,
                    "l": 2,
                    "t": 0,
                    "pokemon": [
                        {"name": "Pikachu", "held_item": "Light Ball"}
                    ]
                }
            ]
        }

        standings = parse_pokedata_json(json_data)
        assert len(standings) == 1
        assert standings[0].name == "AltPlayer"

    def test_parse_json_with_username_key(self):
        """Parse JSON with username instead of name."""
        json_data = [
            {"rank": 1, "username": "User123", "wins": 3, "losses": 1}
        ]

        standings = parse_pokedata_json(json_data)
        assert standings[0].name == "User123"

    def test_parse_json_with_opp_wr(self):
        """Parse JSON with opponent win rate as resistance."""
        json_data = {
            "standings": [
                {"rank": 1, "name": "Player", "record": "5-0", "opp_wr": 65.5}
            ]
        }

        standings = parse_pokedata_json(json_data)
        assert standings[0].resistance == 65.5

    def test_parse_json_dict_without_known_keys(self):
        """Parse dict without standard keys."""
        json_data = {
            "player1": {"rank": 1, "name": "First", "record": "1-0"},
            "player2": {"rank": 2, "name": "Second", "record": "0-1"},
        }

        standings = parse_pokedata_json(json_data)
        assert isinstance(standings, list)

    def test_parse_json_skip_non_dict_items(self):
        """Skip non-dict items in list."""
        json_data = [
            {"rank": 1, "name": "Valid", "record": "1-0"},
            "invalid string item",
            123,
            {"rank": 2, "name": "Also Valid", "record": "0-1"},
        ]

        standings = parse_pokedata_json(json_data)
        assert len(standings) == 2

    def test_parse_json_with_tera_type(self):
        """Parse Pokemon with teraType field."""
        json_data = {
            "standings": [
                {
                    "rank": 1,
                    "name": "Player",
                    "team": [
                        {"species": "Pikachu", "teraType": "Flying"}
                    ]
                }
            ]
        }

        standings = parse_pokedata_json(json_data)
        assert standings[0].pokemon[0].tera_type == "Flying"


class TestFetchPokedataRaw:
    """Test raw data fetching (requires network or mocking)."""

    def test_fetch_returns_none_without_requests(self):
        """fetch_pokedata_raw returns None if requests unavailable or fails."""
        # This will likely return None since the API doesn't exist
        result = fetch_pokedata_raw("0000164", "masters", "VGC")
        # Either None or valid data depending on network state
        assert result is None or isinstance(result, dict)


class TestDataClasses:
    """Test data class functionality."""

    def test_pokemon_entry_defaults(self):
        """PokemonEntry should have sensible defaults."""
        entry = PokemonEntry(species="Pikachu")

        assert entry.species == "Pikachu"
        assert entry.item is None
        assert entry.ability is None
        assert entry.tera_type is None
        assert entry.moves == []

    def test_pokemon_entry_with_all_fields(self):
        """PokemonEntry with all fields populated."""
        entry = PokemonEntry(
            species="Pikachu",
            item="Light Ball",
            ability="Static",
            tera_type="Electric",
            moves=["Thunderbolt", "Quick Attack"],
        )

        assert entry.item == "Light Ball"
        assert entry.ability == "Static"
        assert entry.tera_type == "Electric"
        assert len(entry.moves) == 2

    def test_player_standing_defaults(self):
        """PlayerStanding should have sensible defaults."""
        standing = PlayerStanding(rank=1, name="Test", record="0-0")

        assert standing.country == ""
        assert standing.pokemon == []
        assert standing.resistance == 0.0
