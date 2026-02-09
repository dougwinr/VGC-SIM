"""Tests for the CLI module."""
import pytest

from cli.battle_cli import (
    BattleCLI,
    Formatter,
    Colors,
    get_pokemon_name,
    get_move_name,
    create_opponent,
)
from agents import RandomAgent, HeuristicAgent, DefensiveAgent, TypeMatchupAgent


class TestFormatter:
    """Tests for the Formatter class."""

    def test_formatter_with_color(self):
        """Test formatter with color enabled."""
        fmt = Formatter(use_color=True)

        bold_text = fmt.bold("test")
        assert Colors.BOLD in bold_text
        assert Colors.RESET in bold_text

    def test_formatter_without_color(self):
        """Test formatter with color disabled."""
        fmt = Formatter(use_color=False)

        bold_text = fmt.bold("test")
        assert Colors.BOLD not in bold_text
        assert bold_text == "test"

    def test_hp_bar(self):
        """Test HP bar generation."""
        fmt = Formatter(use_color=False)

        # Full HP
        bar = fmt.hp_bar(100, 100, width=10)
        assert "[" in bar
        assert "]" in bar

        # Half HP
        bar = fmt.hp_bar(50, 100, width=10)
        assert "█" in bar

        # Zero HP
        bar = fmt.hp_bar(0, 100, width=10)
        assert bar.count("░") == 10 or bar.count("█") == 0

    def test_status_text(self):
        """Test status formatting."""
        fmt = Formatter(use_color=False)

        from core.layout import STATUS_BURN, STATUS_NONE

        assert fmt.status_text(STATUS_NONE) == ""
        assert "BRN" in fmt.status_text(STATUS_BURN)


class TestDataHelpers:
    """Tests for data helper functions."""

    def test_get_pokemon_name(self):
        """Test getting Pokemon name from ID."""
        # Known species
        name = get_pokemon_name(6)
        assert "charizard" in name.lower()

        # Unknown species (should return placeholder)
        name = get_pokemon_name(99999)
        assert "Pokemon#" in name or "99999" in name

    def test_get_move_name(self):
        """Test getting move name from ID."""
        # Known move (Earthquake)
        name = get_move_name(89)
        assert "earthquake" in name.lower()

        # Empty move
        name = get_move_name(0)
        assert name == "---"


class TestOpponentCreation:
    """Tests for opponent agent creation."""

    def test_create_random_opponent(self):
        """Test creating random opponent."""
        opponent = create_opponent("random", seed=42)
        assert isinstance(opponent, RandomAgent)
        assert "Random" in opponent.name

    def test_create_heuristic_opponent(self):
        """Test creating heuristic opponent."""
        opponent = create_opponent("heuristic", seed=42)
        assert isinstance(opponent, HeuristicAgent)

    def test_create_defensive_opponent(self):
        """Test creating defensive opponent."""
        opponent = create_opponent("defensive", seed=42)
        assert isinstance(opponent, DefensiveAgent)

    def test_create_type_opponent(self):
        """Test creating type matchup opponent."""
        opponent = create_opponent("type", seed=42)
        assert isinstance(opponent, TypeMatchupAgent)


class TestBattleCLI:
    """Tests for BattleCLI class."""

    def test_cli_creation(self):
        """Test CLI creation."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
            use_color=False,
        )

        assert cli.opponent == opponent
        assert cli.game_type == "doubles"
        assert cli.seed == 42

    def test_cli_setup_battle(self):
        """Test battle setup."""
        opponent = RandomAgent(seed=42)
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
            use_color=False,
        )

        cli.setup_battle()

        # Check state is initialized
        assert cli.state is not None
        assert cli.engine is not None

        # Check teams were generated
        for side in range(2):
            for slot in range(cli.state.team_size):
                pokemon = cli.state.get_pokemon(side, slot)
                assert pokemon.max_hp > 0

    def test_cli_singles_format(self):
        """Test singles format setup."""
        opponent = RandomAgent()
        cli = BattleCLI(
            opponent=opponent,
            game_type="singles",
            seed=42,
        )

        cli.setup_battle()

        assert cli.state.active_slots == 1

    def test_cli_doubles_format(self):
        """Test doubles format setup."""
        opponent = RandomAgent()
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        assert cli.state.active_slots == 2

    def test_cli_get_legal_actions(self):
        """Test getting legal actions."""
        opponent = RandomAgent()
        cli = BattleCLI(
            opponent=opponent,
            game_type="doubles",
            seed=42,
        )

        cli.setup_battle()

        # Get legal actions for first active slot
        actions = cli.get_legal_actions(0)

        assert len(actions) > 0

        # Each action should have description
        for action, desc in actions:
            assert isinstance(desc, str)
            assert len(desc) > 0
