"""Tests for core/pokemon.py - Pokemon class and stat calculations.

Tests cover:
- HP calculation formula
- Stat calculation formula with nature modifiers
- calculate_all_stats function
- Pokemon class creation and property accessors
- Pokemon stat stages and modification
- Pokemon damage/healing mechanics
"""
import pytest
import numpy as np

from core.pokemon import (
    calculate_hp,
    calculate_stat,
    calculate_all_stats,
    Pokemon,
)
from core.layout import (
    POKEMON_ARRAY_SIZE,
    P_SPECIES, P_LEVEL, P_NATURE, P_CURRENT_HP,
    P_STAT_HP, P_STAT_ATK, P_STAT_SPE,
    P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE,
    STATUS_NONE, STATUS_BURN, STATUS_PARALYSIS,
)
from data.species import get_species
from data.natures import Nature


class TestCalculateHP:
    """Tests for HP calculation formula."""

    def test_hp_formula_lv100_max_ivs_no_evs(self):
        """HP at level 100 with 31 IVs and 0 EVs."""
        # Formula: floor(((2*Base + IV + EV/4) * Level) / 100) + Level + 10
        # With Base=100, IV=31, EV=0, Level=100:
        # = floor(((2*100 + 31 + 0) * 100) / 100) + 100 + 10
        # = floor(231) + 110 = 341
        hp = calculate_hp(base=100, iv=31, ev=0, level=100)
        assert hp == 341

    def test_hp_formula_lv100_max_ivs_max_evs(self):
        """HP at level 100 with 31 IVs and 252 EVs."""
        # = floor(((2*100 + 31 + 63) * 100) / 100) + 100 + 10
        # = floor(294) + 110 = 404
        hp = calculate_hp(base=100, iv=31, ev=252, level=100)
        assert hp == 404

    def test_hp_formula_lv50(self):
        """HP at level 50."""
        # = floor(((2*100 + 31 + 0) * 50) / 100) + 50 + 10
        # = floor(115.5) + 60 = 175
        hp = calculate_hp(base=100, iv=31, ev=0, level=50)
        assert hp == 175

    def test_hp_formula_lv1(self):
        """HP at level 1."""
        # = floor(((2*100 + 31 + 0) * 1) / 100) + 1 + 10
        # = floor(2.31) + 11 = 13
        hp = calculate_hp(base=100, iv=31, ev=0, level=1)
        assert hp == 13

    def test_hp_shedinja_special_case(self):
        """Shedinja always has 1 HP regardless of formula."""
        hp = calculate_hp(base=1, iv=31, ev=252, level=100)
        assert hp == 1

    def test_hp_blissey_high_base(self):
        """Blissey with base HP 255 has very high HP."""
        # = floor(((2*255 + 31 + 63) * 100) / 100) + 100 + 10
        # = floor(604) + 110 = 714
        hp = calculate_hp(base=255, iv=31, ev=252, level=100)
        assert hp == 714

    def test_hp_pikachu(self):
        """Pikachu HP calculation at level 100."""
        # Base HP: 35
        # = floor(((2*35 + 31 + 0) * 100) / 100) + 100 + 10
        # = 101 + 110 = 211
        hp = calculate_hp(base=35, iv=31, ev=0, level=100)
        assert hp == 211


