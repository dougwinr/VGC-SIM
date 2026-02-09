"""Tests using tournament data from Limitless VGC Tournament 417.

Tournament: Special Event Auckland
Date: January 25, 2026
Format: Scarlet & Violet Regulation F
Players: 43
Source: https://limitlessvgc.com/tournaments/417

These tests use real competitive team data to verify:
- Team parsing and validation
- Battle simulation with competitive teams
- Tournament model integration
"""

import pytest

from tournament.model import Tournament, Division, Player, Team
from tournament.limitless_loader import PokemonData, TeamData


# =============================================================================
# Tournament 417 Team Data - Special Event Auckland
# =============================================================================

# 1st Place - Yoav Reuven
TEAM_1ST_YOAV_REUVEN = TeamData(
    team_id=5582,
    player_name="Yoav Reuven",
    tournament_name="Special Event Auckland",
    placement="1st Place",
    pokemon=[
        PokemonData(
            species="Zapdos-Galar",
            item="Grassy Seed",
            ability="Defiant",
            tera_type="Water",
            moves=["Acrobatics", "Thunderous Kick", "Coaching", "Protect"],
        ),
        PokemonData(
            species="Incineroar",
            item="Rocky Helmet",
            ability="Intimidate",
            tera_type="Ghost",
            moves=["Flare Blitz", "Knock Off", "Fake Out", "Parting Shot"],
        ),
        PokemonData(
            species="Rillaboom",
            item="Assault Vest",
            ability="Grassy Surge",
            tera_type="Water",
            moves=["Wood Hammer", "Grassy Glide", "Fake Out", "High Horsepower"],
        ),
        PokemonData(
            species="Ogerpon-Wellspring",
            item="Wellspring Mask",
            ability="Water Absorb",
            tera_type="Water",
            moves=["Ivy Cudgel", "Wood Hammer", "Follow Me", "Spiky Shield"],
        ),
        PokemonData(
            species="Ting-Lu",
            item="Sitrus Berry",
            ability="Vessel of Ruin",
            tera_type="Fairy",
            moves=["Stomping Tantrum", "Payback", "Tera Blast", "Protect"],
        ),
        PokemonData(
            species="Raging Bolt",
            item="Booster Energy",
            ability="Protosynthesis",
            tera_type="Fairy",
            moves=["Thunderbolt", "Dragon Pulse", "Thunderclap", "Protect"],
        ),
    ],
)

# 2nd Place - Nicholas Kan
TEAM_2ND_NICHOLAS_KAN = TeamData(
    team_id=5583,
    player_name="Nicholas Kan",
    tournament_name="Special Event Auckland",
    placement="2nd Place",
    pokemon=[
        PokemonData(
            species="Ursaluna",
            item="Flame Orb",
            ability="Guts",
            tera_type="Ghost",
            moves=["Facade", "Earthquake", "Headlong Rush", "Protect"],
        ),
        PokemonData(
            species="Cresselia",
            item="Mental Herb",
            ability="Levitate",
            tera_type="Fairy",
            moves=["Moonblast", "Helping Hand", "Lunar Blessing", "Trick Room"],
        ),
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Mystic Water",
            ability="Unseen Fist",
            tera_type="Water",
            moves=["Surging Strikes", "Aqua Jet", "Close Combat", "Protect"],
        ),
        PokemonData(
            species="Pelipper",
            item="Focus Sash",
            ability="Drizzle",
            tera_type="Ghost",
            moves=["Weather Ball", "Hurricane", "Helping Hand", "Wide Guard"],
        ),
        PokemonData(
            species="Amoonguss",
            item="Rocky Helmet",
            ability="Regenerator",
            tera_type="Water",
            moves=["Spore", "Sludge Bomb", "Rage Powder", "Protect"],
        ),
        PokemonData(
            species="Incineroar",
            item="Assault Vest",
            ability="Intimidate",
            tera_type="Grass",
            moves=["Flare Blitz", "Knock Off", "U-turn", "Fake Out"],
        ),
    ],
)

