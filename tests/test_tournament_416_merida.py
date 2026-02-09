"""Tests using tournament data from Limitless VGC Tournament 416.

Tournament: Regional Merida
Date: January 24, 2026
Format: Scarlet & Violet Regulation F
Players: 234
Source: https://limitlessvgc.com/tournaments/416

These tests use real competitive team data to verify:
- Team parsing and validation
- Battle simulation with competitive teams
- Tournament model integration
"""

import pytest

from tournament.model import Tournament, Division, Player, Team
from tournament.limitless_loader import PokemonData, TeamData


# =============================================================================
# Tournament 416 Team Data - Regional Merida
# =============================================================================

# 1st Place - Max Morales
TEAM_1ST_MAX_MORALES = TeamData(
    team_id=5498,
    player_name="Max Morales",
    tournament_name="Regional Merida",
    placement="1st Place",
    pokemon=[
        PokemonData(
            species="Gholdengo",
            item="Metal Coat",
            ability="Good as Gold",
            tera_type="Fairy",
            moves=["Shadow Ball", "Make It Rain", "Nasty Plot", "Protect"],
        ),
        PokemonData(
            species="Porygon2",
            item="Eviolite",
            ability="Download",
            tera_type="Flying",
            moves=["Tera Blast", "Ice Beam", "Recover", "Trick Room"],
        ),
        PokemonData(
            species="Ursaluna",
            item="Flame Orb",
            ability="Guts",
            tera_type="Ghost",
            moves=["Facade", "Earthquake", "Headlong Rush", "Protect"],
        ),
        PokemonData(
            species="Ogerpon-Wellspring",
            item="Wellspring Mask",
            ability="Water Absorb",
            tera_type="Water",
            moves=["Ivy Cudgel", "Wood Hammer", "Follow Me", "Spiky Shield"],
        ),
        PokemonData(
            species="Tornadus",
            item="Rocky Helmet",
            ability="Prankster",
            tera_type="Steel",
            moves=["Bleakwind Storm", "Rain Dance", "Tailwind", "Protect"],
        ),
        PokemonData(
            species="Incineroar",
            item="Sitrus Berry",
            ability="Intimidate",
            tera_type="Grass",
            moves=["Fake Out", "Knock Off", "Flare Blitz", "Parting Shot"],
        ),
    ],
)

# 2nd Place - Victor Manoath
TEAM_2ND_VICTOR_MANOATH = TeamData(
    team_id=5499,
    player_name="Victor Manoath",
    tournament_name="Regional Merida",
    placement="2nd Place",
    pokemon=[
        PokemonData(
            species="Gholdengo",
            item="Metal Coat",
            ability="Good as Gold",
            tera_type="Dragon",
            moves=["Protect", "Make It Rain", "Nasty Plot", "Shadow Ball"],
        ),
        PokemonData(
            species="Landorus",
            item="Life Orb",
            ability="Sheer Force",
            tera_type="Poison",
            moves=["Protect", "Earth Power", "Sludge Bomb", "Sandsear Storm"],
        ),
        PokemonData(
            species="Dragonite",
            item="Assault Vest",
            ability="Multiscale",
            tera_type="Flying",
            moves=["Extreme Speed", "Dragon Claw", "Tera Blast", "Ice Spinner"],
        ),
        PokemonData(
            species="Gouging Fire",
            item="Booster Energy",
            ability="Protosynthesis",
            tera_type="Fairy",
            moves=["Breaking Swipe", "Heat Crash", "Howl", "Snarl"],
        ),
        PokemonData(
            species="Ogerpon-Wellspring",
            item="Wellspring Mask",
            ability="Water Absorb",
            tera_type="Water",
            moves=["Ivy Cudgel", "Wood Hammer", "Follow Me", "Spiky Shield"],
        ),
        PokemonData(
            species="Flutter Mane",
            item="Sitrus Berry",
            ability="Protosynthesis",
            tera_type="Grass",
            moves=["Moonblast", "Taunt", "Thunder Wave", "Icy Wind"],
        ),
    ],
)