class TestCalculateStat:
    """Tests for non-HP stat calculation formula."""

    def test_stat_formula_neutral_nature(self):
        """Stat at level 100 with neutral nature (1.0x)."""
        # Formula: floor((floor(((2*Base + IV + EV/4) * Level) / 100) + 5) * Nature)
        # With Base=100, IV=31, EV=0, Level=100, Nature=1.0:
        # = floor((floor(231) + 5) * 1.0) = 236
        stat = calculate_stat(base=100, iv=31, ev=0, level=100, nature_multiplier=1.0)
        assert stat == 236

    def test_stat_formula_boosting_nature(self):
        """Stat with boosting nature (+10%, 1.1x)."""
        # = floor((231 + 5) * 1.1) = floor(259.6) = 259
        stat = calculate_stat(base=100, iv=31, ev=0, level=100, nature_multiplier=1.1)
        assert stat == 259

    def test_stat_formula_hindering_nature(self):
        """Stat with hindering nature (-10%, 0.9x)."""
        # = floor((231 + 5) * 0.9) = floor(212.4) = 212
        stat = calculate_stat(base=100, iv=31, ev=0, level=100, nature_multiplier=0.9)
        assert stat == 212

    def test_stat_with_evs(self):
        """Stat with EVs investment."""
        # = floor(((2*100 + 31 + 63) * 100) / 100) + 5 = 294 + 5 = 299
        stat = calculate_stat(base=100, iv=31, ev=252, level=100, nature_multiplier=1.0)
        assert stat == 299

    def test_stat_lv50(self):
        """Stat at level 50."""
        # = floor(((2*100 + 31 + 0) * 50) / 100) + 5 = 115 + 5 = 120
        stat = calculate_stat(base=100, iv=31, ev=0, level=50, nature_multiplier=1.0)
        assert stat == 120

    def test_speed_base_102_adamant(self):
        """Garchomp's speed with Adamant nature (neutral for speed)."""
        # Base Speed: 102
        # = floor(((2*102 + 31 + 0) * 100) / 100) + 5 = 235 + 5 = 240
        stat = calculate_stat(base=102, iv=31, ev=0, level=100, nature_multiplier=1.0)
        assert stat == 240

    def test_attack_base_130_adamant(self):
        """Garchomp's attack with Adamant nature (+Atk)."""
        # Raw = floor(((2*130 + 31 + 0) * 100) / 100) + 5 = 291 + 5 = 296
        # = floor(296 * 1.1) = floor(325.6) = 325
        stat = calculate_stat(base=130, iv=31, ev=0, level=100, nature_multiplier=1.1)
        assert stat == 325


class TestCalculateAllStats:
    """Tests for calculate_all_stats function."""

    def test_all_stats_neutral_nature(self):
        """All stats with Hardy (neutral) nature."""
        base_stats = (100, 100, 100, 100, 100, 100)
        ivs = (31, 31, 31, 31, 31, 31)
        evs = (0, 0, 0, 0, 0, 0)

        stats = calculate_all_stats(base_stats, ivs, evs, level=100, nature=Nature.HARDY)

        assert stats[0] == 341  # HP
        assert stats[1] == 236  # Atk
        assert stats[2] == 236  # Def
        assert stats[3] == 236  # SpA
        assert stats[4] == 236  # SpD
        assert stats[5] == 236  # Spe

    def test_all_stats_adamant_nature(self):
        """All stats with Adamant (+Atk, -SpA) nature."""
        base_stats = (100, 100, 100, 100, 100, 100)
        ivs = (31, 31, 31, 31, 31, 31)
        evs = (0, 0, 0, 0, 0, 0)

        stats = calculate_all_stats(base_stats, ivs, evs, level=100, nature=Nature.ADAMANT)

        assert stats[0] == 341  # HP (unaffected)
        assert stats[1] == 259  # Atk (+10%)
        assert stats[2] == 236  # Def (neutral)
        assert stats[3] == 212  # SpA (-10%)
        assert stats[4] == 236  # SpD (neutral)
        assert stats[5] == 236  # Spe (neutral)

    def test_all_stats_timid_nature(self):
        """All stats with Timid (+Spe, -Atk) nature."""
        base_stats = (100, 100, 100, 100, 100, 100)
        ivs = (31, 31, 31, 31, 31, 31)
        evs = (0, 0, 0, 0, 0, 0)

        stats = calculate_all_stats(base_stats, ivs, evs, level=100, nature=Nature.TIMID)

        assert stats[0] == 341  # HP
        assert stats[1] == 212  # Atk (-10%)
        assert stats[5] == 259  # Spe (+10%)

    def test_pikachu_stats(self):
        """Pikachu stats at level 100 with perfect IVs."""
        pikachu = get_species(25)
        base_stats = pikachu.base_stats.as_tuple()
        ivs = (31, 31, 31, 31, 31, 31)
        evs = (0, 0, 0, 0, 0, 0)

        stats = calculate_all_stats(base_stats, ivs, evs, level=100, nature=Nature.HARDY)

        assert stats[0] == 211  # HP
        assert stats[5] == 216  # Speed (base 90)


