"""Pokemon species data and registry.

Species define the base template for a Pokemon: base stats, types, abilities, etc.
This module provides SpeciesData frozen dataclass with support for forms and evolutions,
and a registry that loads all species from the Showdown data.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, FrozenSet, List, Optional, Tuple, Set

from .types import Type


class EvolutionType(Enum):
    """Types of evolution triggers."""
    LEVEL = auto()           # Evolves at a specific level
    LEVEL_FRIENDSHIP = auto()  # Evolves when leveled with high friendship
    USE_ITEM = auto()        # Evolves when item is used
    TRADE = auto()           # Evolves when traded
    TRADE_ITEM = auto()      # Evolves when traded holding an item
    LEVEL_HOLD = auto()      # Evolves when leveled while holding an item
    LEVEL_MOVE = auto()      # Evolves when leveled knowing a specific move
    LEVEL_EXTRA = auto()     # Evolves at level with special condition
    OTHER = auto()           # Other/special evolution


class FormType(Enum):
    """Types of Pokemon forms."""
    BASE = auto()            # Base form
    MEGA = auto()            # Mega Evolution
    MEGA_X = auto()          # Mega Evolution X
    MEGA_Y = auto()          # Mega Evolution Y
    PRIMAL = auto()          # Primal Reversion
    ALOLA = auto()           # Alolan form
    GALAR = auto()           # Galarian form
    HISUI = auto()           # Hisuian form
    PALDEA = auto()          # Paldean form
    GMAX = auto()            # Gigantamax
    TOTEM = auto()           # Totem form
    BATTLE = auto()          # Battle-only form (Aegislash, Darmanitan, etc.)
    COSMETIC = auto()        # Cosmetic form (no stat differences)
    OTHER = auto()           # Other form type


@dataclass(frozen=True)
class BaseStats:
    """Base stats for a Pokemon species.

    These are the raw values used in stat calculation formulas.
    Range is typically 1-255 for each stat.
    """
    hp: int
    atk: int
    defense: int  # 'def' is a Python keyword
    spa: int
    spd: int
    spe: int

    def __getitem__(self, index: int) -> int:
        """Allow indexing by stat index (0=HP, 1=Atk, etc.)."""
        return (self.hp, self.atk, self.defense, self.spa, self.spd, self.spe)[index]

    def as_tuple(self) -> Tuple[int, int, int, int, int, int]:
        """Return stats as a tuple."""
        return (self.hp, self.atk, self.defense, self.spa, self.spd, self.spe)

    @property
    def total(self) -> int:
        """Base stat total (BST)."""
        return self.hp + self.atk + self.defense + self.spa + self.spd + self.spe


@dataclass(frozen=True)
class EvolutionData:
    """Data describing how a Pokemon evolves.

    Attributes:
        target: Name of the species this evolves into
        evo_type: Type of evolution trigger
        level: Level required (for level-based evolutions)
        item: Item required (for item-based evolutions)
        move: Move required (for move-based evolutions)
        condition: Additional text condition
    """
    target: str
    evo_type: EvolutionType = EvolutionType.LEVEL
    level: Optional[int] = None
    item: Optional[str] = None
    move: Optional[str] = None
    condition: Optional[str] = None


@dataclass(frozen=True)
class FormData:
    """Data for an alternate form of a Pokemon.

    Forms can have different stats, types, abilities, etc.
    Some forms are battle-only (like Mega Evolutions).

    Attributes:
        name: Display name of this form (e.g., "Charizard-Mega-X")
        forme: Form identifier (e.g., "Mega-X")
        form_type: Type classification of this form
        base_stats: Stats for this form (may differ from base)
        type1: Primary type (may differ from base)
        type2: Secondary type (may differ from base)
        abilities: Available abilities for this form
        hidden_ability: Hidden ability for this form
        weight: Weight in kg
        height: Height in m
        required_item: Item required to transform into this form
        required_ability: Ability required for this form
        changes_from: Species/form this changes from (for in-battle transforms)
        is_battle_only: True if form only exists during battle
        is_cosmetic: True if form is purely cosmetic (no gameplay differences)
    """
    name: str
    forme: str
    form_type: FormType = FormType.OTHER
    base_stats: Optional[BaseStats] = None
    type1: Optional[Type] = None
    type2: Optional[Type] = None
    abilities: Tuple[str, ...] = field(default_factory=tuple)
    hidden_ability: Optional[str] = None
    weight: float = 0.0
    height: float = 0.0
    required_item: Optional[str] = None
    required_ability: Optional[str] = None
    changes_from: Optional[str] = None
    is_battle_only: bool = False
    is_cosmetic: bool = False


@dataclass(frozen=True)
class SpeciesData:
    """Immutable data for a Pokemon species.

    Attributes:
        id: Unique integer ID for this species
        name: Display name of the species
        dex_num: National Pokedex number
        base_stats: Base stat values
        type1: Primary type
        type2: Secondary type (None if single-typed)
        abilities: Tuple of ability names (regular abilities)
        hidden_ability: Hidden ability name (None if none)
        weight: Weight in kg (for weight-based moves)
        height: Height in m
        gender_ratio: Male ratio (0.0-1.0), None for genderless
        egg_groups: Tuple of egg group names
        base_exp: Base experience yield
        catch_rate: Catch rate (1-255)
        base_friendship: Base friendship value
        generation: Generation this species was introduced
        color: Color category for Pokedex
        evolutions: Tuple of evolution data for this species
        prevo: Name of pre-evolution (None if none)
        other_forms: Tuple of alternate form data
        base_forme: Name of the base forme (for alternate forms)
        forme: Form identifier (None for base form)
        form_type: Type classification of this form
        is_legendary: Whether this is a legendary Pokemon
        is_mythical: Whether this is a mythical Pokemon
        is_baby: Whether this is a baby Pokemon
        can_gigantamax: G-Max move name if can Gigantamax (None otherwise)
        tags: Additional classification tags
    """
    id: int
    name: str
    dex_num: int
    base_stats: BaseStats
    type1: Type
    type2: Optional[Type] = None
    abilities: Tuple[str, ...] = field(default_factory=tuple)
    hidden_ability: Optional[str] = None
    weight: float = 0.0
    height: float = 0.0
    gender_ratio: Optional[float] = 0.5
    egg_groups: Tuple[str, ...] = field(default_factory=tuple)
    base_exp: int = 0
    catch_rate: int = 45
    base_friendship: int = 70
    generation: int = 1
    color: str = "Gray"
    evolutions: Tuple[EvolutionData, ...] = field(default_factory=tuple)
    prevo: Optional[str] = None
    other_forms: Tuple[FormData, ...] = field(default_factory=tuple)
    base_forme: Optional[str] = None
    forme: Optional[str] = None
    form_type: FormType = FormType.BASE
    is_legendary: bool = False
    is_mythical: bool = False
    is_baby: bool = False
    can_gigantamax: Optional[str] = None
    tags: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def types(self) -> Tuple[Type, ...]:
        """Return all types as a tuple."""
        if self.type2 is None or self.type2 == self.type1:
            return (self.type1,)
        return (self.type1, self.type2)

    @property
    def is_dual_typed(self) -> bool:
        """Return True if this species has two different types."""
        return self.type2 is not None and self.type2 != self.type1

    @property
    def can_evolve(self) -> bool:
        """Return True if this species can evolve."""
        return len(self.evolutions) > 0

    @property
    def is_fully_evolved(self) -> bool:
        """Return True if this species cannot evolve."""
        return len(self.evolutions) == 0

    @property
    def has_forms(self) -> bool:
        """Return True if this species has alternate forms."""
        return len(self.other_forms) > 0

    @property
    def is_forme(self) -> bool:
        """Return True if this is an alternate form (not the base)."""
        return self.forme is not None and self.forme != ""

    @property
    def is_mega(self) -> bool:
        """Return True if this is a Mega Evolution."""
        return self.form_type in (FormType.MEGA, FormType.MEGA_X, FormType.MEGA_Y)

    @property
    def is_gmax(self) -> bool:
        """Return True if this is a Gigantamax form."""
        return self.form_type == FormType.GMAX

    @property
    def is_regional(self) -> bool:
        """Return True if this is a regional form."""
        return self.form_type in (FormType.ALOLA, FormType.GALAR, FormType.HISUI, FormType.PALDEA)


# Registry of species with their IDs
SPECIES_REGISTRY: Dict[int, SpeciesData] = {}
SPECIES_BY_NAME: Dict[str, int] = {}
SPECIES_BY_DEX: Dict[int, List[int]] = {}  # dex_num -> list of species IDs (for forms)


def _normalize_name(name: str) -> str:
    """Normalize a species name for lookup."""
    return name.lower().replace(" ", "").replace("-", "").replace(".", "").replace("'", "").replace(":", "")


def get_species(species_id: int) -> Optional[SpeciesData]:
    """Get species data by ID.

    Args:
        species_id: The unique ID of the species

    Returns:
        SpeciesData if found, None otherwise
    """
    return SPECIES_REGISTRY.get(species_id)


def get_species_id(name: str) -> Optional[int]:
    """Get species ID by name.

    Args:
        name: The name of the species (case-insensitive)

    Returns:
        Species ID if found, None otherwise
    """
    return SPECIES_BY_NAME.get(_normalize_name(name))


def get_species_by_name(name: str) -> Optional[SpeciesData]:
    """Get species data by name.

    Args:
        name: The name of the species (case-insensitive)

    Returns:
        SpeciesData if found, None otherwise
    """
    species_id = get_species_id(name)
    if species_id is not None:
        return SPECIES_REGISTRY.get(species_id)
    return None


def get_species_by_dex(dex_num: int) -> Optional[SpeciesData]:
    """Get base species data by National Pokedex number.

    Args:
        dex_num: The National Pokedex number

    Returns:
        Base form SpeciesData if found, None otherwise
    """
    species_ids = SPECIES_BY_DEX.get(dex_num)
    if species_ids:
        # Return the base form (first one registered, or one without forme)
        for sid in species_ids:
            species = SPECIES_REGISTRY.get(sid)
            if species and not species.is_forme:
                return species
        # If no base form found, return first available
        return SPECIES_REGISTRY.get(species_ids[0])
    return None


def get_all_forms_by_dex(dex_num: int) -> List[SpeciesData]:
    """Get all species forms for a given Pokedex number.

    Args:
        dex_num: The National Pokedex number

    Returns:
        List of all SpeciesData with this dex number (base + forms)
    """
    species_ids = SPECIES_BY_DEX.get(dex_num, [])
    return [SPECIES_REGISTRY[sid] for sid in species_ids if sid in SPECIES_REGISTRY]


def register_species(species: SpeciesData) -> None:
    """Register a new species in the registry.

    Args:
        species: The SpeciesData to register
    """
    SPECIES_REGISTRY[species.id] = species
    SPECIES_BY_NAME[_normalize_name(species.name)] = species.id
    if species.dex_num not in SPECIES_BY_DEX:
        SPECIES_BY_DEX[species.dex_num] = []
    if species.id not in SPECIES_BY_DEX[species.dex_num]:
        SPECIES_BY_DEX[species.dex_num].append(species.id)


def get_species_count() -> int:
    """Get the total number of registered species."""
    return len(SPECIES_REGISTRY)


def get_base_species_count() -> int:
    """Get the number of base (non-forme) species."""
    return sum(1 for s in SPECIES_REGISTRY.values() if not s.is_forme)


def get_form_species_count() -> int:
    """Get the number of alternate form species."""
    return sum(1 for s in SPECIES_REGISTRY.values() if s.is_forme)


# Initialize with placeholder
_PLACEHOLDER = SpeciesData(
    id=0,
    name="MissingNo",
    dex_num=0,
    base_stats=BaseStats(hp=0, atk=0, defense=0, spa=0, spd=0, spe=0),
    type1=Type.NORMAL,
    generation=0,
)
register_species(_PLACEHOLDER)


def _auto_load_species() -> None:
    """Automatically load species data from the TypeScript source.

    This is called on module import for backwards compatibility.
    """
    from pathlib import Path

    # Only load if we just have the placeholder
    if len(SPECIES_REGISTRY) > 1:
        return

    # Try to find the pokedex file
    module_dir = Path(__file__).parent
    possible_paths = [
        module_dir / "raw" / "pokedex_data.ts",
        module_dir.parent / "doc" / "pokedex_data.ts",
    ]

    for path in possible_paths:
        if path.exists():
            try:
                # Import loader here to avoid circular imports
                from .species_loader import load_species_from_ts
                load_species_from_ts(str(path))
                return
            except Exception:
                pass


# Auto-load species data
_auto_load_species()
