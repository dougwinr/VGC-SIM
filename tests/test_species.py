"""Tests for data/species.py - Species data and registry.

Tests cover:
- BaseStats dataclass
- SpeciesData frozen dataclass
- Species registry lookup functions
- Pre-registered species
- Forms system (Megas, regional variants, Gigantamax)
- Evolution data
"""
import pytest

from data.species import (
    BaseStats,
    EvolutionData,
    EvolutionType,
    FormData,
    FormType,
    SpeciesData,
    SPECIES_REGISTRY,
    SPECIES_BY_NAME,
    SPECIES_BY_DEX,
    get_species,
    get_species_id,
    get_species_by_name,
    get_species_by_dex,
    get_all_forms_by_dex,
    register_species,
    get_species_count,
    get_base_species_count,
    get_form_species_count,
)
from data.types import Type


class TestBaseStats:
    """Tests for the BaseStats dataclass."""

    def test_basestats_creation(self):
        """BaseStats can be created with all six stats."""
        stats = BaseStats(hp=100, atk=110, defense=90, spa=130, spd=90, spe=80)
        assert stats.hp == 100
        assert stats.atk == 110
        assert stats.defense == 90
        assert stats.spa == 130
        assert stats.spd == 90
        assert stats.spe == 80

    def test_basestats_indexing(self):
        """BaseStats supports index access (0=HP, 1=Atk, etc.)."""
        stats = BaseStats(hp=100, atk=110, defense=90, spa=130, spd=90, spe=80)
        assert stats[0] == 100  # HP
        assert stats[1] == 110  # Atk
        assert stats[2] == 90   # Def
        assert stats[3] == 130  # SpA
        assert stats[4] == 90   # SpD
        assert stats[5] == 80   # Spe

    def test_basestats_as_tuple(self):
        """BaseStats can be converted to a tuple."""
        stats = BaseStats(hp=100, atk=110, defense=90, spa=130, spd=90, spe=80)
        t = stats.as_tuple()
        assert t == (100, 110, 90, 130, 90, 80)

    def test_basestats_total(self):
        """BaseStats calculates base stat total (BST)."""
        stats = BaseStats(hp=100, atk=110, defense=90, spa=130, spd=90, spe=80)
        assert stats.total == 600

    def test_basestats_immutable(self):
        """BaseStats is immutable (frozen dataclass)."""
        stats = BaseStats(hp=100, atk=110, defense=90, spa=130, spd=90, spe=80)
        with pytest.raises(Exception):  # FrozenInstanceError
            stats.hp = 50


class TestSpeciesData:
    """Tests for the SpeciesData dataclass."""

    def test_species_single_type(self):
        """Single-typed species has type2 as None."""
        species = SpeciesData(
            id=25,
            name="Pikachu",
            dex_num=25,
            base_stats=BaseStats(hp=35, atk=55, defense=40, spa=50, spd=50, spe=90),
            type1=Type.ELECTRIC,
        )
        assert species.type1 == Type.ELECTRIC
        assert species.type2 is None
        assert not species.is_dual_typed
        assert species.types == (Type.ELECTRIC,)

    def test_species_dual_type(self):
        """Dual-typed species has both types set."""
        species = SpeciesData(
            id=6,
            name="Charizard",
            dex_num=6,
            base_stats=BaseStats(hp=78, atk=84, defense=78, spa=109, spd=85, spe=100),
            type1=Type.FIRE,
            type2=Type.FLYING,
        )
        assert species.type1 == Type.FIRE
        assert species.type2 == Type.FLYING
        assert species.is_dual_typed
        assert species.types == (Type.FIRE, Type.FLYING)

    def test_species_same_type_not_dual(self):
        """Species with same type1 and type2 is not considered dual-typed."""
        species = SpeciesData(
            id=999,
            name="TestMon",
            dex_num=999,
            base_stats=BaseStats(hp=50, atk=50, defense=50, spa=50, spd=50, spe=50),
            type1=Type.NORMAL,
            type2=Type.NORMAL,
        )
        assert not species.is_dual_typed
        assert species.types == (Type.NORMAL,)

    def test_species_immutable(self):
        """SpeciesData is immutable (frozen dataclass)."""
        species = SpeciesData(
            id=1,
            name="TestMon",
            dex_num=1,
            base_stats=BaseStats(hp=50, atk=50, defense=50, spa=50, spd=50, spe=50),
            type1=Type.NORMAL,
        )
        with pytest.raises(Exception):
            species.name = "ChangedName"


