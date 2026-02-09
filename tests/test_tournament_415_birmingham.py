"""Tests using tournament data from Limitless VGC Tournament 415.

Tournament: Regional Birmingham
Date: January 24, 2026
Format: Scarlet & Violet Regulation F
Players: 688
Source: https://limitlessvgc.com/tournaments/415

These tests use real competitive team data to verify:
- Team parsing and validation
- Battle simulation with competitive teams
- Tournament model integration
"""

import pytest

from tournament.model import Tournament, Division, Player, Team
from tournament.limitless_loader import PokemonData, TeamData


# =============================================================================
# Tournament 415 Team Data - Regional Birmingham
# =============================================================================

# 1st Place - Stefano Greppi
TEAM_1ST_STEFANO_GREPPI = TeamData(
    team_id=5412,
    player_name="Stefano Greppi",
    tournament_name="Regional Birmingham",
    placement="1st Place",
    pokemon=[
        PokemonData(
            species="Landorus",
            item="Life Orb",
            ability="Sheer Force",
            tera_type="Poison",
            moves=["Earth Power", "Sludge Bomb", "Substitute", "Protect"],
        ),
        PokemonData(
            species="Chien-Pao",
            item="Focus Sash",
            ability="Sword of Ruin",
            tera_type="Ice",
            moves=["Icicle Crash", "Icy Wind", "Sucker Punch", "Protect"],
        ),
        PokemonData(
            species="Incineroar",
            item="Safety Goggles",
            ability="Intimidate",
            tera_type="Ghost",
            moves=["Taunt", "Flare Blitz", "Parting Shot", "Fake Out"],
        ),
        PokemonData(
            species="Rillaboom",
            item="Assault Vest",
            ability="Grassy Surge",
            tera_type="Fire",
            moves=["Fake Out", "Wood Hammer", "Grassy Glide", "U-turn"],
        ),
        PokemonData(
            species="Raging Bolt",
            item="Booster Energy",
            ability="Protosynthesis",
            tera_type="Fairy",
            moves=["Thunderclap", "Dragon Pulse", "Calm Mind", "Protect"],
        ),
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Mystic Water",
            ability="Unseen Fist",
            tera_type="Steel",
            moves=["Surging Strikes", "Close Combat", "Aqua Jet", "Detect"],
        ),
    ],
)

# 2nd Place - Marcus Koh
TEAM_2ND_MARCUS_KOH = TeamData(
    team_id=5413,
    player_name="Marcus Koh",
    tournament_name="Regional Birmingham",
    placement="2nd Place",
    pokemon=[
        PokemonData(
            species="Weezing-Galar",
            item="Sitrus Berry",
            ability="Neutralizing Gas",
            tera_type="Flying",
            moves=["Gunk Shot", "Poison Gas", "Toxic Spikes", "Protect"],
        ),
        PokemonData(
            species="Flutter Mane",
            item="Booster Energy",
            ability="Protosynthesis",
            tera_type="Fairy",
            moves=["Moonblast", "Icy Wind", "Taunt", "Protect"],
        ),
        PokemonData(
            species="Dondozo",
            item="Rocky Helmet",
            ability="Oblivious",
            tera_type="Grass",
            moves=["Wave Crash", "Order Up", "Earthquake", "Protect"],
        ),
        PokemonData(
            species="Tatsugiri",
            item="Safety Goggles",
            ability="Commander",
            tera_type="Steel",
            moves=["Draco Meteor", "Muddy Water", "Helping Hand", "Protect"],
        ),
        PokemonData(
            species="Dragonite",
            item="Choice Band",
            ability="Multiscale",
            tera_type="Normal",
            moves=["Extreme Speed", "Iron Head", "Earthquake", "Outrage"],
        ),
        PokemonData(
            species="Chi-Yu",
            item="Focus Sash",
            ability="Beads of Ruin",
            tera_type="Ghost",
            moves=["Heat Wave", "Overheat", "Dark Pulse", "Protect"],
        ),
    ],
)

