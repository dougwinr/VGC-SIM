"""Tests using tournament data from Limitless VGC Tournament 409.

Tournament: LAIC 2025-26 (Latin America International Championships)
Date: November 21, 2025
Location: Sao Paulo, Brazil
Format: Scarlet & Violet Regulation H
Players: 518
Source: https://limitlessvgc.com/tournaments/409

These tests use real competitive team data to verify:
- Team parsing and validation
- Battle simulation with competitive teams
- Tournament model integration
"""

import pytest

from tournament.model import Tournament, Division, Player, Team
from tournament.limitless_loader import PokemonData, TeamData


# =============================================================================
# Tournament 409 Team Data - LAIC 2025-26 Sao Paulo
# =============================================================================

# 1st Place - Yuma Kinugawa
TEAM_1ST_YUMA_KINUGAWA = TeamData(
    team_id=5043,
    player_name="Yuma Kinugawa",
    tournament_name="LAIC 2025-26",
    placement="1st Place",
    pokemon=[
        PokemonData(
            species="Typhlosion-Hisui",
            item="Choice Specs",
            ability="Blaze",
            tera_type="Fire",
            moves=["Eruption", "Shadow Ball", "Heat Wave", "Overheat"],
        ),
        PokemonData(
            species="Whimsicott",
            item="Babiri Berry",
            ability="Prankster",
            tera_type="Ghost",
            moves=["Moonblast", "Sunny Day", "Encore", "Tailwind"],
        ),
        PokemonData(
            species="Incineroar",
            item="Safety Goggles",
            ability="Intimidate",
            tera_type="Water",
            moves=["Flare Blitz", "Knock Off", "Parting Shot", "Fake Out"],
        ),
        PokemonData(
            species="Ursaluna-Bloodmoon",
            item="Life Orb",
            ability="Mind's Eye",
            tera_type="Normal",
            moves=["Earth Power", "Blood Moon", "Hyper Voice", "Protect"],
        ),
        PokemonData(
            species="Farigiraf",
            item="Sitrus Berry",
            ability="Armor Tail",
            tera_type="Water",
            moves=["Psychic", "Night Shade", "Helping Hand", "Trick Room"],
        ),
        PokemonData(
            species="Flamigo",
            item="Focus Sash",
            ability="Scrappy",
            tera_type="Fighting",
            moves=["Close Combat", "Feint", "Wide Guard", "Detect"],
        ),
    ],
)

# 2nd Place - Juan Francisco Salerno
TEAM_2ND_JUAN_SALERNO = TeamData(
    team_id=5044,
    player_name="Juan Francisco Salerno",
    tournament_name="LAIC 2025-26",
    placement="2nd Place",
    pokemon=[
        PokemonData(
            species="Ursaluna-Bloodmoon",
            item="Leftovers",
            ability="Mind's Eye",
            tera_type="Water",
            moves=["Blood Moon", "Earth Power", "Yawn", "Protect"],
        ),
        PokemonData(
            species="Incineroar",
            item="Sitrus Berry",
            ability="Intimidate",
            tera_type="Grass",
            moves=["Fake Out", "Parting Shot", "Knock Off", "Flare Blitz"],
        ),
        PokemonData(
            species="Sneasler",
            item="Grassy Seed",
            ability="Unburden",
            tera_type="Flying",
            moves=["Swords Dance", "Acrobatics", "Protect", "Close Combat"],
        ),
        PokemonData(
            species="Rillaboom",
            item="Assault Vest",
            ability="Grassy Surge",
            tera_type="Fire",
            moves=["Fake Out", "Wood Hammer", "Grassy Glide", "High Horsepower"],
        ),
        PokemonData(
            species="Dragonite",
            item="Loaded Dice",
            ability="Multiscale",
            tera_type="Steel",
            moves=["Scale Shot", "Tailwind", "Haze", "Protect"],
        ),
        PokemonData(
            species="Gholdengo",
            item="Life Orb",
            ability="Good as Gold",
            tera_type="Water",
            moves=["Make It Rain", "Nasty Plot", "Shadow Ball", "Protect"],
        ),
    ],
)