class TestSpeciesRegistry:
    """Tests for the species registry and lookup functions."""

    def test_registry_contains_missingno(self):
        """Registry contains MissingNo placeholder at ID 0."""
        assert 0 in SPECIES_REGISTRY
        species = SPECIES_REGISTRY[0]
        assert species.name == "MissingNo"
        assert species.base_stats.total == 0

    def test_registry_contains_pikachu(self):
        """Registry contains Pikachu."""
        assert 25 in SPECIES_REGISTRY
        species = SPECIES_REGISTRY[25]
        assert species.name == "Pikachu"
        assert species.type1 == Type.ELECTRIC

    def test_registry_contains_charizard(self):
        """Registry contains Charizard."""
        assert 6 in SPECIES_REGISTRY
        species = SPECIES_REGISTRY[6]
        assert species.name == "Charizard"
        assert species.type1 == Type.FIRE
        assert species.type2 == Type.FLYING

    def test_get_species_by_id(self):
        """get_species returns species by ID."""
        pikachu = get_species(25)
        assert pikachu is not None
        assert pikachu.name == "Pikachu"

    def test_get_species_nonexistent(self):
        """get_species returns None for nonexistent ID."""
        result = get_species(99999)
        assert result is None

    def test_get_species_id_by_name(self):
        """get_species_id returns ID by name."""
        id_ = get_species_id("pikachu")
        assert id_ == 25

    def test_get_species_id_case_insensitive(self):
        """get_species_id is case-insensitive."""
        assert get_species_id("PIKACHU") == 25
        assert get_species_id("Pikachu") == 25
        assert get_species_id("pikachu") == 25

    def test_get_species_id_nonexistent(self):
        """get_species_id returns None for nonexistent name."""
        result = get_species_id("NotAPokemon")
        assert result is None

    def test_get_species_by_dex(self):
        """get_species_by_dex returns species by Pokedex number."""
        charizard = get_species_by_dex(6)
        assert charizard is not None
        assert charizard.name == "Charizard"

    def test_get_species_by_dex_nonexistent(self):
        """get_species_by_dex returns None for nonexistent dex number."""
        result = get_species_by_dex(99999)
        assert result is None

    def test_get_species_by_name_nonexistent(self):
        """get_species_by_name returns None for nonexistent species name."""
        result = get_species_by_name("NonexistentPokemon12345")
        assert result is None


class TestRegisteredSpeciesData:
    """Tests for correctness of pre-registered species data."""

    def test_pikachu_base_stats(self):
        """Pikachu has correct base stats."""
        pikachu = get_species(25)
        assert pikachu.base_stats.hp == 35
        assert pikachu.base_stats.atk == 55
        assert pikachu.base_stats.defense == 40
        assert pikachu.base_stats.spa == 50
        assert pikachu.base_stats.spd == 50
        assert pikachu.base_stats.spe == 90

    def test_charizard_base_stats(self):
        """Charizard has correct base stats."""
        charizard = get_species(6)
        assert charizard.base_stats.hp == 78
        assert charizard.base_stats.atk == 84
        assert charizard.base_stats.defense == 78
        assert charizard.base_stats.spa == 109
        assert charizard.base_stats.spd == 85
        assert charizard.base_stats.spe == 100

    def test_garchomp_base_stats(self):
        """Garchomp has correct base stats (BST 600)."""
        garchomp = get_species(445)
        assert garchomp.base_stats.hp == 108
        assert garchomp.base_stats.atk == 130
        assert garchomp.base_stats.defense == 95
        assert garchomp.base_stats.spa == 80
        assert garchomp.base_stats.spd == 85
        assert garchomp.base_stats.spe == 102
        assert garchomp.base_stats.total == 600

    def test_blissey_extreme_hp(self):
        """Blissey has the highest HP base stat (255)."""
        blissey = get_species(242)
        assert blissey.base_stats.hp == 255

    def test_shedinja_unique_hp(self):
        """Shedinja has unique 1 HP base stat."""
        shedinja = get_species(292)
        assert shedinja.base_stats.hp == 1

    def test_alakazam_high_spa_spe(self):
        """Alakazam has high Special Attack and Speed."""
        alakazam = get_species(65)
        assert alakazam.base_stats.spa == 135
        assert alakazam.base_stats.spe == 120

    def test_tyranitar_is_rock_dark(self):
        """Tyranitar is Rock/Dark type."""
        tyranitar = get_species(248)
        assert tyranitar.type1 == Type.ROCK
        assert tyranitar.type2 == Type.DARK

    def test_dragonite_is_dragon_flying(self):
        """Dragonite is Dragon/Flying type."""
        dragonite = get_species(149)
        assert dragonite.type1 == Type.DRAGON
        assert dragonite.type2 == Type.FLYING

    def test_gengar_is_ghost_poison(self):
        """Gengar is Ghost/Poison type."""
        gengar = get_species(94)
        assert gengar.type1 == Type.GHOST
        assert gengar.type2 == Type.POISON

    def test_gyarados_is_water_flying(self):
        """Gyarados is Water/Flying type."""
        gyarados = get_species(130)
        assert gyarados.type1 == Type.WATER
        assert gyarados.type2 == Type.FLYING


