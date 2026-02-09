"""Tests using tournament data from Limitless VGC Tournament 418.

Tournament: Regional Sydney
Date: February 7, 2026
Format: Scarlet & Violet Regulation F
Players: 278
Source: https://limitlessvgc.com/tournaments/418

These tests use real competitive team data to verify:
- Team parsing and validation
- Battle simulation with competitive teams
- Tournament model integration
"""

import pytest

from tournament.model import Tournament, Division, Player, Team
from tournament.limitless_loader import PokemonData, TeamData


# =============================================================================
# Tournament 418 Team Data - Regional Sydney
# =============================================================================

# 1st Place - Drew Bliss
TEAM_1ST_DREW_BLISS = TeamData(
    team_id=5591,
    player_name="Drew Bliss",
    tournament_name="Regional Sydney",
    placement="1st Place",
    pokemon=[
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Mystic Water",
            ability="Unseen Fist",
            tera_type="Fire",
            moves=["Surging Strikes", "Close Combat", "Aqua Jet", "Protect"],
        ),
        PokemonData(
            species="Zoroark-Hisui",
            item="Life Orb",
            ability="Illusion",
            tera_type="Stellar",
            moves=["Shadow Ball", "Hyper Voice", "Tera Blast", "Protect"],
        ),
        PokemonData(
            species="Whimsicott",
            item="Focus Sash",
            ability="Prankster",
            tera_type="Ghost",
            moves=["Moonblast", "Tailwind", "Encore", "Helping Hand"],
        ),
        PokemonData(
            species="Rillaboom",
            item="Assault Vest",
            ability="Grassy Surge",
            tera_type="Fire",
            moves=["Wood Hammer", "Grassy Glide", "High Horsepower", "Fake Out"],
        ),
        PokemonData(
            species="Regidrago",
            item="Dragon Fang",
            ability="Dragon's Maw",
            tera_type="Steel",
            moves=["Dragon Energy", "Draco Meteor", "Earth Power", "Protect"],
        ),
        PokemonData(
            species="Kingambit",
            item="Safety Goggles",
            ability="Defiant",
            tera_type="Flying",
            moves=["Kowtow Cleave", "Iron Head", "Sucker Punch", "Protect"],
        ),
    ],
)

# 2nd Place - Yuxiang Wang
TEAM_2ND_YUXIANG_WANG = TeamData(
    team_id=5592,
    player_name="Yuxiang Wang",
    tournament_name="Regional Sydney",
    placement="2nd Place",
    pokemon=[
        PokemonData(
            species="Incineroar",
            item="Sitrus Berry",
            ability="Intimidate",
            tera_type="Ghost",
            moves=["Fake Out", "Knock Off", "Parting Shot", "Taunt"],
        ),
        PokemonData(
            species="Ogerpon-Hearthflame",
            item="Hearthflame Mask",
            ability="Mold Breaker",
            tera_type="Fire",
            moves=["Swords Dance", "Ivy Cudgel", "Grassy Glide", "Spiky Shield"],
        ),
        PokemonData(
            species="Flutter Mane",
            item="Booster Energy",
            ability="Protosynthesis",
            tera_type="Grass",
            moves=["Moonblast", "Icy Wind", "Thunder Wave", "Protect"],
        ),
        PokemonData(
            species="Raging Bolt",
            item="Leftovers",
            ability="Protosynthesis",
            tera_type="Fairy",
            moves=["Calm Mind", "Thunderclap", "Dragon Pulse", "Protect"],
        ),
        PokemonData(
            species="Rillaboom",
            item="Assault Vest",
            ability="Grassy Surge",
            tera_type="Fire",
            moves=["Fake Out", "Grassy Glide", "Wood Hammer", "High Horsepower"],
        ),
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Focus Sash",
            ability="Unseen Fist",
            tera_type="Water",
            moves=["Surging Strikes", "Aqua Jet", "Close Combat", "Protect"],
        ),
    ],
)