# 3rd Place - Hengyue Zhang
TEAM_3RD_HENGYUE_ZHANG = TeamData(
    team_id=5414,
    player_name="Hengyue Zhang",
    tournament_name="Regional Birmingham",
    placement="3rd Place",
    pokemon=[
        PokemonData(
            species="Iron Crown",
            item="Booster Energy",
            ability="Quark Drive",
            tera_type="Water",
            moves=["Expanding Force", "Tachyon Cutter", "Tera Blast", "Protect"],
        ),
        PokemonData(
            species="Indeedee-F",
            item="Rocky Helmet",
            ability="Psychic Surge",
            tera_type="Water",
            moves=["Dazzling Gleam", "Follow Me", "Helping Hand", "Trick Room"],
        ),
        PokemonData(
            species="Regidrago",
            item="Dragon Fang",
            ability="Dragon's Maw",
            tera_type="Fairy",
            moves=["Dragon Energy", "Draco Meteor", "Earth Power", "Protect"],
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
            moves=["Ivy Cudgel", "Wood Hammer", "Follow Me", "Spiky Shield"],
        ),
        PokemonData(
            species="Tornadus",
            item="Focus Sash",
            ability="Prankster",
            tera_type="Steel",
            moves=["Bleakwind Storm", "Tailwind", "Rain Dance", "Scary Face"],
        ),
    ],
)

# 4th Place - Mattie Morgan
TEAM_4TH_MATTIE_MORGAN = TeamData(
    team_id=5415,
    player_name="Mattie Morgan",
    tournament_name="Regional Birmingham",
    placement="4th Place",
    pokemon=[
        PokemonData(
            species="Incineroar",
            item="Assault Vest",
            ability="Intimidate",
            tera_type="Grass",
            moves=["Flare Blitz", "Knock Off", "U-turn", "Fake Out"],
        ),
        PokemonData(
            species="Porygon2",
            item="Eviolite",
            ability="Download",
            tera_type="Flying",
            moves=["Tera Blast", "Ice Beam", "Recover", "Trick Room"],
        ),
        PokemonData(
            species="Amoonguss",
            item="Rocky Helmet",
            ability="Regenerator",
            tera_type="Fire",
            moves=["Sludge Bomb", "Spore", "Rage Powder", "Protect"],
        ),
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Focus Sash",
            ability="Unseen Fist",
            tera_type="Water",
            moves=["Close Combat", "Surging Strikes", "Aqua Jet", "Detect"],
        ),
        PokemonData(
            species="Ursaluna",
            item="Flame Orb",
            ability="Guts",
            tera_type="Ghost",
            moves=["Headlong Rush", "Earthquake", "Facade", "Protect"],
        ),
        PokemonData(
            species="Flutter Mane",
            item="Booster Energy",
            ability="Protosynthesis",
            tera_type="Water",
            moves=["Moonblast", "Shadow Ball", "Substitute", "Protect"],
        ),
    ],
)

# All tournament teams
TOURNAMENT_415_TEAMS = [
    TEAM_1ST_STEFANO_GREPPI,
    TEAM_2ND_MARCUS_KOH,
    TEAM_3RD_HENGYUE_ZHANG,
    TEAM_4TH_MATTIE_MORGAN,
]


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def tournament_415():
    """Create tournament 415 with all team data."""
    tournament = Tournament(
        id="415",
        name="Regional Birmingham",
        metadata={
            "source": "limitlessvgc.com",
            "date": "January 24, 2026",
            "format": "Scarlet & Violet Regulation F",
            "player_count": 688,
        },
    )

    division = Division(id="main", name="Masters")
    tournament.divisions.append(division)

    for team_data in TOURNAMENT_415_TEAMS:
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

