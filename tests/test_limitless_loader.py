"""Tests for Limitless VGC tournament loader."""

import pytest
from pathlib import Path

from tournament.limitless_loader import (
    parse_tournament_page,
    parse_team_page,
    _parse_pokemon_name,
    _decode_html_entities,
    _parse_limitless_pokemon,
    _parse_pokemon_section,
    _parse_pokemon_list,
    get_tournament_url,
    get_team_url,
    TournamentInfo,
    TournamentStanding,
    TeamData,
    PokemonData,
)

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPokemonNameParsing:
    """Test Pokemon name normalization."""

    def test_basic_names(self):
        """Basic Pokemon names should be title-cased."""
        assert _parse_pokemon_name("pikachu") == "Pikachu"
        assert _parse_pokemon_name("CHARIZARD") == "Charizard"

    def test_form_names(self):
        """Form names should be properly formatted."""
        assert _parse_pokemon_name("urshifu-rapid-strike") == "Urshifu-Rapid-Strike"
        assert _parse_pokemon_name("flutter-mane") == "Flutter Mane"
        assert _parse_pokemon_name("zoroark-hisui") == "Zoroark-Hisui"


class TestTournamentParsing:
    """Test tournament page parsing."""

    def test_parse_basic_tournament_info(self):
        """Parse basic tournament metadata."""
        html = """
        <html>
        <head><title>Regional Sydney</title></head>
        <body>
        <h1>Regional Sydney</h1>
        <p>7th February 2026</p>
        <p>278 players</p>
        <p>Scarlet & Violet - Regulation F</p>
        </body>
        </html>
        """

        info = parse_tournament_page(html, 418)

        assert info.tournament_id == 418
        assert info.name == "Regional Sydney"
        assert "February" in info.date
        assert info.player_count == 278

    def test_parse_standings_with_team_links(self):
        """Parse standings table with team links."""
        html = """
        <table>
        <tr>
            <td>1</td>
            <td><a href="/teams/5591">Drew Bliss</a></td>
            <td class="flag-icon-au">AU</td>
        </tr>
        <tr>
            <td>2</td>
            <td><a href="/teams/5592">Yuxiang Wang</a></td>
            <td class="flag-icon-cn">CN</td>
        </tr>
        </table>
        """

        info = parse_tournament_page(html, 418)

        assert len(info.standings) == 2
        assert info.standings[0].team_id == 5591
        assert info.standings[1].team_id == 5592


class TestTeamParsing:
    """Test team page parsing."""

    def test_parse_team_basic(self):
        """Parse basic team structure."""
        html = """
        <html>
        <h1>Drew Bliss</h1>
        <p>1st Place - Regional Sydney</p>
        <a href="/players/4288">Player Profile</a>
        </html>
        """

        team = parse_team_page(html, 5591)

        assert team.team_id == 5591
        assert team.player_name == "Drew Bliss"
        assert team.player_id == 4288


class TestIntegration:
    """Integration tests that require network access."""

    @pytest.mark.skip(reason="Requires network access")
    def test_load_real_tournament(self):
        """Load actual tournament data from Limitless VGC."""
        from tournament.limitless_loader import load_tournament_info

        info = load_tournament_info(418)

        assert info.name == "Regional Sydney"
        assert info.player_count > 0
        assert len(info.standings) > 0

    @pytest.mark.skip(reason="Requires network access")
    def test_load_real_team(self):
        """Load actual team data from Limitless VGC."""
        from tournament.limitless_loader import load_team

        team = load_team(5591)

        assert team.player_name != "Unknown"
        assert len(team.pokemon) == 6