# 3rd Place - Yuxiang Peng
TEAM_3RD_YUXIANG_PENG = TeamData(
    team_id=5593,
    player_name="Yuxiang Peng",
    tournament_name="Regional Sydney",
    placement="3rd Place",
    pokemon=[
        PokemonData(
            species="Ogerpon-Hearthflame",
            item="Hearthflame Mask",
            ability="Mold Breaker",
            tera_type="Fire",
            moves=["Spiky Shield", "Ivy Cudgel", "Wood Hammer", "Follow Me"],
        ),
        PokemonData(
            species="Tornadus",
            item="Covert Cloak",
            ability="Prankster",
            tera_type="Steel",
            moves=["Protect", "Tailwind", "Bleakwind Storm", "Sunny Day"],
        ),
        PokemonData(
            species="Incineroar",
            item="Assault Vest",
            ability="Intimidate",
            tera_type="Grass",
            moves=["Fake Out", "Flare Blitz", "Knock Off", "U-turn"],
        ),
        PokemonData(
            species="Farigiraf",
            item="Throat Spray",
            ability="Armor Tail",
            tera_type="Fairy",
            moves=["Protect", "Trick Room", "Hyper Voice", "Psychic"],
        ),
        PokemonData(
            species="Ursaluna",
            item="Flame Orb",
            ability="Guts",
            tera_type="Dragon",
            moves=["Protect", "Facade", "Headlong Rush", "Earthquake"],
        ),
        PokemonData(
            species="Flutter Mane",
            item="Choice Specs",
            ability="Protosynthesis",
            tera_type="Fairy",
            moves=["Moonblast", "Dazzling Gleam", "Shadow Ball", "Power Gem"],
        ),
    ],
)

# 4th Place - Kynan Campbell
TEAM_4TH_KYNAN_CAMPBELL = TeamData(
    team_id=5594,
    player_name="Kynan Campbell",
    tournament_name="Regional Sydney",
    placement="4th Place",
    pokemon=[
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Mystic Water",
            ability="Unseen Fist",
            tera_type="Steel",
            moves=["Surging Strikes", "Close Combat", "Taunt", "Protect"],
        ),
        PokemonData(
            species="Ursaluna",
            item="Flame Orb",
            ability="Guts",
            tera_type="Ghost",
            moves=["Headlong Rush", "Facade", "Protect", "Earthquake"],
        ),
        PokemonData(
            species="Cresselia",
            item="Safety Goggles",
            ability="Levitate",
            tera_type="Steel",
            moves=["Psychic", "Icy Wind", "Trick Room", "Lunar Blessing"],
        ),
        PokemonData(
            species="Flutter Mane",
            item="Choice Specs",
            ability="Protosynthesis",
            tera_type="Fairy",
            moves=["Dazzling Gleam", "Shadow Ball", "Moonblast", "Power Gem"],
        ),
        PokemonData(
            species="Incineroar",
            item="Assault Vest",
            ability="Intimidate",
            tera_type="Grass",
            moves=["Flare Blitz", "Knock Off", "U-turn", "Fake Out"],
        ),
        PokemonData(
            species="Amoonguss",
            item="Rocky Helmet",
            ability="Regenerator",
            tera_type="Fire",
            moves=["Rage Powder", "Spore", "Sludge Bomb", "Protect"],
        ),
    ],
)

# All tournament teams
TOURNAMENT_418_TEAMS = [
    TEAM_1ST_DREW_BLISS,
    TEAM_2ND_YUXIANG_WANG,
    TEAM_3RD_YUXIANG_PENG,
    TEAM_4TH_KYNAN_CAMPBELL,
]


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def tournament_418():
    """Create tournament 418 with all team data."""
    tournament = Tournament(
        id="418",
        name="Regional Sydney",
        metadata={
            "source": "limitlessvgc.com",
            "date": "February 7, 2026",
            "format": "Scarlet & Violet Regulation F",
            "player_count": 278,
        },
    )

    division = Division(id="main", name="Masters")
    tournament.divisions.append(division)

    for team_data in TOURNAMENT_418_TEAMS:
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