class TestPokemonClass:
    """Tests for the Pokemon class."""

    def test_create_empty_pokemon(self):
        """Pokemon can be created with empty data array."""
        poke = Pokemon()
        assert poke.data.shape == (POKEMON_ARRAY_SIZE,)
        assert poke.data.dtype == np.int32

    def test_create_from_existing_array(self):
        """Pokemon can be created from existing NumPy array."""
        data = np.zeros(POKEMON_ARRAY_SIZE, dtype=np.int32)
        data[P_SPECIES] = 25
        data[P_LEVEL] = 50

        poke = Pokemon(data)
        assert poke.species_id == 25
        assert poke.level == 50

    def test_create_from_species(self):
        """Pokemon.from_species creates correct Pokemon."""
        pikachu_species = get_species(25)
        poke = Pokemon.from_species(pikachu_species, level=100)

        assert poke.species_id == 25
        assert poke.level == 100
        assert poke.max_hp == 211
        assert poke.current_hp == 211

    def test_from_species_with_nature(self):
        """Pokemon.from_species applies nature correctly."""
        species = get_species(25)

        # Adamant: +Atk, -SpA
        poke_adamant = Pokemon.from_species(species, level=100, nature=Nature.ADAMANT)

        # Modest: +SpA, -Atk
        poke_modest = Pokemon.from_species(species, level=100, nature=Nature.MODEST)

        assert poke_adamant.attack > poke_modest.attack
        assert poke_adamant.special_attack < poke_modest.special_attack

    def test_from_species_with_evs(self):
        """Pokemon.from_species applies EVs correctly."""
        species = get_species(25)

        poke_no_evs = Pokemon.from_species(species, level=100, evs=(0, 0, 0, 0, 0, 0))
        poke_spe_evs = Pokemon.from_species(species, level=100, evs=(0, 0, 0, 0, 0, 252))

        assert poke_spe_evs.speed > poke_no_evs.speed

    def test_from_species_with_ivs(self):
        """Pokemon.from_species applies IVs correctly."""
        species = get_species(25)

        poke_max_ivs = Pokemon.from_species(species, level=100, ivs=(31, 31, 31, 31, 31, 31))
        poke_no_ivs = Pokemon.from_species(species, level=100, ivs=(0, 0, 0, 0, 0, 0))

        assert poke_max_ivs.max_hp > poke_no_ivs.max_hp
        assert poke_max_ivs.attack > poke_no_ivs.attack


class TestPokemonProperties:
    """Tests for Pokemon property accessors."""

    def test_type_properties(self):
        """Pokemon has correct type properties."""
        charizard = get_species(6)
        poke = Pokemon.from_species(charizard)

        from data.types import Type
        assert poke.type1 == Type.FIRE.value
        assert poke.type2 == Type.FLYING.value

    def test_single_type_pokemon(self):
        """Single-typed Pokemon has type2 as -1."""
        pikachu = get_species(25)
        poke = Pokemon.from_species(pikachu)

        assert poke.type2 == -1

    def test_hp_fraction(self):
        """hp_fraction returns correct ratio."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        assert poke.hp_fraction == 1.0

        poke.current_hp = poke.max_hp // 2
        assert 0.45 < poke.hp_fraction < 0.55

    def test_hp_fraction_zero_max_hp(self):
        """hp_fraction returns 0.0 when max_hp is 0."""
        poke = Pokemon()  # Empty pokemon with 0 stats
        # Max HP is 0 for empty pokemon
        assert poke.max_hp == 0
        assert poke.hp_fraction == 0.0

    def test_is_fainted(self):
        """is_fainted returns correct state."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        assert not poke.is_fainted

        poke.current_hp = 0
        assert poke.is_fainted

    def test_stat_accessors(self):
        """All stat accessors return correct values."""
        species = get_species(445)  # Garchomp
        poke = Pokemon.from_species(species, level=100, nature=Nature.JOLLY)

        # Jolly: +Spe, -SpA
        assert poke.max_hp > 0
        assert poke.attack > 0
        assert poke.defense > 0
        assert poke.special_attack > 0
        assert poke.special_defense > 0
        assert poke.speed > 0

    def test_moves_property(self):
        """moves property returns all four move IDs."""
        species = get_species(25)
        poke = Pokemon.from_species(species, moves=[100, 200, 300, 400])

        assert poke.moves == (100, 200, 300, 400)

    def test_ivs_property(self):
        """ivs property returns all IVs."""
        species = get_species(25)
        poke = Pokemon.from_species(species, ivs=(31, 30, 29, 28, 27, 26))

        ivs = poke.ivs
        assert ivs == (31, 30, 29, 28, 27, 26)

    def test_evs_property(self):
        """evs property returns all EVs."""
        species = get_species(25)
        poke = Pokemon.from_species(species, evs=(4, 252, 0, 0, 0, 252))

        evs = poke.evs
        assert evs == (4, 252, 0, 0, 0, 252)

    def test_nature_id_property(self):
        """nature_id property returns correct nature ID."""
        species = get_species(25)
        poke = Pokemon.from_species(species, nature=Nature.ADAMANT)

        # Adamant is nature ID 3
        assert poke.nature_id == Nature.ADAMANT.value

    def test_ability_id_property(self):
        """ability_id property returns correct ability ID."""
        species = get_species(25)
        poke = Pokemon.from_species(species, ability_id=1)

        assert poke.ability_id == 1

    def test_item_id_property(self):
        """item_id property returns correct item ID."""
        species = get_species(25)
        poke = Pokemon.from_species(species, item_id=100)

        assert poke.item_id == 100

    def test_get_stat_method(self):
        """get_stat method returns stat by index."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        # Get HP stat
        hp_stat = poke.get_stat(P_STAT_HP)
        assert hp_stat == poke.max_hp

        # Get Attack stat
        atk_stat = poke.get_stat(P_STAT_ATK)
        assert atk_stat == poke.attack

    def test_get_pp_invalid_slot(self):
        """get_pp returns 0 for invalid slot."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        # Invalid slot should return 0
        assert poke.get_pp(-1) == 0
        assert poke.get_pp(4) == 0
        assert poke.get_pp(10) == 0