# 3rd Place - Chloe Bourke
TEAM_3RD_CHLOE_BOURKE = TeamData(
    team_id=5584,
    player_name="Chloe Bourke",
    tournament_name="Special Event Auckland",
    placement="3rd Place",
    pokemon=[
        PokemonData(
            species="Entei",
            item="Sitrus Berry",
            ability="Inner Focus",
            tera_type="Normal",
            moves=["Protect", "Sacred Fire", "Stomping Tantrum", "Extreme Speed"],
        ),
        PokemonData(
            species="Chien-Pao",
            item="Focus Sash",
            ability="Sword of Ruin",
            tera_type="Stellar",
            moves=["Protect", "Ice Spinner", "Sacred Sword", "Sucker Punch"],
        ),
        PokemonData(
            species="Flutter Mane",
            item="Booster Energy",
            ability="Protosynthesis",
            tera_type="Grass",
            moves=["Moonblast", "Icy Wind", "Taunt", "Sunny Day"],
        ),
        PokemonData(
            species="Raging Bolt",
            item="Assault Vest",
            ability="Protosynthesis",
            tera_type="Electric",
            moves=["Thunderbolt", "Thunderclap", "Draco Meteor", "Snarl"],
        ),
        PokemonData(
            species="Dragonite",
            item="Loaded Dice",
            ability="Multiscale",
            tera_type="Steel",
            moves=["Protect", "Scale Shot", "Extreme Speed", "Iron Head"],
        ),
        PokemonData(
            species="Ogerpon-Cornerstone",
            item="Cornerstone Mask",
            ability="Sturdy",
            tera_type="Rock",
            moves=["Spiky Shield", "Ivy Cudgel", "Power Whip", "Follow Me"],
        ),
    ],
)

# 4th Place - Luke Iuele
TEAM_4TH_LUKE_IUELE = TeamData(
    team_id=5585,
    player_name="Luke Iuele",
    tournament_name="Special Event Auckland",
    placement="4th Place",
    pokemon=[
        PokemonData(
            species="Tornadus",
            item="Focus Sash",
            ability="Prankster",
            tera_type="Ghost",
            moves=["Protect", "Bleakwind Storm", "Tailwind", "Icy Wind"],
        ),
        PokemonData(
            species="Gholdengo",
            item="Choice Specs",
            ability="Good as Gold",
            tera_type="Steel",
            moves=["Make It Rain", "Shadow Ball", "Trick", "Power Gem"],
        ),
        PokemonData(
            species="Regidrago",
            item="Life Orb",
            ability="Dragon's Maw",
            tera_type="Ghost",
            moves=["Dragon Energy", "Draco Meteor", "Earth Power", "Protect"],
        ),
        PokemonData(
            species="Rillaboom",
            item="Assault Vest",
            ability="Grassy Surge",
            tera_type="Fire",
            moves=["Grassy Glide", "Wood Hammer", "High Horsepower", "Fake Out"],
        ),
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Choice Scarf",
            ability="Unseen Fist",
            tera_type="Water",
            moves=["Surging Strikes", "Close Combat", "Aqua Jet", "U-turn"],
        ),
        PokemonData(
            species="Ogerpon-Hearthflame",
            item="Hearthflame Mask",
            ability="Mold Breaker",
            tera_type="Fire",
            moves=["Ivy Cudgel", "Grassy Glide", "Follow Me", "Spiky Shield"],
        ),
    ],
)