class TestTournament415TeamData:
    """Tests for tournament 415 team data structure."""

    def test_team_count(self):
        """All 4 top teams are present."""
        assert len(TOURNAMENT_415_TEAMS) == 4

    def test_all_teams_have_6_pokemon(self):
        """Each team has exactly 6 Pokemon."""
        for team in TOURNAMENT_415_TEAMS:
            assert len(team.pokemon) == 6, f"{team.player_name}'s team has {len(team.pokemon)} Pokemon"

    def test_all_pokemon_have_required_fields(self):
        """All Pokemon have species, item, ability, tera_type, and 4 moves."""
        for team in TOURNAMENT_415_TEAMS:
            for poke in team.pokemon:
                assert poke.species, f"Missing species in {team.player_name}'s team"
                assert poke.item, f"Missing item for {poke.species}"
                assert poke.ability, f"Missing ability for {poke.species}"
                assert poke.tera_type, f"Missing tera_type for {poke.species}"
                assert len(poke.moves) == 4, f"{poke.species} has {len(poke.moves)} moves"

    def test_first_place_team_structure(self):
        """1st place team (Stefano Greppi) has correct Pokemon."""
        team = TEAM_1ST_STEFANO_GREPPI
        species = [p.species for p in team.pokemon]

        assert "Landorus" in species
        assert "Chien-Pao" in species
        assert "Incineroar" in species
        assert "Rillaboom" in species
        assert "Raging Bolt" in species
        assert "Urshifu-Rapid-Strike" in species

    def test_second_place_has_commander_combo(self):
        """2nd place team has Dondozo + Tatsugiri (Commander combo)."""
        team = TEAM_2ND_MARCUS_KOH
        species = [p.species for p in team.pokemon]
        abilities = [p.ability for p in team.pokemon]

        assert "Dondozo" in species
        assert "Tatsugiri" in species
        assert "Commander" in abilities

    def test_second_place_has_neutralizing_gas(self):
        """2nd place team has Galarian Weezing with Neutralizing Gas."""
        team = TEAM_2ND_MARCUS_KOH
        weezing = next(p for p in team.pokemon if "Weezing" in p.species)
        assert weezing.ability == "Neutralizing Gas"

    def test_third_place_has_psychic_terrain(self):
        """3rd place team has Psychic Surge (Indeedee-F)."""
        team = TEAM_3RD_HENGYUE_ZHANG
        abilities = [p.ability for p in team.pokemon]
        assert "Psychic Surge" in abilities

    def test_fourth_place_has_trick_room(self):
        """4th place team has Trick Room support."""
        team = TEAM_4TH_MATTIE_MORGAN
        all_moves = [m for p in team.pokemon for m in p.moves]
        assert "Trick Room" in all_moves


# =============================================================================
# Tournament Model Integration Tests
# =============================================================================

class TestTournament415Model:
    """Tests for tournament 415 model integration."""

    def test_tournament_created(self, tournament_415):
        """Tournament is created with correct metadata."""
        assert tournament_415.id == "415"
        assert tournament_415.name == "Regional Birmingham"
        assert tournament_415.metadata["format"] == "Scarlet & Violet Regulation F"
        assert tournament_415.metadata["player_count"] == 688

    def test_all_players_registered(self, tournament_415):
        """All 4 players are registered."""
        assert len(tournament_415.players) == 4

    def test_all_teams_registered(self, tournament_415):
        """All 4 teams are registered."""
        assert len(tournament_415.teams) == 4

    def test_player_team_association(self, tournament_415):
        """Each player is associated with their team."""
        for player in tournament_415.players.values():
            team = tournament_415.get_player_team(player.id)
            assert team is not None
            assert len(team.pokemon) == 6

    def test_first_place_player(self, tournament_415):
        """1st place player data is correct."""
        player = tournament_415.players.get("stefano_greppi")
        assert player is not None
        assert player.name == "Stefano Greppi"
        assert player.metadata["placement"] == "1st Place"

    def test_large_tournament_size(self, tournament_415):
        """Tournament 415 is a large regional (688 players)."""
        assert tournament_415.metadata["player_count"] == 688


# =============================================================================
# Pokemon Species Coverage Tests
# =============================================================================

class TestTournament415SpeciesCoverage:
    """Test the variety of Pokemon used in tournament 415."""

    def test_unique_species_count(self):
        """Count unique species across all teams."""
        all_species = set()
        for team in TOURNAMENT_415_TEAMS:
            for poke in team.pokemon:
                all_species.add(poke.species)

        # Tournament 415 has diverse teams
        assert len(all_species) >= 15, f"Only {len(all_species)} unique species"

    def test_urshifu_prevalence(self):
        """Urshifu-Rapid-Strike appears on multiple teams."""
        urshifu_count = sum(
            1 for team in TOURNAMENT_415_TEAMS
            for p in team.pokemon if "Urshifu" in p.species
        )
        assert urshifu_count >= 3, "Urshifu is a meta staple"

    def test_flutter_mane_usage(self):
        """Flutter Mane appears on multiple teams."""
        flutter_count = sum(
            1 for team in TOURNAMENT_415_TEAMS
            for p in team.pokemon if p.species == "Flutter Mane"
        )
        assert flutter_count >= 2

    def test_legendary_representation(self):
        """Various legendary/paradox Pokemon are used."""
        legendaries = {"Landorus", "Raging Bolt", "Chi-Yu", "Chien-Pao",
                      "Iron Crown", "Regidrago", "Tornadus", "Flutter Mane"}
        found = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if p.species in legendaries:
                    found.add(p.species)
        assert len(found) >= 5