class TestPokemonStatus:
    """Tests for Pokemon status conditions."""

    def test_default_status_none(self):
        """Pokemon starts with no status."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        assert poke.status == STATUS_NONE

    def test_set_status(self):
        """Status can be set."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.status = STATUS_BURN
        assert poke.status == STATUS_BURN

        poke.status = STATUS_PARALYSIS
        assert poke.status == STATUS_PARALYSIS

    def test_status_counter(self):
        """Status counter can be set and read."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.status_counter = 3
        assert poke.status_counter == 3


class TestPokemonStages:
    """Tests for stat stage modification."""

    def test_initial_stages_zero(self):
        """All stages start at 0."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        assert poke.get_stage(P_STAGE_ATK) == 0
        assert poke.get_stage(P_STAGE_DEF) == 0
        assert poke.get_stage(P_STAGE_SPA) == 0
        assert poke.get_stage(P_STAGE_SPD) == 0
        assert poke.get_stage(P_STAGE_SPE) == 0

    def test_set_stage(self):
        """set_stage sets stage value."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.set_stage(P_STAGE_ATK, 2)
        assert poke.get_stage(P_STAGE_ATK) == 2

    def test_set_stage_clamped_max(self):
        """set_stage clamps to +6."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.set_stage(P_STAGE_ATK, 10)
        assert poke.get_stage(P_STAGE_ATK) == 6

    def test_set_stage_clamped_min(self):
        """set_stage clamps to -6."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.set_stage(P_STAGE_ATK, -10)
        assert poke.get_stage(P_STAGE_ATK) == -6

    def test_modify_stage(self):
        """modify_stage changes stage and returns actual change."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        change = poke.modify_stage(P_STAGE_ATK, 2)
        assert change == 2
        assert poke.get_stage(P_STAGE_ATK) == 2

    def test_modify_stage_clamped(self):
        """modify_stage returns actual change when clamped."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.set_stage(P_STAGE_ATK, 5)
        change = poke.modify_stage(P_STAGE_ATK, 3)

        assert change == 1  # Only +1 because clamped at +6
        assert poke.get_stage(P_STAGE_ATK) == 6

    def test_reset_stages(self):
        """reset_stages sets all stages to 0."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.set_stage(P_STAGE_ATK, 3)
        poke.set_stage(P_STAGE_DEF, -2)
        poke.set_stage(P_STAGE_SPE, 6)

        poke.reset_stages()

        assert poke.get_stage(P_STAGE_ATK) == 0
        assert poke.get_stage(P_STAGE_DEF) == 0
        assert poke.get_stage(P_STAGE_SPE) == 0


