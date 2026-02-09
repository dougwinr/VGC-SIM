"""Tests for data/species_loader.py - Species data loading from TypeScript.

Tests cover:
- TypeScript parsing functions
- Type parsing helpers
- Form classification
- Gender ratio parsing
- Ability parsing
- Evolution data parsing
- Generation inference
- Tag parsing
- Full species loading from TS files
"""
import pytest

from data.species_loader import (
    _parse_type,
    _classify_form,
    _parse_gender_ratio,
    _parse_abilities,
    _parse_evolutions,
    _infer_generation,
    _parse_tags,
    _parse_ts_value,
    _parse_ts_object_simple,
    parse_ts_pokedex,
)
from data.species import FormType, EvolutionType
from data.types import Type


class TestParseType:
    """Tests for _parse_type helper function."""

    def test_parse_fire(self):
        """Should parse 'Fire' type correctly."""
        assert _parse_type("Fire") == Type.FIRE

    def test_parse_water(self):
        """Should parse 'Water' type correctly."""
        assert _parse_type("Water") == Type.WATER

    def test_parse_grass(self):
        """Should parse 'Grass' type correctly."""
        assert _parse_type("Grass") == Type.GRASS

    def test_parse_electric(self):
        """Should parse 'Electric' type correctly."""
        assert _parse_type("Electric") == Type.ELECTRIC

    def test_parse_dragon(self):
        """Should parse 'Dragon' type correctly."""
        assert _parse_type("Dragon") == Type.DRAGON

    def test_parse_fairy(self):
        """Should parse 'Fairy' type correctly."""
        assert _parse_type("Fairy") == Type.FAIRY

    def test_parse_case_insensitive(self):
        """Should handle various cases."""
        assert _parse_type("fire") == Type.FIRE
        assert _parse_type("FIRE") == Type.FIRE
        assert _parse_type("Fire") == Type.FIRE

    def test_parse_empty_returns_none(self):
        """Empty string should return None."""
        assert _parse_type("") is None

    def test_parse_none_returns_none(self):
        """Falsy input should return None."""
        assert _parse_type(None) is None

    def test_parse_invalid_returns_none(self):
        """Invalid type name should return None."""
        assert _parse_type("InvalidType") is None


class TestClassifyForm:
    """Tests for _classify_form helper function."""

    def test_classify_base_form(self):
        """Empty forme should be BASE."""
        assert _classify_form("", "Pikachu", None) == FormType.BASE
        assert _classify_form(None, "Pikachu", None) == FormType.BASE

    def test_classify_mega(self):
        """'Mega' forme should be MEGA."""
        assert _classify_form("Mega", "Venusaur-Mega", "Venusaur") == FormType.MEGA

    def test_classify_mega_x(self):
        """'Mega-X' forme should be MEGA_X."""
        assert _classify_form("Mega-X", "Charizard-Mega-X", "Charizard") == FormType.MEGA_X

    def test_classify_mega_y(self):
        """'Mega-Y' forme should be MEGA_Y."""
        assert _classify_form("Mega-Y", "Charizard-Mega-Y", "Charizard") == FormType.MEGA_Y

    def test_classify_primal(self):
        """'Primal' forme should be PRIMAL."""
        assert _classify_form("Primal", "Groudon-Primal", "Groudon") == FormType.PRIMAL

    def test_classify_alola(self):
        """'Alola' forme should be ALOLA."""
        assert _classify_form("Alola", "Vulpix-Alola", "Vulpix") == FormType.ALOLA

    def test_classify_galar(self):
        """'Galar' forme should be GALAR."""
        assert _classify_form("Galar", "Ponyta-Galar", "Ponyta") == FormType.GALAR

    def test_classify_hisui(self):
        """'Hisui' forme should be HISUI."""
        assert _classify_form("Hisui", "Growlithe-Hisui", "Growlithe") == FormType.HISUI

    def test_classify_paldea(self):
        """'Paldea' forme should be PALDEA."""
        assert _classify_form("Paldea", "Wooper-Paldea", "Wooper") == FormType.PALDEA

    def test_classify_gmax(self):
        """'Gmax' forme should be GMAX."""
        assert _classify_form("Gmax", "Charizard-Gmax", "Charizard") == FormType.GMAX

    def test_classify_totem(self):
        """'Totem' forme should be TOTEM."""
        assert _classify_form("Totem", "Raticate-Totem", "Raticate") == FormType.TOTEM

    def test_classify_partial_match(self):
        """Partial matches in forme should work."""
        assert _classify_form("Alola-Totem", "Raticate-Alola-Totem", "Raticate") == FormType.ALOLA

    def test_classify_other(self):
        """Unknown formes should be OTHER."""
        assert _classify_form("Origin", "Giratina-Origin", "Giratina") == FormType.OTHER
        assert _classify_form("Sky", "Shaymin-Sky", "Shaymin") == FormType.OTHER