class TestTournament418TeamData:
    """Tests for tournament 418 team data structure."""

    def test_team_count(self):
        """All 4 top teams are present."""
        assert len(TOURNAMENT_418_TEAMS) == 4

    def test_all_teams_have_6_pokemon(self):
        """Each team has exactly 6 Pokemon."""
        for team in TOURNAMENT_418_TEAMS:
            assert len(team.pokemon) == 6, f"{team.player_name}'s team has {len(team.pokemon)} Pokemon"

    def test_all_pokemon_have_required_fields(self):
        """All Pokemon have species, item, ability, tera_type, and 4 moves."""
        for team in TOURNAMENT_418_TEAMS:
            for poke in team.pokemon:
                assert poke.species, f"Missing species in {team.player_name}'s team"
                assert poke.item, f"Missing item for {poke.species}"
                assert poke.ability, f"Missing ability for {poke.species}"
                assert poke.tera_type, f"Missing tera_type for {poke.species}"
                assert len(poke.moves) == 4, f"{poke.species} has {len(poke.moves)} moves"

    def test_first_place_team_structure(self):
        """1st place team (Drew Bliss) has correct Pokemon."""
        team = TEAM_1ST_DREW_BLISS
        species = [p.species for p in team.pokemon]

        assert "Urshifu-Rapid-Strike" in species
        assert "Zoroark-Hisui" in species
        assert "Whimsicott" in species
        assert "Rillaboom" in species
        assert "Regidrago" in species
        assert "Kingambit" in species

    def test_first_place_has_illusion(self):
        """1st place uses Hisuian Zoroark with Illusion."""
        team = TEAM_1ST_DREW_BLISS
        zoroark = next(p for p in team.pokemon if "Zoroark" in p.species)
        assert zoroark.ability == "Illusion"
        assert zoroark.tera_type == "Stellar"

    def test_first_place_has_defiant_kingambit(self):
        """1st place uses Kingambit with Defiant."""
        team = TEAM_1ST_DREW_BLISS
        kingambit = next(p for p in team.pokemon if p.species == "Kingambit")
        assert kingambit.ability == "Defiant"

    def test_second_place_has_swords_dance_ogerpon(self):
        """2nd place uses Swords Dance Ogerpon."""
        team = TEAM_2ND_YUXIANG_WANG
        ogerpon = next(p for p in team.pokemon if "Ogerpon" in p.species)
        assert "Swords Dance" in ogerpon.moves

    def test_third_place_has_farigiraf(self):
        """3rd place uses Farigiraf with Armor Tail."""
        team = TEAM_3RD_YUXIANG_PENG
        farigiraf = next(p for p in team.pokemon if p.species == "Farigiraf")
        assert farigiraf.ability == "Armor Tail"
        assert "Trick Room" in farigiraf.moves

    def test_fourth_place_has_trick_room_core(self):
        """4th place has Cresselia + Ursaluna Trick Room core."""
        team = TEAM_4TH_KYNAN_CAMPBELL
        species = [p.species for p in team.pokemon]
        assert "Cresselia" in species
        assert "Ursaluna" in species

        cresselia = next(p for p in team.pokemon if p.species == "Cresselia")
        assert "Trick Room" in cresselia.moves


# =============================================================================
# Tournament Model Integration Tests
# =============================================================================

class TestTournament418Model:
    """Tests for tournament 418 model integration."""

    def test_tournament_created(self, tournament_418):
        """Tournament is created with correct metadata."""
        assert tournament_418.id == "418"
        assert tournament_418.name == "Regional Sydney"
        assert tournament_418.metadata["format"] == "Scarlet & Violet Regulation F"
        assert tournament_418.metadata["player_count"] == 278

    def test_all_players_registered(self, tournament_418):
        """All 4 players are registered."""
        assert len(tournament_418.players) == 4

    def test_all_teams_registered(self, tournament_418):
        """All 4 teams are registered."""
        assert len(tournament_418.teams) == 4

    def test_player_team_association(self, tournament_418):
        """Each player is associated with their team."""
        for player in tournament_418.players.values():
            team = tournament_418.get_player_team(player.id)
            assert team is not None
            assert len(team.pokemon) == 6

    def test_first_place_player(self, tournament_418):
        """1st place player data is correct."""
        player = tournament_418.players.get("drew_bliss")
        assert player is not None
        assert player.name == "Drew Bliss"
        assert player.metadata["placement"] == "1st Place"


# =============================================================================
# Pokemon Species Coverage Tests
# =============================================================================