class TestPokemonMoves:
    """Tests for Pokemon move and PP management."""

    def test_get_move(self):
        """get_move returns move ID in slot."""
        species = get_species(25)
        poke = Pokemon.from_species(species, moves=[100, 200, 300, 400])

        assert poke.get_move(0) == 100
        assert poke.get_move(1) == 200
        assert poke.get_move(2) == 300
        assert poke.get_move(3) == 400

    def test_get_move_invalid_slot(self):
        """get_move returns 0 for invalid slot."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        assert poke.get_move(5) == 0
        assert poke.get_move(-1) == 0

    def test_set_pp(self):
        """set_pp sets PP for a slot."""
        species = get_species(25)
        poke = Pokemon.from_species(species, moves=[100])

        poke.set_pp(0, 35)
        assert poke.get_pp(0) == 35

    def test_use_pp(self):
        """use_pp decreases PP and returns success."""
        species = get_species(25)
        poke = Pokemon.from_species(species, moves=[100], move_pp=[35])

        success = poke.use_pp(0, 1)
        assert success
        assert poke.get_pp(0) == 34

    def test_use_pp_insufficient(self):
        """use_pp returns False if not enough PP."""
        species = get_species(25)
        poke = Pokemon.from_species(species, moves=[100], move_pp=[1])

        success = poke.use_pp(0, 5)
        assert not success
        assert poke.get_pp(0) == 1  # Unchanged


class TestPokemonDamageHealing:
    """Tests for damage and healing mechanics."""

    def test_take_damage(self):
        """take_damage reduces HP and returns actual damage."""
        species = get_species(25)
        poke = Pokemon.from_species(species)
        initial_hp = poke.current_hp

        actual = poke.take_damage(50)

        assert actual == 50
        assert poke.current_hp == initial_hp - 50

    def test_take_damage_overkill(self):
        """take_damage handles overkill correctly."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        poke.current_hp = 30
        actual = poke.take_damage(100)

        assert actual == 30
        assert poke.current_hp == 0

    def test_take_damage_zero(self):
        """take_damage with 0 does nothing."""
        species = get_species(25)
        poke = Pokemon.from_species(species)
        initial_hp = poke.current_hp

        actual = poke.take_damage(0)

        assert actual == 0
        assert poke.current_hp == initial_hp

    def test_heal(self):
        """heal restores HP and returns actual healing."""
        species = get_species(25)
        poke = Pokemon.from_species(species)
        poke.current_hp = 100

        actual = poke.heal(50)

        assert actual == 50
        assert poke.current_hp == 150

    def test_heal_overheal(self):
        """heal caps at max HP."""
        species = get_species(25)
        poke = Pokemon.from_species(species)
        max_hp = poke.max_hp
        poke.current_hp = max_hp - 10

        actual = poke.heal(100)

        assert actual == 10
        assert poke.current_hp == max_hp

    def test_heal_zero(self):
        """heal with 0 does nothing."""
        species = get_species(25)
        poke = Pokemon.from_species(species)
        poke.current_hp = 100

        actual = poke.heal(0)

        assert actual == 0
        assert poke.current_hp == 100


class TestPokemonCopy:
    """Tests for Pokemon copying."""

    def test_copy_creates_independent_pokemon(self):
        """copy() creates independent Pokemon."""
        species = get_species(25)
        poke = Pokemon.from_species(species)

        copy = poke.copy()

        # Modify original
        poke.current_hp = 50

        # Copy should be unchanged
        assert copy.current_hp == copy.max_hp

    def test_copy_preserves_all_data(self):
        """copy() preserves all Pokemon data."""
        species = get_species(25)
        poke = Pokemon.from_species(
            species,
            level=50,
            nature=Nature.ADAMANT,
            moves=[100, 200, 300, 400],
            move_pp=[35, 30, 25, 20],
        )
        poke.current_hp = 100
        poke.set_stage(P_STAGE_ATK, 2)

        copy = poke.copy()

        assert copy.level == 50
        assert copy.current_hp == 100
        assert copy.get_stage(P_STAGE_ATK) == 2
        assert copy.moves == (100, 200, 300, 400)


class TestPokemonRepr:
    """Tests for Pokemon string representation."""

    def test_repr_basic(self):
        """repr shows species, level, and HP."""
        species = get_species(25)
        poke = Pokemon.from_species(species, level=50)

        repr_str = repr(poke)

        assert "species=25" in repr_str
        assert "lv=50" in repr_str
        assert "hp=" in repr_str