# =============================================================================
# Item and Ability Coverage Tests
# =============================================================================

class TestTournament415ItemsAbilities:
    """Test item and ability variety in tournament 415."""

    def test_common_items(self):
        """Common competitive items are present."""
        all_items = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                all_items.add(p.item)

        expected_items = ["Focus Sash", "Booster Energy", "Assault Vest", "Choice Scarf"]
        for item in expected_items:
            assert item in all_items, f"Expected {item} in tournament"

    def test_ruin_abilities(self):
        """Ruin abilities are present (Sword of Ruin, Beads of Ruin)."""
        ruin_abilities = {"Sword of Ruin", "Beads of Ruin", "Vessel of Ruin", "Tablets of Ruin"}
        found = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if p.ability in ruin_abilities:
                    found.add(p.ability)
        assert len(found) >= 2, "Expected multiple Ruin abilities"

    def test_terrain_setters(self):
        """Terrain-setting abilities are present."""
        terrain_abilities = {"Grassy Surge", "Psychic Surge", "Electric Surge", "Misty Surge"}
        found = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if p.ability in terrain_abilities:
                    found.add(p.ability)
        assert len(found) >= 2

    def test_intimidate_usage(self):
        """Intimidate remains a common ability."""
        intimidate_count = sum(
            1 for team in TOURNAMENT_415_TEAMS
            for p in team.pokemon if p.ability == "Intimidate"
        )
        assert intimidate_count >= 2


# =============================================================================
# Move Coverage Tests
# =============================================================================

class TestTournament415Moves:
    """Test move variety and strategy in tournament 415."""

    def test_protect_prevalence(self):
        """Protect variants are common in doubles."""
        protect_moves = {"Protect", "Detect", "Spiky Shield"}
        protect_count = 0
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if any(m in protect_moves for m in p.moves):
                    protect_count += 1

        assert protect_count >= 10, "Protect is essential in VGC doubles"

    def test_fake_out_presence(self):
        """Fake Out is present on support Pokemon."""
        fake_out_users = []
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if "Fake Out" in p.moves:
                    fake_out_users.append(p.species)

        assert len(fake_out_users) >= 3

    def test_speed_control_moves(self):
        """Speed control moves are present."""
        speed_control = {"Tailwind", "Trick Room", "Icy Wind", "Scary Face"}
        found = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                found.update(set(p.moves) & speed_control)

        assert len(found) >= 3, "Expected variety of speed control"

    def test_priority_moves(self):
        """Priority moves are present."""
        priority_moves = {"Fake Out", "Extreme Speed", "Aqua Jet", "Grassy Glide",
                        "Sucker Punch", "Thunderclap"}
        found = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                found.update(set(p.moves) & priority_moves)

        assert len(found) >= 4


# =============================================================================
# Tera Type Strategy Tests
# =============================================================================

class TestTournament415TeraTypes:
    """Test Tera type distribution and strategy."""

    def test_defensive_tera_types(self):
        """Defensive tera types are used."""
        tera_types = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                tera_types.add(p.tera_type)

        assert "Ghost" in tera_types
        assert "Steel" in tera_types

    def test_offensive_tera_types(self):
        """Offensive tera types are used."""
        tera_types = set()
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                tera_types.add(p.tera_type)

        # Normal for Extreme Speed, Fairy for offensive, etc.
        assert "Normal" in tera_types or "Fairy" in tera_types

    def test_grass_tera_for_ground_immunity(self):
        """Grass tera is used to dodge Ground moves."""
        grass_tera_users = []
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if p.tera_type == "Grass":
                    grass_tera_users.append(p.species)

        assert len(grass_tera_users) >= 1