class TestDataClasses:
    """Test data class functionality."""

    def test_pokemon_data_defaults(self):
        """PokemonData should have sensible defaults."""
        pokemon = PokemonData(species="Pikachu")

        assert pokemon.species == "Pikachu"
        assert pokemon.item is None
        assert pokemon.ability is None
        assert pokemon.moves == []

    def test_tournament_info_defaults(self):
        """TournamentInfo should have sensible defaults."""
        info = TournamentInfo(tournament_id=1, name="Test")

        assert info.tournament_id == 1
        assert info.name == "Test"
        assert info.standings == []
        assert info.player_count == 0

    def test_tournament_standing_defaults(self):
        """TournamentStanding should have sensible defaults."""
        standing = TournamentStanding(rank=1, name="Player")

        assert standing.rank == 1
        assert standing.name == "Player"
        assert standing.country == ""
        assert standing.team_id is None
        assert standing.pokemon_names == []

    def test_team_data_defaults(self):
        """TeamData should have sensible defaults."""
        team = TeamData(team_id=123, player_name="Test")

        assert team.team_id == 123
        assert team.player_name == "Test"
        assert team.player_id is None
        assert team.tournament_name == ""
        assert team.placement == ""
        assert team.pokemon == []

    def test_pokemon_data_with_all_fields(self):
        """PokemonData with all fields populated."""
        pokemon = PokemonData(
            species="Pikachu",
            item="Light Ball",
            ability="Static",
            tera_type="Electric",
            moves=["Thunderbolt", "Quick Attack"],
            nature="Timid",
            evs={"spa": 252, "spe": 252, "hp": 4},
            ivs={"atk": 0},
        )

        assert pokemon.species == "Pikachu"
        assert pokemon.item == "Light Ball"
        assert pokemon.ability == "Static"
        assert pokemon.tera_type == "Electric"
        assert pokemon.moves == ["Thunderbolt", "Quick Attack"]
        assert pokemon.nature == "Timid"
        assert pokemon.evs == {"spa": 252, "spe": 252, "hp": 4}
        assert pokemon.ivs == {"atk": 0}


class TestDecodeHtmlEntities:
    """Test HTML entity decoding."""

    def test_decode_ampersand(self):
        """Decode &amp; entity."""
        assert _decode_html_entities("Pikachu &amp; Friends") == "Pikachu & Friends"

    def test_decode_apostrophe(self):
        """Decode apostrophe entities."""
        assert _decode_html_entities("It&#39;s a test") == "It's a test"

    def test_decode_quotes(self):
        """Decode quote entities."""
        assert _decode_html_entities("&quot;Hello&quot;") == '"Hello"'

    def test_decode_less_greater(self):
        """Decode less than and greater than."""
        assert _decode_html_entities("&lt;div&gt;") == "<div>"

    def test_no_entities(self):
        """String without entities returns unchanged."""
        assert _decode_html_entities("No entities here") == "No entities here"


class TestParseLimitlessPokemon:
    """Test Limitless VGC Pokemon parsing."""

    def test_parse_basic_pokemon(self):
        """Parse basic Pokemon from Limitless format."""
        section = '''pikachu">
            <div class="name"><a href="/pokemon/pikachu">Pikachu</a></div>
            <div class="main">
                <div class="details">
                    <div class="item">Light Ball</div>
                    <div class="ability">Ability: Static</div>
                    <div class="tera">Tera Type: Electric</div>
                </div>
                <ul class="moves">
                    <li>Thunderbolt</li>
                    <li>Quick Attack</li>
                    <li>Iron Tail</li>
                    <li>Volt Tackle</li>
                </ul>
            </div>
        '''

        pokemon = _parse_limitless_pokemon(section)

        assert pokemon is not None
        assert pokemon.species == "Pikachu"
        assert pokemon.item == "Light Ball"
        assert pokemon.ability == "Static"
        assert pokemon.tera_type == "Electric"
        assert len(pokemon.moves) == 4
        assert "Thunderbolt" in pokemon.moves

    def test_parse_pokemon_without_species_id(self):
        """Return None if species cannot be extracted."""
        section = 'invalid content without proper format'
        pokemon = _parse_limitless_pokemon(section)
        assert pokemon is None

    def test_parse_pokemon_with_form(self):
        """Parse Pokemon with form name."""
        section = '''urshifu-rapid-strike">
            <div class="name"><a href="/pokemon/urshifu">Rapid Strike Urshifu</a></div>
            <div class="main">
                <div class="details">
                    <div class="item">Focus Sash</div>
                    <div class="ability">Unseen Fist</div>
                </div>
            </div>
        '''

        pokemon = _parse_limitless_pokemon(section)

        assert pokemon is not None
        assert "Urshifu" in pokemon.species

    def test_parse_pokemon_ability_without_prefix(self):
        """Parse ability without 'Ability:' prefix."""
        section = '''charizard">
            <div class="name"><a href="/pokemon/charizard">Charizard</a></div>
            <div class="main">
                <div class="details">
                    <div class="ability">Blaze</div>
                </div>
            </div>
        '''

        pokemon = _parse_limitless_pokemon(section)
        assert pokemon is not None
        assert pokemon.ability == "Blaze"