# All tournament teams
TOURNAMENT_417_TEAMS = [
    TEAM_1ST_YOAV_REUVEN,
    TEAM_2ND_NICHOLAS_KAN,
    TEAM_3RD_CHLOE_BOURKE,
    TEAM_4TH_LUKE_IUELE,
]


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def tournament_417():
    """Create tournament 417 with all team data."""
    tournament = Tournament(
        id="417",
        name="Special Event Auckland",
        metadata={
            "source": "limitlessvgc.com",
            "date": "January 25, 2026",
            "format": "Scarlet & Violet Regulation F",
            "player_count": 43,
        },
    )

    division = Division(id="main", name="Masters")
    tournament.divisions.append(division)

    for team_data in TOURNAMENT_417_TEAMS:
        player_id = team_data.player_name.lower().replace(" ", "_")
        team_id = f"team_{team_data.team_id}"

        # Convert PokemonData to dict format
        pokemon_list = []
        for poke in team_data.pokemon:
            pokemon_list.append({
                "species": poke.species,
                "item": poke.item,
                "ability": poke.ability,
                "tera_type": poke.tera_type,
                "moves": poke.moves,
            })

        team = Team(
            id=team_id,
            name=f"{team_data.player_name}'s Team",
            pokemon=pokemon_list,
            metadata={
                "limitless_team_id": team_data.team_id,
                "placement": team_data.placement,
            },
        )
        tournament.add_team(team)

        player = Player(
            id=player_id,
            name=team_data.player_name,
            team_id=team_id,
            metadata={"placement": team_data.placement},
        )
        tournament.players[player.id] = player
        division.add_player(player.id)

    return tournament


# =============================================================================
# Team Data Validation Tests
# =============================================================================

class TestTournament417TeamData:
    """Tests for tournament 417 team data structure."""

    def test_team_count(self):
        """All 4 top teams are present."""
        assert len(TOURNAMENT_417_TEAMS) == 4

    def test_all_teams_have_6_pokemon(self):
        """Each team has exactly 6 Pokemon."""
        for team in TOURNAMENT_417_TEAMS:
            assert len(team.pokemon) == 6, f"{team.player_name}'s team has {len(team.pokemon)} Pokemon"

    def test_all_pokemon_have_required_fields(self):
        """All Pokemon have species, item, ability, tera_type, and 4 moves."""
        for team in TOURNAMENT_417_TEAMS:
            for poke in team.pokemon:
                assert poke.species, f"Missing species in {team.player_name}'s team"
                assert poke.item, f"Missing item for {poke.species}"
                assert poke.ability, f"Missing ability for {poke.species}"
                assert poke.tera_type, f"Missing tera_type for {poke.species}"
                assert len(poke.moves) == 4, f"{poke.species} has {len(poke.moves)} moves"

    def test_first_place_team_structure(self):
        """1st place team (Yoav Reuven) has correct Pokemon."""
        team = TEAM_1ST_YOAV_REUVEN
        species = [p.species for p in team.pokemon]

        assert "Zapdos-Galar" in species
        assert "Incineroar" in species
        assert "Rillaboom" in species
        assert "Ogerpon-Wellspring" in species
        assert "Ting-Lu" in species
        assert "Raging Bolt" in species

    def test_second_place_has_rain_core(self):
        """2nd place team has Pelipper + water attackers (rain team)."""
        team = TEAM_2ND_NICHOLAS_KAN
        species = [p.species for p in team.pokemon]
        abilities = [p.ability for p in team.pokemon]

        assert "Pelipper" in species
        assert "Drizzle" in abilities
        assert "Urshifu-Rapid-Strike" in species

    def test_third_place_has_sun_support(self):
        """3rd place team has Sunny Day on Flutter Mane."""
        team = TEAM_3RD_CHLOE_BOURKE
        flutter_mane = next(p for p in team.pokemon if p.species == "Flutter Mane")
        assert "Sunny Day" in flutter_mane.moves

    def test_fourth_place_has_tailwind(self):
        """4th place team has Tailwind on Tornadus."""
        team = TEAM_4TH_LUKE_IUELE
        tornadus = next(p for p in team.pokemon if p.species == "Tornadus")
        assert "Tailwind" in tornadus.moves
        assert tornadus.ability == "Prankster"