class TestRegisterSpecies:
    """Tests for dynamically registering new species."""

    def test_register_new_species(self):
        """New species can be registered."""
        new_species = SpeciesData(
            id=9999,
            name="TestSpecies",
            dex_num=9999,
            base_stats=BaseStats(hp=100, atk=100, defense=100, spa=100, spd=100, spe=100),
            type1=Type.DRAGON,
        )
        register_species(new_species)

        # Verify it was registered
        assert get_species(9999) is not None
        assert get_species(9999).name == "TestSpecies"
        assert get_species_id("testspecies") == 9999

        # Cleanup
        del SPECIES_REGISTRY[9999]
        del SPECIES_BY_NAME["testspecies"]
        del SPECIES_BY_DEX[9999]

    def test_name_lookup_maps_updated(self):
        """SPECIES_BY_NAME is updated when registering."""
        count_before = len(SPECIES_BY_NAME)

        new_species = SpeciesData(
            id=9998,
            name="UniqueTestName",
            dex_num=9998,
            base_stats=BaseStats(hp=50, atk=50, defense=50, spa=50, spd=50, spe=50),
            type1=Type.NORMAL,
        )
        register_species(new_species)

        assert len(SPECIES_BY_NAME) == count_before + 1
        assert "uniquetestname" in SPECIES_BY_NAME

        # Cleanup
        del SPECIES_REGISTRY[9998]
        del SPECIES_BY_NAME["uniquetestname"]
        del SPECIES_BY_DEX[9998]


class TestEvolutionData:
    """Tests for the EvolutionData dataclass."""

    def test_evolution_data_creation(self):
        """EvolutionData can be created with basic fields."""
        evo = EvolutionData(target="Ivysaur", evo_type=EvolutionType.LEVEL, level=16)
        assert evo.target == "Ivysaur"
        assert evo.evo_type == EvolutionType.LEVEL
        assert evo.level == 16

    def test_evolution_data_immutable(self):
        """EvolutionData is immutable."""
        evo = EvolutionData(target="Ivysaur")
        with pytest.raises(Exception):
            evo.target = "Venusaur"

    def test_evolution_types(self):
        """EvolutionType enum has expected values."""
        assert EvolutionType.LEVEL is not None
        assert EvolutionType.USE_ITEM is not None
        assert EvolutionType.TRADE is not None
        assert EvolutionType.LEVEL_FRIENDSHIP is not None


class TestFormData:
    """Tests for the FormData dataclass."""

    def test_form_data_creation(self):
        """FormData can be created with basic fields."""
        form = FormData(
            name="Charizard-Mega-X",
            forme="Mega-X",
            form_type=FormType.MEGA_X,
        )
        assert form.name == "Charizard-Mega-X"
        assert form.forme == "Mega-X"
        assert form.form_type == FormType.MEGA_X

    def test_form_types(self):
        """FormType enum has expected values."""
        assert FormType.BASE is not None
        assert FormType.MEGA is not None
        assert FormType.MEGA_X is not None
        assert FormType.MEGA_Y is not None
        assert FormType.ALOLA is not None
        assert FormType.GALAR is not None
        assert FormType.GMAX is not None


class TestSpeciesEvolutions:
    """Tests for evolution chains in loaded species data."""

    def test_bulbasaur_evolves_to_ivysaur(self):
        """Bulbasaur evolves into Ivysaur."""
        bulbasaur = get_species_by_name("Bulbasaur")
        assert bulbasaur is not None
        assert bulbasaur.can_evolve
        assert len(bulbasaur.evolutions) > 0
        assert bulbasaur.evolutions[0].target == "Ivysaur"

    def test_venusaur_fully_evolved(self):
        """Venusaur is fully evolved."""
        venusaur = get_species_by_name("Venusaur")
        assert venusaur is not None
        assert venusaur.is_fully_evolved
        assert not venusaur.can_evolve

    def test_eevee_multiple_evolutions(self):
        """Eevee has multiple evolution paths."""
        eevee = get_species_by_name("Eevee")
        assert eevee is not None
        assert len(eevee.evolutions) >= 8  # All Eeveelutions
        evo_targets = [e.target for e in eevee.evolutions]
        assert "Vaporeon" in evo_targets
        assert "Jolteon" in evo_targets
        assert "Flareon" in evo_targets
        assert "Espeon" in evo_targets
        assert "Umbreon" in evo_targets

    def test_pikachu_has_prevo(self):
        """Pikachu has Pichu as pre-evolution."""
        pikachu = get_species_by_name("Pikachu")
        assert pikachu is not None
        assert pikachu.prevo == "Pichu"