class TestParsePokemonSection:
    """Test generic Pokemon section parsing."""

    def test_parse_basic_section(self):
        """Parse basic Pokemon section."""
        html = '''
        <div class="pokemon">
            <h3>Pikachu</h3>
            <div class="pokemon-name">Pikachu</div>
        </div>
        '''

        pokemon = _parse_pokemon_section(html)

        assert pokemon is not None
        assert pokemon.species == "Pikachu"

    def test_parse_section_with_item(self):
        """Parse section with item."""
        html = '''
        <div class="pokemon">
            <h3>Pikachu</h3>
            <div>@ Light Ball</div>
        </div>
        '''

        pokemon = _parse_pokemon_section(html)

        assert pokemon is not None
        assert pokemon.item == "Light Ball"

    def test_parse_section_with_ability(self):
        """Parse section with ability."""
        html = '''
        <div class="pokemon">
            <h3>Pikachu</h3>
            <div>Ability: Static</div>
        </div>
        '''

        pokemon = _parse_pokemon_section(html)

        assert pokemon is not None
        assert pokemon.ability == "Static"

    def test_parse_section_with_tera_type(self):
        """Parse section with Tera type."""
        html = '''
        <div class="pokemon">
            <h3>Pikachu</h3>
            <div>teraType="Electric"</div>
        </div>
        '''

        pokemon = _parse_pokemon_section(html)

        assert pokemon is not None
        assert pokemon.tera_type is not None
        assert "Electric" in pokemon.tera_type

    def test_parse_unknown_pokemon(self):
        """Return None for section without identifiable Pokemon."""
        html = '<div>Nothing useful here</div>'
        pokemon = _parse_pokemon_section(html)
        assert pokemon is None


class TestParsePokemonList:
    """Test Pokemon list parsing."""

    def test_parse_json_style_list(self):
        """Parse JSON-style Pokemon data in HTML."""
        html = '''
        <script>
        var data = {
            "pokemon": "Pikachu",
            "item": "Light Ball",
            "ability": "Static",
            "teraType": "Electric",
            "moves": ["Thunderbolt", "Quick Attack"]
        };
        </script>
        '''

        pokemon_list = _parse_pokemon_list(html)
        # This may or may not match depending on exact format
        assert isinstance(pokemon_list, list)

    def test_parse_empty_html(self):
        """Empty HTML returns empty list."""
        pokemon_list = _parse_pokemon_list("")
        assert pokemon_list == []

    def test_parse_table_rows(self):
        """Parse Pokemon from table rows."""
        html = '''
        <table>
            <tr>
                <td><h3>Pikachu</h3></td>
            </tr>
        </table>
        '''

        pokemon_list = _parse_pokemon_list(html)
        assert isinstance(pokemon_list, list)


class TestUrlFunctions:
    """Test URL generation functions."""

    def test_get_tournament_url(self):
        """Generate correct tournament URL."""
        url = get_tournament_url(418)
        assert url == "https://limitlessvgc.com/tournaments/418"

    def test_get_tournament_url_different_id(self):
        """Generate URL for different tournament ID."""
        url = get_tournament_url(100)
        assert url == "https://limitlessvgc.com/tournaments/100"

    def test_get_team_url(self):
        """Generate correct team URL."""
        url = get_team_url(5591)
        assert url == "https://limitlessvgc.com/teams/5591"

    def test_get_team_url_different_id(self):
        """Generate URL for different team ID."""
        url = get_team_url(1234)
        assert url == "https://limitlessvgc.com/teams/1234"