class TestParseGenderRatio:
    """Tests for _parse_gender_ratio helper function."""

    def test_genderless(self):
        """Gender 'N' should return None (genderless)."""
        assert _parse_gender_ratio({"gender": "N"}) is None

    def test_female_only(self):
        """Gender 'F' should return 0.0 (100% female)."""
        assert _parse_gender_ratio({"gender": "F"}) == 0.0

    def test_male_only(self):
        """Gender 'M' should return 1.0 (100% male)."""
        assert _parse_gender_ratio({"gender": "M"}) == 1.0

    def test_gender_ratio_dict(self):
        """genderRatio dict should extract M ratio."""
        assert _parse_gender_ratio({"genderRatio": {"M": 0.875}}) == 0.875
        assert _parse_gender_ratio({"genderRatio": {"M": 0.5}}) == 0.5

    def test_default_gender_ratio(self):
        """Default gender ratio should be 0.5."""
        assert _parse_gender_ratio({}) == 0.5


class TestParseAbilities:
    """Tests for _parse_abilities helper function."""

    def test_parse_single_ability(self):
        """Should parse single ability correctly."""
        data = {"abilities": {"0": "Static"}}
        abilities, hidden = _parse_abilities(data)
        assert abilities == ("Static",)
        assert hidden is None

    def test_parse_dual_abilities(self):
        """Should parse dual abilities correctly."""
        data = {"abilities": {"0": "Static", "1": "Lightning Rod"}}
        abilities, hidden = _parse_abilities(data)
        assert "Static" in abilities
        assert "Lightning Rod" in abilities
        assert hidden is None

    def test_parse_hidden_ability(self):
        """Should parse hidden ability correctly."""
        data = {"abilities": {"0": "Static", "H": "Lightning Rod"}}
        abilities, hidden = _parse_abilities(data)
        assert abilities == ("Static",)
        assert hidden == "Lightning Rod"

    def test_skip_special_ability(self):
        """Should skip 'S' (special) abilities."""
        data = {"abilities": {"0": "Static", "S": "Lightning Rod"}}
        abilities, hidden = _parse_abilities(data)
        assert abilities == ("Static",)
        assert hidden is None

    def test_empty_abilities(self):
        """Should handle empty abilities dict."""
        abilities, hidden = _parse_abilities({})
        assert abilities == ()
        assert hidden is None