# 3rd Place - David Israel Soto
TEAM_3RD_DAVID_ISRAEL_SOTO = TeamData(
    team_id=5500,
    player_name="David Israel Soto",
    tournament_name="Regional Merida",
    placement="3rd Place",
    pokemon=[
        PokemonData(
            species="Amoonguss",
            item="Rocky Helmet",
            ability="Regenerator",
            tera_type="Fairy",
            moves=["Spore", "Pollen Puff", "Rage Powder", "Protect"],
        ),
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Mystic Water",
            ability="Unseen Fist",
            tera_type="Steel",
            moves=["Surging Strikes", "Close Combat", "Aqua Jet", "Detect"],
        ),
        PokemonData(
            species="Tornadus",
            item="Sky Plate",
            ability="Prankster",
            tera_type="Steel",
            moves=["Bleakwind Storm", "Rain Dance", "Tailwind", "Protect"],
        ),
        PokemonData(
            species="Porygon2",
            item="Eviolite",
            ability="Download",
            tera_type="Flying",
            moves=["Tera Blast", "Ice Beam", "Recover", "Trick Room"],
        ),
        PokemonData(
            species="Ursaluna",
            item="Flame Orb",
            ability="Guts",
            tera_type="Ghost",
            moves=["Facade", "Headlong Rush", "Earthquake", "Protect"],
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

# 4th Place - Kenneth Gamboa
TEAM_4TH_KENNETH_GAMBOA = TeamData(
    team_id=5501,
    player_name="Kenneth Gamboa",
    tournament_name="Regional Merida",
    placement="4th Place",
    pokemon=[
        PokemonData(
            species="Porygon2",
            item="Eviolite",
            ability="Download",
            tera_type="Flying",
            moves=["Tera Blast", "Ice Beam", "Recover", "Trick Room"],
        ),
        PokemonData(
            species="Amoonguss",
            item="Mental Herb",
            ability="Regenerator",
            tera_type="Fairy",
            moves=["Sludge Bomb", "Protect", "Rage Powder", "Spore"],
        ),
        PokemonData(
            species="Urshifu-Rapid-Strike",
            item="Mystic Water",
            ability="Unseen Fist",
            tera_type="Fire",
            moves=["Surging Strikes", "Close Combat", "Aqua Jet", "Detect"],
        ),
        PokemonData(
            species="Tornadus",
            item="Covert Cloak",
            ability="Prankster",
            tera_type="Steel",
            moves=["Bleakwind Storm", "Protect", "Tailwind", "Rain Dance"],
        ),
        PokemonData(
            species="Ursaluna",
            item="Flame Orb",
            ability="Guts",
            tera_type="Dragon",
            moves=["Facade", "Earthquake", "Headlong Rush", "Protect"],
        ),
        PokemonData(
            species="Incineroar",
            item="Assault Vest",
            ability="Intimidate",
            tera_type="Grass",
            moves=["Knock Off", "Flare Blitz", "Fake Out", "U-turn"],
        ),
    ],
)

# All tournament teams
TOURNAMENT_416_TEAMS = [
    TEAM_1ST_MAX_MORALES,
    TEAM_2ND_VICTOR_MANOATH,
    TEAM_3RD_DAVID_ISRAEL_SOTO,
    TEAM_4TH_KENNETH_GAMBOA,
]


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def tournament_416():
    """Create tournament 416 with all team data."""
    tournament = Tournament(
        id="416",
        name="Regional Merida",
        metadata={
            "source": "limitlessvgc.com",
            "date": "January 24, 2026",
            "format": "Scarlet & Violet Regulation F",
            "player_count": 234,
        },
    )

    division = Division(id="main", name="Masters")
    tournament.divisions.append(division)

    for team_data in TOURNAMENT_416_TEAMS:
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

class TestTournament416TeamData:
    """Tests for tournament 416 team data structure."""

    def test_team_count(self):
        """All 4 top teams are present."""
        assert len(TOURNAMENT_416_TEAMS) == 4

    def test_all_teams_have_6_pokemon(self):
        """Each team has exactly 6 Pokemon."""
        for team in TOURNAMENT_416_TEAMS:
            assert len(team.pokemon) == 6, f"{team.player_name}'s team has {len(team.pokemon)} Pokemon"

    def test_all_pokemon_have_required_fields(self):
        """All Pokemon have species, item, ability, tera_type, and 4 moves."""
        for team in TOURNAMENT_416_TEAMS:
            for poke in team.pokemon:
                assert poke.species, f"Missing species in {team.player_name}'s team"
                assert poke.item, f"Missing item for {poke.species}"
                assert poke.ability, f"Missing ability for {poke.species}"
                assert poke.tera_type, f"Missing tera_type for {poke.species}"
                assert len(poke.moves) == 4, f"{poke.species} has {len(poke.moves)} moves"

    def test_first_place_team_structure(self):
        """1st place team (Max Morales) has correct Pokemon."""
        team = TEAM_1ST_MAX_MORALES
        species = [p.species for p in team.pokemon]

        assert "Gholdengo" in species
        assert "Porygon2" in species
        assert "Ursaluna" in species
        assert "Ogerpon-Wellspring" in species
        assert "Tornadus" in species
        assert "Incineroar" in species

    def test_first_place_has_good_as_gold(self):
        """1st place uses Gholdengo with Good as Gold."""
        team = TEAM_1ST_MAX_MORALES
        gholdengo = next(p for p in team.pokemon if p.species == "Gholdengo")
        assert gholdengo.ability == "Good as Gold"
        assert "Nasty Plot" in gholdengo.moves

    def test_second_place_has_gouging_fire(self):
        """2nd place uses Gouging Fire (unique pick)."""
        team = TEAM_2ND_VICTOR_MANOATH
        species = [p.species for p in team.pokemon]
        assert "Gouging Fire" in species

        gouging_fire = next(p for p in team.pokemon if p.species == "Gouging Fire")
        assert gouging_fire.ability == "Protosynthesis"

    def test_second_place_has_landorus(self):
        """2nd place uses Landorus with Sheer Force."""
        team = TEAM_2ND_VICTOR_MANOATH
        landorus = next(p for p in team.pokemon if p.species == "Landorus")
        assert landorus.ability == "Sheer Force"
        assert landorus.item == "Life Orb"

    def test_third_place_has_pollen_puff(self):
        """3rd place uses Pollen Puff Amoonguss for healing."""
        team = TEAM_3RD_DAVID_ISRAEL_SOTO
        amoonguss = next(p for p in team.pokemon if p.species == "Amoonguss")
        assert "Pollen Puff" in amoonguss.moves

    def test_fourth_place_has_mental_herb(self):
        """4th place uses Mental Herb on Amoonguss."""
        team = TEAM_4TH_KENNETH_GAMBOA
        amoonguss = next(p for p in team.pokemon if p.species == "Amoonguss")
        assert amoonguss.item == "Mental Herb"


# =============================================================================
# Tournament Model Integration Tests
# =============================================================================

class TestTournament416Model:
    """Tests for tournament 416 model integration."""

    def test_tournament_created(self, tournament_416):
        """Tournament is created with correct metadata."""
        assert tournament_416.id == "416"
        assert tournament_416.name == "Regional Merida"
        assert tournament_416.metadata["format"] == "Scarlet & Violet Regulation F"
        assert tournament_416.metadata["player_count"] == 234

    def test_all_players_registered(self, tournament_416):
        """All 4 players are registered."""
        assert len(tournament_416.players) == 4

    def test_all_teams_registered(self, tournament_416):
        """All 4 teams are registered."""
        assert len(tournament_416.teams) == 4

    def test_player_team_association(self, tournament_416):
        """Each player is associated with their team."""
        for player in tournament_416.players.values():
            team = tournament_416.get_player_team(player.id)
            assert team is not None
            assert len(team.pokemon) == 6

    def test_first_place_player(self, tournament_416):
        """1st place player data is correct."""
        player = tournament_416.players.get("max_morales")
        assert player is not None
        assert player.name == "Max Morales"
        assert player.metadata["placement"] == "1st Place"


# =============================================================================
# Pokemon Species Coverage Tests
# =============================================================================

class TestTournament416SpeciesCoverage:
    """Test the variety of Pokemon used in tournament 416."""

    def test_unique_species_count(self):
        """Count unique species across all teams."""
        all_species = set()
        for team in TOURNAMENT_416_TEAMS:
            for poke in team.pokemon:
                all_species.add(poke.species)

        assert len(all_species) >= 10, f"Only {len(all_species)} unique species"

    def test_ursaluna_dominance(self):
        """Ursaluna appears on most teams."""
        ursaluna_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.species == "Ursaluna"
        )
        assert ursaluna_count >= 3, "Ursaluna is dominant in Merida"

    def test_incineroar_prevalence(self):
        """Incineroar appears on most teams."""
        incineroar_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.species == "Incineroar"
        )
        assert incineroar_count >= 3, "Incineroar on most top teams"

    def test_tornadus_prevalence(self):
        """Tornadus appears on multiple teams."""
        tornadus_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.species == "Tornadus"
        )
        assert tornadus_count >= 3

    def test_porygon2_trick_room_setter(self):
        """Porygon2 is used as Trick Room setter."""
        porygon2_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.species == "Porygon2"
        )
        assert porygon2_count >= 3