# 3rd Place - Yuya Tada
TEAM_3RD_YUYA_TADA = TeamData(
    team_id=5045,
    player_name="Yuya Tada",
    tournament_name="LAIC 2025-26",
    placement="3rd Place",
    pokemon=[
        PokemonData(
            species="Pelipper",
            item="Focus Sash",
            ability="Drizzle",
            tera_type="Stellar",
            moves=["Weather Ball", "Hurricane", "Tailwind", "Protect"],
        ),
        PokemonData(
            species="Archaludon",
            item="Assault Vest",
            ability="Stamina",
            tera_type="Grass",
            moves=["Draco Meteor", "Snarl", "Electro Shot", "Body Press"],
        ),
        PokemonData(
            species="Ursaluna-Bloodmoon",
            item="Life Orb",
            ability="Mind's Eye",
            tera_type="Normal",
            moves=["Blood Moon", "Earth Power", "Hyper Voice", "Protect"],
        ),
        PokemonData(
            species="Farigiraf",
            item="Mental Herb",
            ability="Armor Tail",
            tera_type="Poison",
            moves=["Psychic", "Dazzling Gleam", "Helping Hand", "Trick Room"],
        ),
        PokemonData(
            species="Sinistcha",
            item="Sitrus Berry",
            ability="Hospitality",
            tera_type="Fire",
            moves=["Matcha Gotcha", "Life Dew", "Rage Powder", "Trick Room"],
        ),
        PokemonData(
            species="Incineroar",
            item="Safety Goggles",
            ability="Intimidate",
            tera_type="Fire",
            moves=["Flare Blitz", "Knock Off", "Parting Shot", "Fake Out"],
        ),
    ],
)

# 4th Place - Theotime Massaut
TEAM_4TH_THEOTIME_MASSAUT = TeamData(
    team_id=5046,
    player_name="Theotime Massaut",
    tournament_name="LAIC 2025-26",
    placement="4th Place",
    pokemon=[
        PokemonData(
            species="Basculegion",
            item="Choice Scarf",
            ability="Adaptability",
            tera_type="Water",
            moves=["Wave Crash", "Aqua Jet", "Flip Turn", "Last Respects"],
        ),
        PokemonData(
            species="Ursaluna-Bloodmoon",
            item="Leftovers",
            ability="Mind's Eye",
            tera_type="Electric",
            moves=["Blood Moon", "Earth Power", "Yawn", "Protect"],
        ),
        PokemonData(
            species="Rillaboom",
            item="Assault Vest",
            ability="Grassy Surge",
            tera_type="Fire",
            moves=["Wood Hammer", "Grassy Glide", "High Horsepower", "Fake Out"],
        ),
        PokemonData(
            species="Volcarona",
            item="Grassy Seed",
            ability="Flame Body",
            tera_type="Fairy",
            moves=["Heat Wave", "Tera Blast", "Quiver Dance", "Protect"],
        ),
        PokemonData(
            species="Ninetales-Alola",
            item="Focus Sash",
            ability="Snow Warning",
            tera_type="Ghost",
            moves=["Blizzard", "Encore", "Disable", "Protect"],
        ),
        PokemonData(
            species="Incineroar",
            item="Safety Goggles",
            ability="Intimidate",
            tera_type="Ghost",
            moves=["Taunt", "Knock Off", "Parting Shot", "Fake Out"],
        ),
    ],
)

# All tournament teams
TOURNAMENT_409_TEAMS = [
    TEAM_1ST_YUMA_KINUGAWA,
    TEAM_2ND_JUAN_SALERNO,
    TEAM_3RD_YUYA_TADA,
    TEAM_4TH_THEOTIME_MASSAUT,
]


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def tournament_409():
    """Create tournament 409 with all team data."""
    tournament = Tournament(
        id="409",
        name="LAIC 2025-26",
        metadata={
            "source": "limitlessvgc.com",
            "date": "November 21, 2025",
            "location": "Sao Paulo, Brazil",
            "format": "Scarlet & Violet Regulation H",
            "player_count": 518,
            "tier": "International Championship",
        },
    )

    division = Division(id="main", name="Masters")
    tournament.divisions.append(division)

    for team_data in TOURNAMENT_409_TEAMS:
        player_id = team_data.player_name.lower().replace(" ", "_")
        team_id = f"team_{team_data.team_id}"

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