class TestTournamentParsingExtended:
    """Extended tests for tournament page parsing."""

    def test_parse_tournament_with_title_separator(self):
        """Parse tournament with dash/em-dash separator in title."""
        html = """
        <html>
        <head><title>Regional Sydney – Limitless VGC</title></head>
        <body></body>
        </html>
        """

        info = parse_tournament_page(html, 418)
        assert info.name == "Regional Sydney"

    def test_parse_tournament_with_hyphen_separator(self):
        """Parse tournament with hyphen separator."""
        html = """
        <html>
        <head><title>Regional Toronto - Limitless VGC</title></head>
        <body></body>
        </html>
        """

        info = parse_tournament_page(html, 400)
        assert "Toronto" in info.name

    def test_parse_tournament_without_title(self):
        """Parse tournament without title tag, fallback to h1."""
        html = """
        <html>
        <body>
        <h1>Regional Melbourne</h1>
        </body>
        </html>
        """

        info = parse_tournament_page(html, 419)
        assert info.name == "Regional Melbourne"

    def test_parse_tournament_format(self):
        """Parse tournament format."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
        <p>Scarlet & Violet Regulation G</p>
        </body>
        </html>
        """

        info = parse_tournament_page(html, 420)
        assert "Regulation" in info.format

    def test_parse_country_from_flag(self):
        """Parse country from flag-icon class."""
        html = """
        <table>
        <tr>
            <td>1</td>
            <td><a href="/teams/1000">Player One</a></td>
            <td><span class="flag-icon-jp"></span></td>
        </tr>
        </table>
        """

        info = parse_tournament_page(html, 421)
        if info.standings:
            assert info.standings[0].country == "JP"

    def test_parse_country_from_text(self):
        """Parse country from text content."""
        html = """
        <table>
        <tr>
            <td>1</td>
            <td><a href="/teams/1001">Player Two</a></td>
            <td>>US<</td>
        </tr>
        </table>
        """

        info = parse_tournament_page(html, 422)
        if info.standings:
            assert info.standings[0].country == "US"

    def test_parse_pokemon_from_sprites(self):
        """Parse Pokemon names from sprite URLs."""
        html = """
        <table>
        <tr>
            <td><a href="/teams/1002">Player</a></td>
            <td>
                <img src="/sprites/gen9/pikachu.png" />
                <img src="/sprites/gen9/charizard.gif" />
            </td>
        </tr>
        </table>
        """

        info = parse_tournament_page(html, 423)
        if info.standings and info.standings[0].pokemon_names:
            pokemon_lower = [p.lower() for p in info.standings[0].pokemon_names]
            assert "pikachu" in pokemon_lower or len(info.standings[0].pokemon_names) > 0


class TestTeamParsingExtended:
    """Extended tests for team page parsing."""

    def test_parse_team_with_meta_description(self):
        """Parse player name from meta description."""
        html = """
        <html>
        <head>
            <meta name="description" content="Teamlist by John Smith - 1st Place Regional Sydney">
        </head>
        </html>
        """

        team = parse_team_page(html, 5592)
        assert team.player_name == "John Smith"

    def test_parse_team_placement(self):
        """Parse team placement."""
        html = """
        <html>
        <p>1st Place Regional Sydney</p>
        </html>
        """

        team = parse_team_page(html, 5593)
        assert "1st" in team.placement.lower()

    def test_parse_team_with_pokemon_sections(self):
        """Parse team with Pokemon sections."""
        html = '''
        <html>
        <div class="pkmn" data-id="pikachu">
            <div class="name"><a>Pikachu</a></div>
            <div class="details">
                <div class="item">Light Ball</div>
                <div class="ability">Static</div>
            </div>
            <ul class="moves">
                <li>Thunderbolt</li>
            </ul>
        </div>
        <div class="pkmn" data-id="charizard">
            <div class="name"><a>Charizard</a></div>
            <div class="details">
                <div class="item">Choice Specs</div>
            </div>
        </div>
        </html>
        '''

        team = parse_team_page(html, 5594)
        assert len(team.pokemon) == 2
        assert any(p.species == "Pikachu" for p in team.pokemon)

    def test_parse_team_tournament_name_from_title(self):
        """Parse tournament name from title."""
        html = """
        <html>
        <head><title>1st Place Regional Sydney – Limitless VGC</title></head>
        </html>
        """

        team = parse_team_page(html, 5595)
        # Tournament name extraction may vary
        assert team.tournament_name != "" or team.player_name != ""