# =============================================================================
# Item and Ability Coverage Tests
# =============================================================================

class TestTournament416ItemsAbilities:
    """Test item and ability variety in tournament 416."""

    def test_eviolite_porygon2(self):
        """Eviolite Porygon2 is standard."""
        eviolite_p2_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if p.species == "Porygon2" and p.item == "Eviolite"
        )
        assert eviolite_p2_count >= 3

    def test_flame_orb_guts(self):
        """Flame Orb + Guts combo on Ursaluna."""
        guts_orb_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if p.ability == "Guts" and p.item == "Flame Orb"
        )
        assert guts_orb_count >= 3

    def test_prankster_usage(self):
        """Prankster is used for speed control."""
        prankster_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.ability == "Prankster"
        )
        assert prankster_count >= 3

    def test_intimidate_usage(self):
        """Intimidate is on most teams."""
        intimidate_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.ability == "Intimidate"
        )
        assert intimidate_count >= 3, "Intimidate is common in the meta"

    def test_good_as_gold_usage(self):
        """Good as Gold Gholdengo is present."""
        gag_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.ability == "Good as Gold"
        )
        assert gag_count >= 2


# =============================================================================
# Move Coverage Tests
# =============================================================================

class TestTournament416Moves:
    """Test move variety and strategy in tournament 416."""

    def test_trick_room_prevalence(self):
        """Trick Room is on most teams."""
        tr_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if "Trick Room" in p.moves
        )
        assert tr_count >= 3, "Trick Room dominant in Merida"

    def test_tailwind_presence(self):
        """Tailwind is also present."""
        tailwind_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if "Tailwind" in p.moves
        )
        assert tailwind_count >= 3

    def test_rain_dance_support(self):
        """Rain Dance is used on Tornadus."""
        rain_dance_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if "Rain Dance" in p.moves
        )
        assert rain_dance_count >= 3

    def test_spore_presence(self):
        """Spore is present for sleep support."""
        spore_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if "Spore" in p.moves
        )
        assert spore_count >= 2

    def test_follow_me_redirection(self):
        """Follow Me is used for redirection."""
        follow_me_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if "Follow Me" in p.moves
        )
        assert follow_me_count >= 2

    def test_nasty_plot_setup(self):
        """Nasty Plot is used for special attack setup."""
        nasty_plot_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if "Nasty Plot" in p.moves
        )
        assert nasty_plot_count >= 2