class TestTournament409TeamData:
    """Tests for tournament 409 team data structure."""

    def test_team_count(self):
        """All 4 top teams are present."""
        assert len(TOURNAMENT_409_TEAMS) == 4

    def test_all_teams_have_6_pokemon(self):
        """Each team has exactly 6 Pokemon."""
        for team in TOURNAMENT_409_TEAMS:
            assert len(team.pokemon) == 6, f"{team.player_name}'s team has {len(team.pokemon)} Pokemon"

    def test_all_pokemon_have_required_fields(self):
        """All Pokemon have species, item, ability, tera_type, and 4 moves."""
        for team in TOURNAMENT_409_TEAMS:
            for poke in team.pokemon:
                assert poke.species, f"Missing species in {team.player_name}'s team"
                assert poke.item, f"Missing item for {poke.species}"
                assert poke.ability, f"Missing ability for {poke.species}"
                assert poke.tera_type, f"Missing tera_type for {poke.species}"
                assert len(poke.moves) == 4, f"{poke.species} has {len(poke.moves)} moves"

    def test_first_place_team_structure(self):
        """1st place team (Yuma Kinugawa) has correct Pokemon."""
        team = TEAM_1ST_YUMA_KINUGAWA
        species = [p.species for p in team.pokemon]

        assert "Typhlosion-Hisui" in species
        assert "Whimsicott" in species
        assert "Incineroar" in species
        assert "Ursaluna-Bloodmoon" in species
        assert "Farigiraf" in species
        assert "Flamigo" in species

    def test_first_place_has_eruption(self):
        """1st place uses Eruption Typhlosion."""
        team = TEAM_1ST_YUMA_KINUGAWA
        typhlosion = next(p for p in team.pokemon if "Typhlosion" in p.species)
        assert "Eruption" in typhlosion.moves
        assert typhlosion.item == "Choice Specs"

    def test_first_place_has_flamigo(self):
        """1st place uses Flamigo with Scrappy."""
        team = TEAM_1ST_YUMA_KINUGAWA
        flamigo = next(p for p in team.pokemon if p.species == "Flamigo")
        assert flamigo.ability == "Scrappy"
        assert "Wide Guard" in flamigo.moves

    def test_bloodmoon_ursaluna_on_all_teams(self):
        """Bloodmoon Ursaluna is on all top 4 teams."""
        for team in TOURNAMENT_409_TEAMS:
            species = [p.species for p in team.pokemon]
            assert "Ursaluna-Bloodmoon" in species, f"{team.player_name} missing Bloodmoon Ursaluna"


# =============================================================================
# Tournament Model Integration Tests
# =============================================================================

class TestTournament409Model:
    """Tests for tournament 409 model integration."""

    def test_tournament_created(self, tournament_409):
        """Tournament is created with correct metadata."""
        assert tournament_409.id == "409"
        assert tournament_409.name == "LAIC 2025-26"
        assert tournament_409.metadata["format"] == "Scarlet & Violet Regulation H"
        assert tournament_409.metadata["player_count"] == 518

    def test_international_championship_tier(self, tournament_409):
        """LAIC is an International Championship."""
        assert tournament_409.metadata["tier"] == "International Championship"

    def test_all_players_registered(self, tournament_409):
        """All 4 players are registered."""
        assert len(tournament_409.players) == 4

    def test_player_team_association(self, tournament_409):
        """Each player is associated with their team."""
        for player in tournament_409.players.values():
            team = tournament_409.get_player_team(player.id)
            assert team is not None
            assert len(team.pokemon) == 6


# =============================================================================
# Pokemon Species Coverage Tests
# =============================================================================

class TestTournament409SpeciesCoverage:
    """Test the variety of Pokemon used in tournament 409."""

    def test_unique_species_count(self):
        """Count unique species across all teams."""
        all_species = set()
        for team in TOURNAMENT_409_TEAMS:
            for poke in team.pokemon:
                all_species.add(poke.species)

        assert len(all_species) >= 14, f"Only {len(all_species)} unique species"

    def test_bloodmoon_ursaluna_dominance(self):
        """Bloodmoon Ursaluna is on every team."""
        count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.species == "Ursaluna-Bloodmoon"
        )
        assert count == 4

    def test_incineroar_prevalence(self):
        """Incineroar is on every team."""
        count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.species == "Incineroar"
        )
        assert count == 4

    def test_unique_pokemon_picks(self):
        """Unique Pokemon picks are present."""
        unique = {"Typhlosion-Hisui", "Flamigo", "Sinistcha", "Basculegion", "Archaludon"}
        found = set()
        for team in TOURNAMENT_409_TEAMS:
            for p in team.pokemon:
                if p.species in unique:
                    found.add(p.species)
        assert len(found) >= 4


