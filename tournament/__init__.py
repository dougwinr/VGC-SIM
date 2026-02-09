"""Tournament system for Pokemon battles.

This module provides:
- Tournament, Player, Team, Match, Standing models
- Regulation and team validation
- Swiss pairings algorithm
- Scoring and tiebreakers
- Tournament simulation runner
- pokedata.ovh tournament data loader
"""

from tournament.model import (
    Tournament,
    Division,
    Player,
    Team,
    Match,
    Standing,
    MatchResult,
    TournamentPhase,
)
from tournament.regulation import Regulation, validate_team
from tournament.pairings import generate_swiss_pairings
from tournament.scoring import ScoringProfile, calculate_standings
from tournament.runner import (
    simulate_match,
    simulate_tournament,
    create_random_team,
    TournamentConfig,
)
from tournament.pokedata_loader import (
    load_from_pokedata_html,
    load_from_pokedata_json,
    parse_pokedata_html,
    parse_pokedata_json,
    fetch_pokedata_raw,
    get_top_pokemon,
    get_top_items,
    get_pokemon_item_pairs,
    PlayerStanding,
    PokemonEntry,
)
from tournament.limitless_loader import (
    load_tournament as load_limitless_tournament,
    load_tournament_standings as load_limitless_standings,
    load_team as load_limitless_team,
    load_tournament_info as load_limitless_info,
    search_tournaments as search_limitless_tournaments,
    get_tournament_url as get_limitless_tournament_url,
    get_team_url as get_limitless_team_url,
    TournamentInfo as LimitlessTournamentInfo,
    TournamentStanding as LimitlessTournamentStanding,
    TeamData as LimitlessTeamData,
    PokemonData as LimitlessPokemonData,
)

__all__ = [
    # Models
    "Tournament",
    "Division",
    "Player",
    "Team",
    "Match",
    "Standing",
    "MatchResult",
    "TournamentPhase",
    # Regulation
    "Regulation",
    "validate_team",
    # Pairings
    "generate_swiss_pairings",
    # Scoring
    "ScoringProfile",
    "calculate_standings",
    # Runner
    "simulate_match",
    "simulate_tournament",
    "create_random_team",
    "TournamentConfig",
    # Pokedata loader
    "load_from_pokedata_html",
    "load_from_pokedata_json",
    "parse_pokedata_html",
    "parse_pokedata_json",
    "fetch_pokedata_raw",
    "get_top_pokemon",
    "get_top_items",
    "get_pokemon_item_pairs",
    "PlayerStanding",
    "PokemonEntry",
    # Limitless VGC loader
    "load_limitless_tournament",
    "load_limitless_standings",
    "load_limitless_team",
    "load_limitless_info",
    "search_limitless_tournaments",
    "get_limitless_tournament_url",
    "get_limitless_team_url",
    "LimitlessTournamentInfo",
    "LimitlessTournamentStanding",
    "LimitlessTeamData",
    "LimitlessPokemonData",
]