class TestSpeciesForms:
    """Tests for alternate forms in loaded species data."""

    def test_charizard_has_mega_forms(self):
        """Charizard has Mega X and Mega Y forms."""
        charizard = get_species_by_name("Charizard")
        assert charizard is not None
        assert charizard.has_forms
        form_names = [f.name for f in charizard.other_forms]
        assert "Charizard-Mega-X" in form_names or any("Mega-X" in n for n in form_names)

    def test_mega_charizard_x_is_mega(self):
        """Charizard-Mega-X is identified as a Mega form."""
        mega_x = get_species_by_name("Charizard-Mega-X")
        assert mega_x is not None
        assert mega_x.is_mega
        assert mega_x.is_forme
        assert mega_x.form_type in (FormType.MEGA, FormType.MEGA_X)

    def test_mega_charizard_x_type_change(self):
        """Charizard-Mega-X has Fire/Dragon typing."""
        mega_x = get_species_by_name("Charizard-Mega-X")
        assert mega_x is not None
        assert mega_x.type1 == Type.FIRE
        assert mega_x.type2 == Type.DRAGON

    def test_alolan_vulpix_is_regional(self):
        """Vulpix-Alola is identified as a regional form."""
        vulpix_alola = get_species_by_name("Vulpix-Alola")
        assert vulpix_alola is not None
        assert vulpix_alola.is_regional
        assert vulpix_alola.form_type == FormType.ALOLA
        assert vulpix_alola.type1 == Type.ICE

    def test_alolan_rattata_is_regional(self):
        """Rattata-Alola is identified as a regional form."""
        rattata_alola = get_species_by_name("Rattata-Alola")
        assert rattata_alola is not None
        assert rattata_alola.is_regional
        assert Type.DARK in rattata_alola.types

    def test_gmax_charizard(self):
        """Charizard-Gmax is identified as a Gigantamax form."""
        gmax = get_species_by_name("Charizard-Gmax")
        assert gmax is not None
        assert gmax.is_gmax
        assert gmax.form_type == FormType.GMAX

    def test_get_all_forms_by_dex(self):
        """get_all_forms_by_dex returns all forms for a Pokedex number."""
        charizard_forms = get_all_forms_by_dex(6)  # Charizard's dex number
        assert len(charizard_forms) >= 3  # Base + Mega X + Mega Y (at minimum)
        names = [f.name for f in charizard_forms]
        assert "Charizard" in names


class TestSpeciesRegistryCounts:
    """Tests for species registry counting functions."""

    def test_species_count_large(self):
        """Registry should have many species loaded."""
        count = get_species_count()
        assert count > 700  # Should have hundreds of species

    def test_base_and_form_counts(self):
        """Base and form counts should sum to total."""
        total = get_species_count()
        base = get_base_species_count()
        forms = get_form_species_count()
        assert base + forms == total

    def test_more_base_than_forms(self):
        """There should be more base species than forms."""
        base = get_base_species_count()
        forms = get_form_species_count()
        assert base > forms


class TestLegendaryAndMythical:
    """Tests for legendary and mythical Pokemon identification."""

    def test_mewtwo_is_legendary(self):
        """Mewtwo is identified as legendary."""
        mewtwo = get_species_by_name("Mewtwo")
        assert mewtwo is not None
        assert mewtwo.is_legendary

    def test_mew_is_mythical(self):
        """Mew is identified as mythical."""
        mew = get_species_by_name("Mew")
        assert mew is not None
        assert mew.is_mythical

    def test_pikachu_not_legendary(self):
        """Pikachu is not legendary."""
        pikachu = get_species_by_name("Pikachu")
        assert pikachu is not None
        assert not pikachu.is_legendary
        assert not pikachu.is_mythical


class TestSpeciesGeneration:
    """Tests for generation data."""

    def test_bulbasaur_gen_1(self):
        """Bulbasaur is from Generation 1."""
        bulbasaur = get_species_by_name("Bulbasaur")
        assert bulbasaur is not None
        assert bulbasaur.generation == 1

    def test_pikachu_gen_1(self):
        """Pikachu is from Generation 1."""
        pikachu = get_species_by_name("Pikachu")
        assert pikachu is not None
        assert pikachu.generation == 1

    def test_garchomp_gen_4(self):
        """Garchomp is from Generation 4."""
        garchomp = get_species_by_name("Garchomp")
        assert garchomp is not None
        assert garchomp.generation == 4
