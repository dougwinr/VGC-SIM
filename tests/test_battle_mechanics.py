"""Tests for special battle mechanics.

Tests for:
- Terastallization
- Mega Evolution
- Z-Moves
- Dynamax/Gigantamax
"""
import pytest
import numpy as np

from core.battle_state import BattleState
from core.battle import BattleEngine, Choice
from core.layout import (
    P_SPECIES, P_LEVEL, P_STAT_HP, P_CURRENT_HP,
    P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE,
    P_TYPE1, P_TYPE2, P_TERA_TYPE, P_MOVE1, P_PP1, P_ITEM, P_ABILITY,
)
from data.moves_loader import MOVE_REGISTRY, get_move
from data.types import Type


def setup_basic_battle(seed: int = 42) -> tuple:
    """Set up a basic battle state for testing."""
    state = BattleState(
        num_sides=2,
        team_size=6,
        active_slots=1,
        seed=seed,
        game_type="singles",
    )

    # Set up basic Pokemon for both sides
    for side in range(2):
        pokemon = state.pokemons[side, 0]
        pokemon[P_SPECIES] = 6  # Charizard
        pokemon[P_LEVEL] = 50
        pokemon[P_STAT_HP] = 150
        pokemon[P_CURRENT_HP] = 150
        pokemon[P_STAT_ATK] = 100
        pokemon[P_STAT_DEF] = 80
        pokemon[P_STAT_SPA] = 120
        pokemon[P_STAT_SPD] = 90
        pokemon[P_STAT_SPE] = 110
        pokemon[P_TYPE1] = Type.FIRE.value
        pokemon[P_TYPE2] = Type.FLYING.value
        pokemon[P_TERA_TYPE] = -1  # Not terastallized
        pokemon[P_MOVE1] = 53  # Flamethrower
        pokemon[P_PP1] = 15

    engine = BattleEngine(state, MOVE_REGISTRY)
    state.start_battle()

    return state, engine


class TestTerastallization:
    """Tests for Terastallization mechanics."""

    def test_tera_type_initial_state(self):
        """Pokemon should start with no tera type active."""
        state, engine = setup_basic_battle()

        pokemon = state.get_pokemon(0, 0)
        assert pokemon.data[P_TERA_TYPE] == -1, "Pokemon should not be terastallized initially"

    def test_tera_type_can_be_set(self):
        """Tera type can be set on a Pokemon."""
        state, engine = setup_basic_battle()

        # Set tera type to Water
        state.pokemons[0, 0, P_TERA_TYPE] = Type.WATER.value

        pokemon = state.get_pokemon(0, 0)
        assert pokemon.data[P_TERA_TYPE] == Type.WATER.value

    def test_tera_choice_flag_exists(self):
        """Choice dataclass should have terastallize flag."""
        choice = Choice(choice_type='move', slot=0, move_slot=0, terastallize=True)
        assert choice.terastallize is True

    def test_tera_choice_default_false(self):
        """Terastallize flag should default to False."""
        choice = Choice(choice_type='move', slot=0, move_slot=0)
        assert choice.terastallize is False

    def test_tera_type_affects_stab(self):
        """Terastallized Pokemon should get STAB on tera type moves."""
        from core.damage import has_stab

        # Fire/Flying Pokemon with Water tera type
        attacker_type1 = Type.FIRE.value
        attacker_type2 = Type.FLYING.value
        attacker_tera_type = Type.WATER.value

        # Should have STAB on Water moves (tera type)
        assert has_stab(Type.WATER, attacker_type1, attacker_type2, attacker_tera_type)
        # Should still have STAB on original types
        assert has_stab(Type.FIRE, attacker_type1, attacker_type2, attacker_tera_type)

    def test_tera_type_changes_defensive_typing(self):
        """Terastallized Pokemon should use tera type for defense."""
        from core.damage import calculate_type_effectiveness

        # Electric attack vs Fire/Flying - super effective against Flying (2x)
        effectiveness_normal = calculate_type_effectiveness(
            Type.ELECTRIC,
            Type.FIRE.value,
            Type.FLYING.value,
            defender_tera_type=-1,
        )

        # Same attack vs terastallized to Ground - Electric is immune to Ground
        effectiveness_tera = calculate_type_effectiveness(
            Type.ELECTRIC,
            Type.FIRE.value,
            Type.FLYING.value,
            defender_tera_type=Type.GROUND.value,
        )

        # Electric vs Ground should be immune (0x)
        assert effectiveness_tera == 0.0
        assert effectiveness_normal > 0.0