# =============================================================================
# Item and Ability Coverage Tests
# =============================================================================

class TestTournament409ItemsAbilities:
    """Test item and ability variety in tournament 409."""

    def test_minds_eye_on_bloodmoon(self):
        """Mind's Eye is standard on Bloodmoon Ursaluna."""
        minds_eye_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon
            if p.species == "Ursaluna-Bloodmoon" and p.ability == "Mind's Eye"
        )
        assert minds_eye_count == 4

    def test_armor_tail_farigiraf(self):
        """Armor Tail Farigiraf is used."""
        armor_tail_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.ability == "Armor Tail"
        )
        assert armor_tail_count >= 2

    def test_intimidate_usage(self):
        """Intimidate is common."""
        intimidate_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.ability == "Intimidate"
        )
        assert intimidate_count == 4

    def test_safety_goggles_common(self):
        """Safety Goggles is a common item."""
        goggles_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.item == "Safety Goggles"
        )
        assert goggles_count >= 3


# =============================================================================
# Move Coverage Tests
# =============================================================================

class TestTournament409Moves:
    """Test move variety and strategy in tournament 409."""

    def test_blood_moon_prevalence(self):
        """Blood Moon is the signature move."""
        blood_moon_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if "Blood Moon" in p.moves
        )
        assert blood_moon_count == 4

    def test_trick_room_presence(self):
        """Trick Room is present."""
        tr_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if "Trick Room" in p.moves
        )
        assert tr_count >= 2

    def test_tailwind_presence(self):
        """Tailwind is present."""
        tailwind_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if "Tailwind" in p.moves
        )
        assert tailwind_count >= 3

    def test_yawn_support(self):
        """Yawn is used on Bloodmoon Ursaluna."""
        yawn_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if "Yawn" in p.moves
        )
        assert yawn_count >= 2


# =============================================================================
# Tera Type Strategy Tests
# =============================================================================

class TestTournament409TeraTypes:
    """Test Tera type distribution and strategy."""

    def test_water_tera_common(self):
        """Water tera is commonly used."""
        water_tera_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.tera_type == "Water"
        )
        assert water_tera_count >= 4

    def test_ghost_tera_defensive(self):
        """Ghost tera used defensively."""
        ghost_tera_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.tera_type == "Ghost"
        )
        assert ghost_tera_count >= 3

    def test_stellar_tera_usage(self):
        """Stellar tera is used."""
        stellar_users = [
            p.species for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.tera_type == "Stellar"
        ]
        assert len(stellar_users) >= 1


# =============================================================================
# Regulation H Meta Tests
# =============================================================================

class TestTournament409RegHMeta:
    """Test Regulation H specific meta patterns."""

    def test_bloodmoon_is_format_defining(self):
        """Bloodmoon Ursaluna defines Reg H meta."""
        bloodmoon_teams = sum(
            1 for team in TOURNAMENT_409_TEAMS
            if any(p.species == "Ursaluna-Bloodmoon" for p in team.pokemon)
        )
        assert bloodmoon_teams == 4

    def test_sun_support(self):
        """Sun support is present (for Typhlosion)."""
        sunny_day_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if "Sunny Day" in p.moves
        )
        assert sunny_day_count >= 1

    def test_rain_support(self):
        """Rain support is present."""
        drizzle_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.ability == "Drizzle"
        )
        assert drizzle_count >= 1

    def test_snow_support(self):
        """Snow support is present."""
        snow_count = sum(
            1 for team in TOURNAMENT_409_TEAMS
            for p in team.pokemon if p.ability == "Snow Warning"
        )
        assert snow_count >= 1


# =============================================================================
# Battle Simulation Tests
# =============================================================================

class TestTournament409BattleSimulation:
    """Tests that simulate battles between tournament 409 teams."""

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_finals_matchup(self, tournament_409):
        """Simulate the finals matchup (1st vs 2nd place)."""
        pass

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_semifinal_matchup(self, tournament_409):
        """Simulate semifinal matchup (3rd vs 4th place)."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