# =============================================================================
# Tournament Model Integration Tests
# =============================================================================

class TestTournament417Model:
    """Tests for tournament 417 model integration."""

    def test_tournament_created(self, tournament_417):
        """Tournament is created with correct metadata."""
        assert tournament_417.id == "417"
        assert tournament_417.name == "Special Event Auckland"
        assert tournament_417.metadata["format"] == "Scarlet & Violet Regulation F"

    def test_all_players_registered(self, tournament_417):
        """All 4 players are registered."""
        assert len(tournament_417.players) == 4

    def test_all_teams_registered(self, tournament_417):
        """All 4 teams are registered."""
        assert len(tournament_417.teams) == 4

    def test_player_team_association(self, tournament_417):
        """Each player is associated with their team."""
        for player in tournament_417.players.values():
            team = tournament_417.get_player_team(player.id)
            assert team is not None
            assert len(team.pokemon) == 6

    def test_first_place_player(self, tournament_417):
        """1st place player data is correct."""
        player = tournament_417.players.get("yoav_reuven")
        assert player is not None
        assert player.name == "Yoav Reuven"
        assert player.metadata["placement"] == "1st Place"


# =============================================================================
# Pokemon Species Coverage Tests
# =============================================================================

class TestTournament417SpeciesCoverage:
    """Test the variety of Pokemon used in tournament 417."""

    def test_unique_species_count(self):
        """Count unique species across all teams."""
        all_species = set()
        for team in TOURNAMENT_417_TEAMS:
            for poke in team.pokemon:
                all_species.add(poke.species)

        # Tournament 417 has diverse teams
        assert len(all_species) >= 15, f"Only {len(all_species)} unique species"

    def test_common_pokemon_usage(self):
        """Incineroar and Rillaboom appear multiple times."""
        incineroar_count = sum(
            1 for team in TOURNAMENT_417_TEAMS
            for p in team.pokemon if p.species == "Incineroar"
        )
        rillaboom_count = sum(
            1 for team in TOURNAMENT_417_TEAMS
            for p in team.pokemon if p.species == "Rillaboom"
        )

        assert incineroar_count >= 2, "Incineroar is a common pick"
        assert rillaboom_count >= 2, "Rillaboom is a common pick"

    def test_ogerpon_forms(self):
        """Multiple Ogerpon forms are represented."""
        ogerpon_forms = set()
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                if "Ogerpon" in p.species:
                    ogerpon_forms.add(p.species)

        assert len(ogerpon_forms) >= 3, f"Only {len(ogerpon_forms)} Ogerpon forms"


# =============================================================================
# Item and Ability Coverage Tests
# =============================================================================

class TestTournament417ItemsAbilities:
    """Test item and ability variety in tournament 417."""

    def test_common_items(self):
        """Common competitive items are present."""
        all_items = set()
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                all_items.add(p.item)

        expected_items = ["Assault Vest", "Focus Sash", "Choice Specs", "Life Orb"]
        for item in expected_items:
            assert item in all_items, f"Expected {item} in tournament"

    def test_intimidate_usage(self):
        """Intimidate is a common ability."""
        intimidate_count = sum(
            1 for team in TOURNAMENT_417_TEAMS
            for p in team.pokemon if p.ability == "Intimidate"
        )
        assert intimidate_count >= 2

    def test_weather_setters(self):
        """Weather-setting abilities are present."""
        abilities = set()
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                abilities.add(p.ability)

        weather_abilities = {"Drizzle", "Grassy Surge"}
        found = abilities & weather_abilities
        assert len(found) >= 1, "Expected weather-setting abilities"


# =============================================================================
# Move Coverage Tests
# =============================================================================