# =============================================================================
# Tera Type Strategy Tests
# =============================================================================

class TestTournament416TeraTypes:
    """Test Tera type distribution and strategy."""

    def test_steel_tera_dominance(self):
        """Steel tera is very common (defensive)."""
        steel_tera_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.tera_type == "Steel"
        )
        assert steel_tera_count >= 3

    def test_grass_tera_for_incineroar(self):
        """Grass tera is common on Incineroar."""
        grass_tera_incin = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if p.species == "Incineroar" and p.tera_type == "Grass"
        )
        assert grass_tera_incin >= 3

    def test_ghost_tera_for_ursaluna(self):
        """Ghost tera is used on Ursaluna."""
        ghost_tera_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if p.species == "Ursaluna" and p.tera_type == "Ghost"
        )
        assert ghost_tera_count >= 2

    def test_flying_tera_for_porygon2(self):
        """Flying tera on Porygon2 for Ground immunity."""
        flying_p2 = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if p.species == "Porygon2" and p.tera_type == "Flying"
        )
        assert flying_p2 >= 3


# =============================================================================
# Team Archetype Tests
# =============================================================================

class TestTournament416TeamArchetypes:
    """Analyze team archetypes from tournament 416."""

    def test_trick_room_meta(self):
        """Trick Room is the dominant archetype."""
        tr_teams = 0
        for team in TOURNAMENT_416_TEAMS:
            moves_flat = [m for p in team.pokemon for m in p.moves]
            species = [p.species for p in team.pokemon]
            if "Trick Room" in moves_flat and "Ursaluna" in species:
                tr_teams += 1

        assert tr_teams >= 3, "Trick Room is dominant in Merida"

    def test_dual_speed_control(self):
        """Teams have both Trick Room and Tailwind."""
        dual_control_teams = 0
        for team in TOURNAMENT_416_TEAMS:
            moves_flat = [m for p in team.pokemon for m in p.moves]
            has_tr = "Trick Room" in moves_flat
            has_tw = "Tailwind" in moves_flat
            if has_tr and has_tw:
                dual_control_teams += 1

        assert dual_control_teams >= 2

    def test_wellspring_ogerpon_usage(self):
        """Wellspring Ogerpon is used for Follow Me support."""
        wellspring_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if p.species == "Ogerpon-Wellspring"
        )
        assert wellspring_count >= 2