class TestTournament418SpeciesCoverage:
    """Test the variety of Pokemon used in tournament 418."""

    def test_unique_species_count(self):
        """Count unique species across all teams."""
        all_species = set()
        for team in TOURNAMENT_418_TEAMS:
            for poke in team.pokemon:
                all_species.add(poke.species)

        # Tournament 418 has diverse teams
        assert len(all_species) >= 12, f"Only {len(all_species)} unique species"

    def test_flutter_mane_dominance(self):
        """Flutter Mane appears on most teams."""
        flutter_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if p.species == "Flutter Mane"
        )
        assert flutter_count >= 3, "Flutter Mane is dominant in meta"

    def test_urshifu_prevalence(self):
        """Urshifu-Rapid-Strike appears on multiple teams."""
        urshifu_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if "Urshifu" in p.species
        )
        assert urshifu_count >= 3

    def test_incineroar_prevalence(self):
        """Incineroar appears on multiple teams."""
        incineroar_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if p.species == "Incineroar"
        )
        assert incineroar_count >= 3

    def test_unique_picks(self):
        """Some unique Pokemon picks are present."""
        unique_species = {"Zoroark-Hisui", "Kingambit", "Whimsicott", "Farigiraf"}
        found = set()
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if p.species in unique_species:
                    found.add(p.species)
        assert len(found) >= 3, "Expected unique picks in top cut"


# =============================================================================
# Item and Ability Coverage Tests
# =============================================================================

class TestTournament418ItemsAbilities:
    """Test item and ability variety in tournament 418."""

    def test_common_items(self):
        """Common competitive items are present."""
        all_items = set()
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                all_items.add(p.item)

        expected_items = ["Assault Vest", "Focus Sash", "Choice Specs", "Flame Orb"]
        for item in expected_items:
            assert item in all_items, f"Expected {item} in tournament"

    def test_intimidate_usage(self):
        """Intimidate remains common."""
        intimidate_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if p.ability == "Intimidate"
        )
        assert intimidate_count >= 3

    def test_prankster_usage(self):
        """Prankster is used for speed control."""
        prankster_users = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if p.ability == "Prankster":
                    prankster_users.append(p.species)
        assert len(prankster_users) >= 2

    def test_guts_ursaluna(self):
        """Guts Ursaluna with Flame Orb is present."""
        guts_count = 0
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if p.species == "Ursaluna" and p.ability == "Guts" and p.item == "Flame Orb":
                    guts_count += 1
        assert guts_count >= 2


# =============================================================================
# Move Coverage Tests
# =============================================================================

class TestTournament418Moves:
    """Test move variety and strategy in tournament 418."""

    def test_protect_prevalence(self):
        """Protect variants are common."""
        protect_moves = {"Protect", "Spiky Shield", "Detect"}
        protect_count = 0
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if any(m in protect_moves for m in p.moves):
                    protect_count += 1

        assert protect_count >= 12

    def test_tailwind_presence(self):
        """Tailwind is used for speed control."""
        tailwind_users = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if "Tailwind" in p.moves:
                    tailwind_users.append(p.species)
        assert len(tailwind_users) >= 2

    def test_trick_room_presence(self):
        """Trick Room is used on multiple teams."""
        tr_users = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if "Trick Room" in p.moves:
                    tr_users.append(p.species)
        assert len(tr_users) >= 2

    def test_fake_out_presence(self):
        """Fake Out is common."""
        fake_out_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if "Fake Out" in p.moves
        )
        assert fake_out_count >= 4

    def test_redirection_moves(self):
        """Redirection moves are present."""
        redirect_moves = {"Follow Me", "Rage Powder"}
        found = set()
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                found.update(set(p.moves) & redirect_moves)
        assert len(found) >= 1


# =============================================================================
# Tera Type Strategy Tests
# =============================================================================

class TestTournament418TeraTypes:
    """Test Tera type distribution and strategy."""

    def test_fire_tera_common(self):
        """Fire tera is commonly used."""
        fire_tera_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if p.tera_type == "Fire"
        )
        assert fire_tera_count >= 4

    def test_defensive_steel_tera(self):
        """Steel tera is used defensively."""
        steel_tera_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if p.tera_type == "Steel"
        )
        assert steel_tera_count >= 2

    def test_stellar_tera_usage(self):
        """Stellar tera is used."""
        stellar_users = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if p.tera_type == "Stellar":
                    stellar_users.append(p.species)
        assert len(stellar_users) >= 1

    def test_grass_tera_for_ground_immunity(self):
        """Grass tera is used to counter Ground moves."""
        grass_tera_count = sum(
            1 for team in TOURNAMENT_418_TEAMS
            for p in team.pokemon if p.tera_type == "Grass"
        )
        assert grass_tera_count >= 2