class TestTournament417Moves:
    """Test move variety and strategy in tournament 417."""

    def test_protect_prevalence(self):
        """Protect/Spiky Shield is common in doubles."""
        protect_count = 0
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                if "Protect" in p.moves or "Spiky Shield" in p.moves:
                    protect_count += 1

        # Most Pokemon should have a protection move in doubles
        assert protect_count >= 10, "Protect is essential in VGC doubles"

    def test_fake_out_presence(self):
        """Fake Out is present on support Pokemon."""
        fake_out_users = []
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                if "Fake Out" in p.moves:
                    fake_out_users.append(p.species)

        assert len(fake_out_users) >= 3

    def test_priority_moves(self):
        """Priority moves are present."""
        priority_moves = {"Fake Out", "Extreme Speed", "Aqua Jet", "Grassy Glide",
                        "Sucker Punch", "Thunderclap"}
        found_priority = set()
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                found_priority.update(set(p.moves) & priority_moves)

        assert len(found_priority) >= 4, "Expected variety of priority moves"


# =============================================================================
# Tera Type Strategy Tests
# =============================================================================

class TestTournament417TeraTypes:
    """Test Tera type distribution and strategy."""

    def test_defensive_tera_types(self):
        """Defensive tera types are used."""
        tera_types = set()
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                tera_types.add(p.tera_type)

        # Ghost and Fairy are common defensive tera types
        assert "Ghost" in tera_types
        assert "Fairy" in tera_types

    def test_stab_tera_types(self):
        """Some Pokemon use STAB-boosting tera types."""
        # Water tera on Water-types, etc.
        stab_tera = 0
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                # Urshifu-Rapid-Strike with Water tera
                if "Urshifu" in p.species and p.tera_type == "Water":
                    stab_tera += 1
                # Raging Bolt with Electric tera
                if p.species == "Raging Bolt" and p.tera_type == "Electric":
                    stab_tera += 1

        assert stab_tera >= 1, "Expected STAB-boosting tera types"

    def test_stellar_tera_present(self):
        """Stellar tera type is used."""
        stellar_users = []
        for team in TOURNAMENT_417_TEAMS:
            for p in team.pokemon:
                if p.tera_type == "Stellar":
                    stellar_users.append(p.species)

        assert len(stellar_users) >= 1, "Stellar tera should be used"


# =============================================================================
# Battle Simulation Tests
# =============================================================================