# =============================================================================
# Unique Strategies Tests
# =============================================================================

class TestTournament416UniqueStrategies:
    """Test unique strategies present in tournament 416."""

    def test_gouging_fire_unique(self):
        """Gouging Fire is a unique pick in this tournament."""
        gouging_fire_teams = []
        for team in TOURNAMENT_416_TEAMS:
            for p in team.pokemon:
                if p.species == "Gouging Fire":
                    gouging_fire_teams.append(team.player_name)
        assert len(gouging_fire_teams) >= 1

    def test_metal_coat_gholdengo(self):
        """Metal Coat Gholdengo instead of Choice Specs."""
        metal_coat_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if p.species == "Gholdengo" and p.item == "Metal Coat"
        )
        assert metal_coat_count >= 2

    def test_sandsear_storm_landorus(self):
        """Sandsear Storm is used on Landorus."""
        sandsear_users = []
        for team in TOURNAMENT_416_TEAMS:
            for p in team.pokemon:
                if "Sandsear Storm" in p.moves:
                    sandsear_users.append(p.species)
        assert len(sandsear_users) >= 1

    def test_sky_plate_tornadus(self):
        """Sky Plate Tornadus for boosted Flying STAB."""
        sky_plate_count = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if p.species == "Tornadus" and p.item == "Sky Plate"
        )
        assert sky_plate_count >= 1


# =============================================================================
# Regional Meta Analysis Tests
# =============================================================================

class TestTournament416MetaAnalysis:
    """Analyze the regional meta patterns from tournament 416."""

    def test_core_pokemon_presence(self):
        """Core Pokemon appear on most teams."""
        core_pokemon = {"Incineroar", "Ursaluna", "Tornadus", "Porygon2"}
        for core in core_pokemon:
            count = sum(
                1 for team in TOURNAMENT_416_TEAMS
                for p in team.pokemon if p.species == core
            )
            assert count >= 3, f"{core} should be on most teams"

    def test_ogerpon_form_preference(self):
        """Wellspring is the preferred Ogerpon form."""
        wellspring = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon if "Wellspring" in p.species
        )
        other_ogerpon = sum(
            1 for team in TOURNAMENT_416_TEAMS
            for p in team.pokemon
            if "Ogerpon" in p.species and "Wellspring" not in p.species
        )
        assert wellspring >= other_ogerpon


# =============================================================================
# Battle Simulation Tests
# =============================================================================

class TestTournament416BattleSimulation:
    """Tests that simulate battles between tournament 416 teams.

    Note: These tests require species name -> ID resolution to be implemented.
    Currently skipped because tournament teams use string species names
    while the battle simulator expects integer species IDs.
    """

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_finals_matchup(self, tournament_416):
        """Simulate the finals matchup (1st vs 2nd place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        match = Match(
            id="finals",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="max_morales",
            player2_id="victor_manoath",
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
            tournament_416,
            regulation,
            config.__dict__,
            base_seed=42,
        )

        assert result.completed
        assert result.winner_id in ["max_morales", "victor_manoath"]

    @pytest.mark.skip(reason="Requires species name resolution (teams use string names, simulator needs IDs)")
    def test_can_simulate_semifinal_matchup(self, tournament_416):
        """Simulate semifinal matchup (3rd vs 4th place)."""
        from tournament.runner import simulate_match, TournamentConfig
        from tournament.regulation import Regulation
        from tournament.model import Match, TournamentPhase

        match = Match(
            id="semifinal",
            round_number=1,
            phase=TournamentPhase.TOP_CUT,
            player1_id="david_israel_soto",
            player2_id="kenneth_gamboa",
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
            tournament_416,
            regulation,
            config.__dict__,
            base_seed=123,
        )

        assert result.completed
        assert result.winner_id in ["david_israel_soto", "kenneth_gamboa"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