class TestParseEvolutions:
    """Tests for _parse_evolutions helper function."""

    def test_no_evolutions(self):
        """Should return empty tuple when no evos."""
        result = _parse_evolutions({})
        assert result == ()

    def test_single_evolution(self):
        """Should parse single evolution correctly."""
        data = {
            "evos": ["Ivysaur"],
            "evoLevel": 16,
        }
        result = _parse_evolutions(data)
        assert len(result) == 1
        assert result[0].target == "Ivysaur"
        assert result[0].level == 16
        assert result[0].evo_type == EvolutionType.LEVEL

    def test_multiple_evolutions(self):
        """Should parse multiple evolutions (like Eevee)."""
        data = {
            "evos": ["Vaporeon", "Jolteon", "Flareon"],
        }
        result = _parse_evolutions(data)
        assert len(result) == 3
        targets = [e.target for e in result]
        assert "Vaporeon" in targets
        assert "Jolteon" in targets
        assert "Flareon" in targets

    def test_use_item_evolution(self):
        """Should parse item-based evolution."""
        data = {
            "evos": ["Vaporeon"],
            "evoType": "useItem",
            "evoItem": "Water Stone",
        }
        result = _parse_evolutions(data)
        assert len(result) == 1
        assert result[0].evo_type == EvolutionType.USE_ITEM
        assert result[0].item == "Water Stone"

    def test_trade_evolution(self):
        """Should parse trade evolution."""
        data = {
            "evos": ["Alakazam"],
            "evoType": "trade",
        }
        result = _parse_evolutions(data)
        assert len(result) == 1
        assert result[0].evo_type == EvolutionType.TRADE

    def test_friendship_evolution(self):
        """Should parse friendship evolution."""
        data = {
            "evos": ["Crobat"],
            "evoType": "levelFriendship",
        }
        result = _parse_evolutions(data)
        assert len(result) == 1
        assert result[0].evo_type == EvolutionType.LEVEL_FRIENDSHIP

    def test_level_move_evolution(self):
        """Should parse level-with-move evolution."""
        data = {
            "evos": ["Sylveon"],
            "evoType": "levelMove",
            "evoMove": "Baby-Doll Eyes",
        }
        result = _parse_evolutions(data)
        assert len(result) == 1
        assert result[0].evo_type == EvolutionType.LEVEL_MOVE
        assert result[0].move == "Baby-Doll Eyes"

    def test_evolution_condition(self):
        """Should parse evolution condition."""
        data = {
            "evos": ["Espeon"],
            "evoType": "levelFriendship",
            "evoCondition": "during the day",
        }
        result = _parse_evolutions(data)
        assert len(result) == 1
        assert result[0].condition == "during the day"


class TestInferGeneration:
    """Tests for _infer_generation helper function."""

    def test_gen1_by_dex(self):
        """Dex 1-151 should be Gen 1."""
        assert _infer_generation(1, []) == 1
        assert _infer_generation(25, []) == 1   # Pikachu
        assert _infer_generation(151, []) == 1  # Mew

    def test_gen2_by_dex(self):
        """Dex 152-251 should be Gen 2."""
        assert _infer_generation(152, []) == 2
        assert _infer_generation(251, []) == 2  # Celebi

    def test_gen3_by_dex(self):
        """Dex 252-386 should be Gen 3."""
        assert _infer_generation(252, []) == 3
        assert _infer_generation(386, []) == 3  # Deoxys

    def test_gen4_by_dex(self):
        """Dex 387-493 should be Gen 4."""
        assert _infer_generation(387, []) == 4
        assert _infer_generation(445, []) == 4  # Garchomp
        assert _infer_generation(493, []) == 4  # Arceus

    def test_gen5_by_dex(self):
        """Dex 494-649 should be Gen 5."""
        assert _infer_generation(494, []) == 5
        assert _infer_generation(649, []) == 5  # Genesect

    def test_gen6_by_dex(self):
        """Dex 650-721 should be Gen 6."""
        assert _infer_generation(650, []) == 6
        assert _infer_generation(721, []) == 6  # Volcanion

    def test_gen7_by_dex(self):
        """Dex 722-809 should be Gen 7."""
        assert _infer_generation(722, []) == 7
        assert _infer_generation(809, []) == 7  # Melmetal

    def test_gen8_by_dex(self):
        """Dex 810-905 should be Gen 8."""
        assert _infer_generation(810, []) == 8
        assert _infer_generation(905, []) == 8  # Enamorus

    def test_gen9_by_dex(self):
        """Dex 906+ should be Gen 9."""
        assert _infer_generation(906, []) == 9
        assert _infer_generation(1000, []) == 9

    def test_invalid_dex(self):
        """Invalid dex (0 or negative) should return 0."""
        assert _infer_generation(0, []) == 0
        assert _infer_generation(-1, []) == 0

    def test_tag_overrides_dex(self):
        """Gen tag should override dex inference."""
        # Even with dex 25 (Pikachu, Gen 1), Gen8 tag should override
        assert _infer_generation(25, ["Gen8"]) == 8
        assert _infer_generation(25, ["Gen4"]) == 4