# =============================================================================
# Team Archetype Tests
# =============================================================================

class TestTournament418TeamArchetypes:
    """Analyze team archetypes from tournament 418."""

    def test_team_archetypes(self):
        """Identify team archetypes based on composition."""
        archetypes = {}

        for team in TOURNAMENT_418_TEAMS:
            abilities = [p.ability for p in team.pokemon]
            moves_flat = [m for p in team.pokemon for m in p.moves]

            # Check for Trick Room team
            if "Trick Room" in moves_flat and any(
                p.species in ["Ursaluna", "Cresselia", "Farigiraf"] for p in team.pokemon
            ):
                archetypes[team.player_name] = "Trick Room"
            # Check for Tailwind team
            elif "Tailwind" in moves_flat:
                archetypes[team.player_name] = "Tailwind"
            # Check for Grassy Terrain team
            elif "Grassy Surge" in abilities:
                archetypes[team.player_name] = "Grassy Terrain"
            else:
                archetypes[team.player_name] = "Balanced"

        # Multiple archetypes present
        assert len(set(archetypes.values())) >= 2

    def test_speed_control_diversity(self):
        """Multiple forms of speed control are used."""
        speed_control = set()
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if "Tailwind" in p.moves:
                    speed_control.add("Tailwind")
                if "Trick Room" in p.moves:
                    speed_control.add("Trick Room")
                if "Icy Wind" in p.moves:
                    speed_control.add("Icy Wind")
                if "Thunder Wave" in p.moves:
                    speed_control.add("Thunder Wave")

        assert len(speed_control) >= 3


# =============================================================================
# Unique Strategies Tests
# =============================================================================

class TestTournament418UniqueStrategies:
    """Test unique strategies present in tournament 418."""

    def test_illusion_zoroark(self):
        """Illusion Zoroark is a unique tech."""
        zoroark_teams = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if "Zoroark" in p.species:
                    zoroark_teams.append(team.player_name)
        assert len(zoroark_teams) >= 1

    def test_defiant_kingambit(self):
        """Defiant Kingambit counters Intimidate."""
        kingambit_teams = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if p.species == "Kingambit" and p.ability == "Defiant":
                    kingambit_teams.append(team.player_name)
        assert len(kingambit_teams) >= 1

    def test_armor_tail_farigiraf(self):
        """Armor Tail Farigiraf blocks priority."""
        farigiraf_teams = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if p.species == "Farigiraf" and p.ability == "Armor Tail":
                    farigiraf_teams.append(team.player_name)
        assert len(farigiraf_teams) >= 1

    def test_encore_support(self):
        """Encore is used to disrupt opponents."""
        encore_users = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if "Encore" in p.moves:
                    encore_users.append(p.species)
        assert len(encore_users) >= 1

    def test_lunar_blessing_cresselia(self):
        """Lunar Blessing provides team healing."""
        lb_users = []
        for team in TOURNAMENT_418_TEAMS:
            for p in team.pokemon:
                if "Lunar Blessing" in p.moves:
                    lb_users.append(p.species)
        assert len(lb_users) >= 1


# =============================================================================
# Battle Simulation Tests
# =============================================================================

class TestTournament418BattleSimulation:
    """Tests that simulate battles between tournament 418 teams.

    Note: These tests require species name -> ID resolution to be implemented.
    Currently skipped because tournament teams use string species names
    while the battle simulator expects integer species IDs.
    """

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_finals_matchup(self, tournament_418):
        """Simulate the finals matchup (1st vs 2nd place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        match = Match(
            id="finals",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="drew_bliss",
            player2_id="yuxiang_wang",
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
            tournament_418,
            regulation,
            config.__dict__,
            base_seed=42,
        )

        assert result.completed
        assert result.winner_id in ["drew_bliss", "yuxiang_wang"]

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_semifinal_matchup(self, tournament_418):
        """Simulate semifinal matchup (3rd vs 4th place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        match = Match(
            id="semifinal",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="yuxiang_peng",
            player2_id="kynan_campbell",
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
            tournament_418,
            regulation,
            config.__dict__,
            base_seed=123,
        )

        assert result.completed
        assert result.winner_id in ["yuxiang_peng", "kynan_campbell"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