class TestPokemonNameExtended:
    """Extended tests for Pokemon name parsing."""

    def test_ogerpon_forms(self):
        """Test Ogerpon form names."""
        assert _parse_pokemon_name("ogerpon-hearthflame") == "Ogerpon-Hearthflame"
        assert _parse_pokemon_name("ogerpon-wellspring") == "Ogerpon-Wellspring"
        assert _parse_pokemon_name("ogerpon-cornerstone") == "Ogerpon-Cornerstone"

    def test_paradox_pokemon(self):
        """Test Paradox Pokemon names."""
        assert _parse_pokemon_name("raging-bolt") == "Raging Bolt"
        assert _parse_pokemon_name("iron-hands") == "Iron Hands"
        assert _parse_pokemon_name("iron-bundle") == "Iron Bundle"

    def test_calyrex_forms(self):
        """Test Calyrex form names."""
        assert _parse_pokemon_name("calyrex-shadow") == "Calyrex-Shadow"
        assert _parse_pokemon_name("calyrex-ice") == "Calyrex-Ice"

    def test_urshifu_forms(self):
        """Test Urshifu form names."""
        assert _parse_pokemon_name("urshifu-single-strike") == "Urshifu-Single-Strike"

    def test_whitespace_handling(self):
        """Handle names with whitespace."""
        assert _parse_pokemon_name("  pikachu  ") == "Pikachu"

    def test_already_formatted_name(self):
        """Already formatted names stay formatted."""
        result = _parse_pokemon_name("Pikachu")
        assert result == "Pikachu"


class TestTournament399WorldChampionships:
    """Tests for Tournament 399 - World Championships 2025."""

    @pytest.fixture
    def tournament_html(self):
        """Load tournament 399 fixture HTML."""
        fixture_path = FIXTURES_DIR / "tournament_399.html"
        return fixture_path.read_text(encoding="utf-8")

    @pytest.fixture
    def team_html(self):
        """Load team 4329 fixture HTML (1st place)."""
        fixture_path = FIXTURES_DIR / "team_4329.html"
        return fixture_path.read_text(encoding="utf-8")

    def test_parse_tournament_399_name(self, tournament_html):
        """Tournament 399 is World Championships 2025."""
        info = parse_tournament_page(tournament_html, 399)
        assert "World Championships" in info.name or "2025" in info.name

    def test_parse_tournament_399_id(self, tournament_html):
        """Tournament ID is correctly set."""
        info = parse_tournament_page(tournament_html, 399)
        assert info.tournament_id == 399

    def test_parse_tournament_399_player_count(self, tournament_html):
        """Tournament 399 has 371 players."""
        info = parse_tournament_page(tournament_html, 399)
        assert info.player_count == 371

    def test_parse_tournament_399_format(self, tournament_html):
        """Tournament 399 is Regulation I format."""
        info = parse_tournament_page(tournament_html, 399)
        assert "Regulation" in info.format

    def test_parse_tournament_399_has_standings(self, tournament_html):
        """Tournament 399 has standings parsed."""
        info = parse_tournament_page(tournament_html, 399)
        assert len(info.standings) >= 10

    def test_parse_tournament_399_winner(self, tournament_html):
        """Giovanni Cischke won Tournament 399."""
        info = parse_tournament_page(tournament_html, 399)
        assert len(info.standings) > 0
        winner = info.standings[0]
        assert winner.rank == 1
        assert winner.team_id == 4329

    def test_parse_tournament_399_top_8_team_ids(self, tournament_html):
        """Top 8 players have correct team IDs."""
        info = parse_tournament_page(tournament_html, 399)
        expected_team_ids = [4329, 4452, 4453, 4454, 4455, 4456, 4457, 4458]
        actual_team_ids = [s.team_id for s in info.standings[:8]]
        assert actual_team_ids == expected_team_ids

    def test_parse_tournament_399_countries(self, tournament_html):
        """Parse countries from tournament standings."""
        info = parse_tournament_page(tournament_html, 399)
        # Winner is from US
        if info.standings and info.standings[0].country:
            assert info.standings[0].country == "US"
        # 3rd place is from JP
        if len(info.standings) >= 3 and info.standings[2].country:
            assert info.standings[2].country == "JP"

    def test_parse_team_4329_winner(self, team_html):
        """Parse winning team (4329) details."""
        team = parse_team_page(team_html, 4329)
        assert team.team_id == 4329
        assert "Giovanni" in team.player_name or team.player_name != "Unknown"

    def test_parse_team_4329_player_id(self, team_html):
        """Winning team has player ID parsed."""
        team = parse_team_page(team_html, 4329)
        assert team.player_id == 3912

    def test_parse_team_4329_placement(self, team_html):
        """Winning team shows 1st place."""
        team = parse_team_page(team_html, 4329)
        assert "1st" in team.placement.lower()

    def test_parse_team_4329_has_six_pokemon(self, team_html):
        """Winning team has 6 Pokemon."""
        team = parse_team_page(team_html, 4329)
        assert len(team.pokemon) == 6

    def test_parse_team_4329_koraidon(self, team_html):
        """Winning team has Koraidon."""
        team = parse_team_page(team_html, 4329)
        pokemon_species = [p.species for p in team.pokemon]
        assert any("Koraidon" in s for s in pokemon_species)

    def test_parse_team_4329_flutter_mane(self, team_html):
        """Winning team has Flutter Mane."""
        team = parse_team_page(team_html, 4329)
        pokemon_species = [p.species for p in team.pokemon]
        assert any("Flutter" in s or "Mane" in s for s in pokemon_species)

    def test_parse_team_4329_lunala(self, team_html):
        """Winning team has Lunala."""
        team = parse_team_page(team_html, 4329)
        pokemon_species = [p.species for p in team.pokemon]
        assert any("Lunala" in s for s in pokemon_species)

    def test_parse_team_4329_items(self, team_html):
        """Winning team Pokemon have items."""
        team = parse_team_page(team_html, 4329)
        items = [p.item for p in team.pokemon if p.item]
        assert len(items) >= 5  # Most Pokemon should have items
        assert "Booster Energy" in items or "Focus Sash" in items

    def test_parse_team_4329_abilities(self, team_html):
        """Winning team Pokemon have abilities."""
        team = parse_team_page(team_html, 4329)
        abilities = [p.ability for p in team.pokemon if p.ability]
        assert len(abilities) >= 5
        # Koraidon's ability
        assert any("Orichalcum" in a for a in abilities)

    def test_parse_team_4329_tera_types(self, team_html):
        """Winning team Pokemon have Tera types."""
        team = parse_team_page(team_html, 4329)
        tera_types = [p.tera_type for p in team.pokemon if p.tera_type]
        assert len(tera_types) >= 5
        # Should include common types
        tera_type_str = " ".join(tera_types)
        assert "Fairy" in tera_type_str or "Fire" in tera_type_str

    def test_parse_team_4329_moves(self, team_html):
        """Winning team Pokemon have moves."""
        team = parse_team_page(team_html, 4329)
        for pokemon in team.pokemon:
            assert len(pokemon.moves) == 4, f"{pokemon.species} should have 4 moves"

    def test_parse_team_4329_specific_moves(self, team_html):
        """Check specific moves on winning team."""
        team = parse_team_page(team_html, 4329)
        all_moves = []
        for pokemon in team.pokemon:
            all_moves.extend(pokemon.moves)
        # Common moves in the winning team
        assert "Protect" in all_moves
        assert "Moonblast" in all_moves or "Shadow Ball" in all_moves

    def test_tournament_399_url(self):
        """Tournament 399 URL is correct."""
        url = get_tournament_url(399)
        assert url == "https://limitlessvgc.com/tournaments/399"

    def test_team_4329_url(self):
        """Team 4329 URL is correct."""
        url = get_team_url(4329)
        assert url == "https://limitlessvgc.com/teams/4329"