class TestParseTags:
    """Tests for _parse_tags helper function."""

    def test_empty_tags(self):
        """Should return empty tuple when no tags."""
        assert _parse_tags({}) == ()

    def test_single_tag(self):
        """Should parse single tag."""
        assert _parse_tags({"tags": ["Legendary"]}) == ("Legendary",)

    def test_multiple_tags(self):
        """Should parse multiple tags."""
        result = _parse_tags({"tags": ["Legendary", "Restricted"]})
        assert "Legendary" in result
        assert "Restricted" in result

    def test_non_list_tags(self):
        """Should handle non-list tags gracefully."""
        assert _parse_tags({"tags": "NotAList"}) == ()


class TestParseTSValue:
    """Tests for _parse_ts_value helper function."""

    def test_parse_string_double_quotes(self):
        """Should parse double-quoted strings."""
        assert _parse_ts_value('"hello"') == "hello"
        assert _parse_ts_value('"Fire"') == "Fire"

    def test_parse_string_single_quotes(self):
        """Should parse single-quoted strings."""
        assert _parse_ts_value("'hello'") == "hello"
        assert _parse_ts_value("'Water'") == "Water"

    def test_parse_integer(self):
        """Should parse integers."""
        assert _parse_ts_value("42") == 42
        assert _parse_ts_value("0") == 0
        assert _parse_ts_value("100") == 100

    def test_parse_float(self):
        """Should parse floats."""
        assert _parse_ts_value("3.14") == 3.14
        assert _parse_ts_value("0.5") == 0.5

    def test_parse_boolean_true(self):
        """Should parse 'true' as True."""
        assert _parse_ts_value("true") is True

    def test_parse_boolean_false(self):
        """Should parse 'false' as False."""
        assert _parse_ts_value("false") is False

    def test_parse_empty_array(self):
        """Should parse empty array."""
        assert _parse_ts_value("[]") == []

    def test_parse_string_array(self):
        """Should parse array of strings."""
        result = _parse_ts_value('["Fire", "Water"]')
        assert result == ["Fire", "Water"]

    def test_parse_number_array(self):
        """Should parse array of numbers."""
        result = _parse_ts_value("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_parse_plain_string(self):
        """Should return plain string if nothing else matches."""
        assert _parse_ts_value("SomeValue") == "SomeValue"


class TestParseTSObjectSimple:
    """Tests for _parse_ts_object_simple helper function."""

    def test_parse_simple_object(self):
        """Should parse simple key-value pairs."""
        content = """
        num: 25,
        name: "Pikachu",
        """
        result = _parse_ts_object_simple(content)
        assert result.get("num") == 25
        assert result.get("name") == "Pikachu"

    def test_parse_object_with_nested_array(self):
        """Should parse object with array value."""
        content = """
        types: ["Electric"],
        baseStats: 35,
        """
        result = _parse_ts_object_simple(content)
        assert result.get("types") == ["Electric"]
        assert result.get("baseStats") == 35

    def test_skip_comments(self):
        """Should skip comment lines."""
        content = """
        // This is a comment
        num: 1,
        """
        result = _parse_ts_object_simple(content)
        assert result.get("num") == 1

    def test_handle_empty_lines(self):
        """Should handle empty lines gracefully."""
        content = """

        num: 1,

        name: "Bulbasaur",

        """
        result = _parse_ts_object_simple(content)
        assert result.get("num") == 1
        assert result.get("name") == "Bulbasaur"


class TestParseTSPokedex:
    """Tests for parse_ts_pokedex function."""

    def test_parse_single_pokemon(self):
        """Should parse a single Pokemon entry."""
        content = """
        export const Pokedex: {[id: string]: any} = {
            pikachu: {
                num: 25,
                name: "Pikachu",
            },
        };
        """
        result = parse_ts_pokedex(content)
        assert "pikachu" in result
        assert result["pikachu"].get("num") == 25
        assert result["pikachu"].get("name") == "Pikachu"

    def test_parse_multiple_pokemon(self):
        """Should parse multiple Pokemon entries."""
        content = """
        export const Pokedex: {[id: string]: any} = {
            bulbasaur: {
                num: 1,
                name: "Bulbasaur",
            },
            charmander: {
                num: 4,
                name: "Charmander",
            },
        };
        """
        result = parse_ts_pokedex(content)
        assert "bulbasaur" in result
        assert "charmander" in result
        assert result["bulbasaur"].get("num") == 1
        assert result["charmander"].get("num") == 4


class TestSpeciesDataIntegration:
    """Integration tests using the loaded species registry."""

    def test_pikachu_loaded(self):
        """Pikachu should be loaded from pokedex data."""
        from data.species import get_species
        pikachu = get_species(25)
        assert pikachu is not None
        assert pikachu.name == "Pikachu"

    def test_charizard_loaded(self):
        """Charizard should be loaded from pokedex data."""
        from data.species import get_species
        charizard = get_species(6)
        assert charizard is not None
        assert charizard.name == "Charizard"
        assert charizard.type1 == Type.FIRE
        assert charizard.type2 == Type.FLYING

    def test_base_stats_loaded(self):
        """Base stats should be loaded correctly."""
        from data.species import get_species
        pikachu = get_species(25)
        assert pikachu.base_stats.hp == 35
        assert pikachu.base_stats.spe == 90

    def test_abilities_loaded(self):
        """Abilities should be loaded correctly."""
        from data.species import get_species
        pikachu = get_species(25)
        assert len(pikachu.abilities) > 0

    def test_many_species_loaded(self):
        """Registry should have many species loaded."""
        from data.species import get_species_count
        assert get_species_count() > 100


class TestEdgeCases:
    """Tests for edge cases in species loading."""

    def test_form_with_different_types(self):
        """Form with different types should load correctly."""
        from data.species import get_species_by_name
        # Alolan Vulpix changes from Fire to Ice
        vulpix_alola = get_species_by_name("Vulpix-Alola")
        if vulpix_alola:  # May not be loaded in all test environments
            assert vulpix_alola.type1 == Type.ICE

    def test_form_with_different_stats(self):
        """Form with different stats should load correctly."""
        from data.species import get_species_by_name
        charizard = get_species_by_name("Charizard")
        mega_x = get_species_by_name("Charizard-Mega-X")
        if charizard and mega_x:
            # Mega Charizard X has higher attack
            assert mega_x.base_stats.atk > charizard.base_stats.atk

    def test_shedinja_special_hp(self):
        """Shedinja should have base HP of 1."""
        from data.species import get_species
        shedinja = get_species(292)
        if shedinja:
            assert shedinja.base_stats.hp == 1

    def test_species_with_no_evolution(self):
        """Fully evolved species should have no evolutions."""
        from data.species import get_species_by_name
        venusaur = get_species_by_name("Venusaur")
        if venusaur:
            assert venusaur.is_fully_evolved
            assert len(venusaur.evolutions) == 0

    def test_species_with_multiple_evolutions(self):
        """Species with branching evolutions should load correctly."""
        from data.species import get_species_by_name
        eevee = get_species_by_name("Eevee")
        if eevee:
            assert eevee.can_evolve
            assert len(eevee.evolutions) >= 8