class TestTournament417BattleSimulation:
    """Tests that simulate battles between tournament 417 teams.

    Note: These tests require species name -> ID resolution to be implemented.
    Currently skipped because tournament teams use string species names
    while the battle simulator expects integer species IDs.
    """

    @pytest.fixture
    def tournament_teams(self, tournament_417):
        """Get teams from tournament 417."""
        return list(tournament_417.teams.values())

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_finals_matchup(self, tournament_417):
        """Simulate the finals matchup (1st vs 2nd place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        team1 = tournament_417.get_team("team_5582")  # 1st place
        team2 = tournament_417.get_team("team_5583")  # 2nd place

        assert team1 is not None
        assert team2 is not None

        # Create a match
        match = Match(
            id="finals",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="yoav_reuven",
            player2_id="nicholas_kan",
            best_of=3,
        )

        regulation = Regulation(
            name="Reg F",
            game_type="doubles",
            team_size=6,
        )

        # Simulate the match
        config = TournamentConfig(verbose=False)
        result = simulate_match(
            match,
            tournament_417,
            regulation,
            config.__dict__,
            base_seed=42,
        )

        assert result.completed
        assert result.winner_id in ["yoav_reuven", "nicholas_kan"]

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_semifinal_matchup(self, tournament_417):
        """Simulate semifinal matchup (3rd vs 4th place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        team3 = tournament_417.get_team("team_5584")  # 3rd place
        team4 = tournament_417.get_team("team_5585")  # 4th place

        assert team3 is not None
        assert team4 is not None

        match = Match(
            id="semifinal",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="chloe_bourke",
            player2_id="luke_iuele",
            best_of=3,
        )

        regulation = Regulation(
            name="Reg F",
            game_type="doubles",
            team_size=6,
        )

        config = TournamentConfig(verbose=False)
        result = simulate_match(
            match,
            tournament_417,
            regulation,
            config.__dict__,
            base_seed=123,
        )

        assert result.completed
        assert result.winner_id in ["chloe_bourke", "luke_iuele"]

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_tournament_simulation_deterministic(self, tournament_417):
        """Same seed produces same tournament result."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        def run_match(seed):
            match = Match(
                id="test",
                round_number=1,
                phase=TournamentPhase.SWISS,
                player1_id="yoav_reuven",
                player2_id="nicholas_kan",
                best_of=3,
            )

            regulation = Regulation(
                name="Reg F",
                game_type="doubles",
                team_size=6,
            )

            config = TournamentConfig(verbose=False)
            result = simulate_match(
                match,
                tournament_417,
                regulation,
                config.__dict__,
                base_seed=seed,
            )
            return (result.winner_id, result.p1_wins, result.p2_wins)

        result1 = run_match(42)
        result2 = run_match(42)

        assert result1 == result2, "Same seed should produce same result"


# =============================================================================
# Team Composition Analysis Tests
# =============================================================================

class TestTournament417TeamComposition:
    """Analyze team compositions from tournament 417."""

    def test_team_archetypes(self):
        """Identify team archetypes based on composition."""
        archetypes = {}

        for team in TOURNAMENT_417_TEAMS:
            abilities = [p.ability for p in team.pokemon]
            moves_flat = [m for p in team.pokemon for m in p.moves]

            # Check for rain team (Drizzle)
            if "Drizzle" in abilities:
                archetypes[team.player_name] = "Rain"
            # Check for sun team (Drought or Sunny Day)
            elif "Drought" in abilities or "Sunny Day" in moves_flat:
                archetypes[team.player_name] = "Sun"
            # Check for Trick Room team
            elif "Trick Room" in moves_flat:
                archetypes[team.player_name] = "Trick Room"
            # Check for Tailwind team
            elif "Tailwind" in moves_flat:
                archetypes[team.player_name] = "Tailwind"
            # Check for Grassy Terrain team
            elif "Grassy Surge" in abilities:
                archetypes[team.player_name] = "Grassy Terrain"
            else:
                archetypes[team.player_name] = "Balanced"

        # At least 2 different archetypes
        assert len(set(archetypes.values())) >= 2

    def test_offensive_coverage(self):
        """Teams should have diverse type coverage."""
        for team in TOURNAMENT_417_TEAMS:
            move_types = set()
            for p in team.pokemon:
                for move in p.moves:
                    # Simplified type inference from move names
                    if move in ["Thunderbolt", "Thunderclap"]:
                        move_types.add("Electric")
                    elif move in ["Flare Blitz", "Sacred Fire"]:
                        move_types.add("Fire")
                    elif move in ["Ice Beam", "Ice Spinner", "Icy Wind"]:
                        move_types.add("Ice")
                    elif move in ["Earthquake", "Stomping Tantrum", "High Horsepower"]:
                        move_types.add("Ground")
                    elif move in ["Moonblast"]:
                        move_types.add("Fairy")
                    elif move in ["Draco Meteor", "Dragon Pulse", "Dragon Energy"]:
                        move_types.add("Dragon")
                    elif move in ["Shadow Ball"]:
                        move_types.add("Ghost")
                    elif move in ["Wood Hammer", "Grassy Glide", "Ivy Cudgel", "Power Whip"]:
                        move_types.add("Grass")
                    elif move in ["Surging Strikes", "Aqua Jet"]:
                        move_types.add("Water")
                    elif move in ["Close Combat", "Sacred Sword"]:
                        move_types.add("Fighting")

            # Each team should have at least 4 different type coverages
            assert len(move_types) >= 4, f"{team.player_name}'s team lacks coverage"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