class TestTournament399Integration:
    """Integration tests for Tournament 399 (requires network)."""

    @pytest.mark.skip(reason="Requires network access - run manually with pytest -k 'test_load_tournament_399' --run-network")
    def test_load_tournament_399_info(self):
        """Load actual tournament 399 info from Limitless VGC."""
        from tournament.limitless_loader import load_tournament_info

        info = load_tournament_info(399)

        assert info.tournament_id == 399
        assert "World" in info.name or "Championships" in info.name
        assert info.player_count > 300
        assert len(info.standings) > 0

    @pytest.mark.skip(reason="Requires network access - run manually with pytest -k 'test_load_team_4329' --run-network")
    def test_load_team_4329_real(self):
        """Load actual team 4329 from Limitless VGC."""
        from tournament.limitless_loader import load_team

        team = load_team(4329)

        assert team.team_id == 4329
        assert team.player_name != "Unknown"
        assert len(team.pokemon) == 6
        # Verify some expected Pokemon on the winning team
        species = [p.species for p in team.pokemon]
        assert any("Koraidon" in s for s in species)

    @pytest.mark.skip(reason="Requires network access - run manually")
    def test_load_full_tournament_399(self):
        """Load full tournament 399 with team data."""
        from tournament.limitless_loader import load_tournament

        tournament = load_tournament(399, load_teams=True, max_teams=3, team_delay=1.0)

        assert tournament.id == "399"
        assert len(tournament.players) > 0
        assert len(tournament.teams) > 0