# =============================================================================
# Team Archetype Tests
# =============================================================================

class TestTournament415TeamArchetypes:
    """Analyze team archetypes from tournament 415."""

    def test_team_archetypes(self):
        """Identify team archetypes based on composition."""
        archetypes = {}

        for team in TOURNAMENT_415_TEAMS:
            abilities = [p.ability for p in team.pokemon]
            species = [p.species for p in team.pokemon]
            moves_flat = [m for p in team.pokemon for m in p.moves]

            # Check for Commander team (Dondozo + Tatsugiri)
            if "Dondozo" in species and "Tatsugiri" in species:
                archetypes[team.player_name] = "Commander"
            # Check for Trick Room team
            elif "Trick Room" in moves_flat:
                archetypes[team.player_name] = "Trick Room"
            # Check for Psychic Terrain team
            elif "Psychic Surge" in abilities:
                archetypes[team.player_name] = "Psychic Terrain"
            # Check for Grassy Terrain team
            elif "Grassy Surge" in abilities:
                archetypes[team.player_name] = "Grassy Terrain"
            else:
                archetypes[team.player_name] = "Balanced"

        # Multiple different archetypes
        assert len(set(archetypes.values())) >= 3

    def test_offensive_vs_defensive_teams(self):
        """Mix of offensive and defensive strategies."""
        offensive_pokemon = {"Chien-Pao", "Chi-Yu", "Flutter Mane", "Urshifu-Rapid-Strike"}
        defensive_pokemon = {"Dondozo", "Amoonguss", "Porygon2", "Incineroar"}

        offensive_count = 0
        defensive_count = 0

        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if p.species in offensive_pokemon:
                    offensive_count += 1
                if p.species in defensive_pokemon:
                    defensive_count += 1

        assert offensive_count >= 5, "Expected offensive threats"
        assert defensive_count >= 4, "Expected defensive cores"


# =============================================================================
# Unique Strategies Tests
# =============================================================================

class TestTournament415UniqueStrategies:
    """Test unique strategies present in tournament 415."""

    def test_neutralizing_gas_strategy(self):
        """Neutralizing Gas is used to counter abilities."""
        gas_users = []
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if p.ability == "Neutralizing Gas":
                    gas_users.append(team.player_name)

        assert len(gas_users) >= 1, "Neutralizing Gas is a unique strategy"

    def test_commander_strategy(self):
        """Commander combo (Dondozo + Tatsugiri) is represented."""
        has_commander = False
        for team in TOURNAMENT_415_TEAMS:
            species = [p.species for p in team.pokemon]
            if "Dondozo" in species and "Tatsugiri" in species:
                has_commander = True
                break

        assert has_commander, "Commander combo should be in top cut"

    def test_substitute_usage(self):
        """Substitute is used for chip damage/protection."""
        sub_users = []
        for team in TOURNAMENT_415_TEAMS:
            for p in team.pokemon:
                if "Substitute" in p.moves:
                    sub_users.append(p.species)

        assert len(sub_users) >= 1


# =============================================================================
# Battle Simulation Tests
# =============================================================================

class TestTournament415BattleSimulation:
    """Tests that simulate battles between tournament 415 teams.

    Note: These tests require species name -> ID resolution to be implemented.
    Currently skipped because tournament teams use string species names
    while the battle simulator expects integer species IDs.
    """

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_finals_matchup(self, tournament_415):
        """Simulate the finals matchup (1st vs 2nd place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        match = Match(
            id="finals",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="stefano_greppi",
            player2_id="marcus_koh",
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
            tournament_415,
            regulation,
            config.__dict__,
            base_seed=42,
        )

        assert result.completed
        assert result.winner_id in ["stefano_greppi", "marcus_koh"]

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_semifinal_matchup(self, tournament_415):
        """Simulate semifinal matchup (3rd vs 4th place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        match = Match(
            id="semifinal",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="hengyue_zhang",
            player2_id="mattie_morgan",
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
            tournament_415,
            regulation,
            config.__dict__,
            base_seed=123,
        )

        assert result.completed
        assert result.winner_id in ["hengyue_zhang", "mattie_morgan"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