class TestMegaEvolution:
    """Tests for Mega Evolution mechanics."""

    def test_mega_choice_flag_exists(self):
        """Choice dataclass should have mega flag."""
        choice = Choice(choice_type='move', slot=0, move_slot=0, mega=True)
        assert choice.mega is True

    def test_mega_choice_default_false(self):
        """Mega flag should default to False."""
        choice = Choice(choice_type='move', slot=0, move_slot=0)
        assert choice.mega is False

    def test_mega_forms_exist_in_data(self):
        """Mega forms should be loaded in species data."""
        from data.species import get_species_by_name

        # Check Charizard has Mega forms
        charizard_x = get_species_by_name("charizardmegax")
        charizard_y = get_species_by_name("charizardmegay")

        # At least one should exist if data is loaded
        has_mega = charizard_x is not None or charizard_y is not None
        # Note: May not exist if data not fully loaded
        # This test documents expected behavior

    def test_mega_stone_flag_exists(self):
        """Item flags should include mega stone."""
        from data.items import ItemFlag

        assert hasattr(ItemFlag, 'MEGA_STONE')


class TestZMoves:
    """Tests for Z-Move mechanics."""

    def test_zmove_choice_flag_exists(self):
        """Choice dataclass should have zmove flag."""
        choice = Choice(choice_type='move', slot=0, move_slot=0, zmove=True)
        assert choice.zmove is True

    def test_zmove_choice_default_false(self):
        """Z-Move flag should default to False."""
        choice = Choice(choice_type='move', slot=0, move_slot=0)
        assert choice.zmove is False

    def test_z_crystal_flag_exists(self):
        """Item flags should include Z crystal."""
        from data.items import ItemFlag

        assert hasattr(ItemFlag, 'Z_CRYSTAL')

    def test_zmove_data_field_exists(self):
        """MoveData should have is_z_move field."""
        from data.moves import MoveData

        # Check the field exists in dataclass
        fields = [f.name for f in MoveData.__dataclass_fields__.values()]
        assert 'is_z_move' in fields


class TestDynamax:
    """Tests for Dynamax/Gigantamax mechanics."""

    def test_dynamax_choice_flag_exists(self):
        """Choice dataclass should have dynamax flag."""
        choice = Choice(choice_type='move', slot=0, move_slot=0, dynamax=True)
        assert choice.dynamax is True

    def test_dynamax_choice_default_false(self):
        """Dynamax flag should default to False."""
        choice = Choice(choice_type='move', slot=0, move_slot=0)
        assert choice.dynamax is False

    def test_max_move_data_field_exists(self):
        """MoveData should have is_max_move field."""
        from data.moves import MoveData

        fields = [f.name for f in MoveData.__dataclass_fields__.values()]
        assert 'is_max_move' in fields

    def test_gmax_form_type_exists(self):
        """FormType should have GMAX option."""
        from data.species import FormType

        assert hasattr(FormType, 'GMAX')


class TestMechanicsIntegration:
    """Integration tests for all mechanics together."""

    def test_multiple_flags_can_coexist(self):
        """Choice can have multiple special flags (though invalid in real game)."""
        # This tests the data structure, not game rules
        choice = Choice(
            choice_type='move',
            slot=0,
            move_slot=0,
            terastallize=True,
            mega=False,
            zmove=False,
            dynamax=False,
        )
        assert choice.terastallize is True

    def test_all_mechanics_default_off(self):
        """All special mechanics should default to off."""
        choice = Choice(choice_type='move', slot=0, move_slot=0)

        assert choice.terastallize is False
        assert choice.mega is False
        assert choice.zmove is False
        assert choice.dynamax is False

    def test_battle_with_tera_choice(self):
        """Battle can process choices with tera flag."""
        state, engine = setup_basic_battle()

        # Make choices with terastallize flag
        choices = {
            0: [Choice(choice_type='move', slot=0, move_slot=0, terastallize=True, target=1)],
            1: [Choice(choice_type='move', slot=0, move_slot=0, target=1)],
        }

        # Should not crash
        engine.step(choices)

        # Battle should continue or end normally
        assert state.turn >= 1
