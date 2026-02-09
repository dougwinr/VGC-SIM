"""Comprehensive tests for data/moves.py based on move.md documentation.

Tests cover:
- Move categories (Physical, Special, Status)
- Move targets (singles, doubles, field, side)
- Move flags (contact, sound, punch, bite, etc.)
- Secondary effects structure
- Priority values
- PP system
- Accuracy handling
"""
import pytest

from data.moves import (
    MoveCategory,
    MoveTarget,
    MoveFlag,
    SecondaryEffect,
    MoveData,
    TARGET_BY_NAME,
    CATEGORY_BY_NAME,
    FLAG_BY_NAME,
    STANDARD_ATTACK,
    SPECIAL_ATTACK,
    STATUS_MOVE,
)
from data.types import Type


class TestMoveCategoryDefinitions:
    """Test MoveCategory enum is correctly defined."""

    def test_physical_category_exists(self):
        """Physical category for Attack-based moves."""
        assert MoveCategory.PHYSICAL.value >= 0

    def test_special_category_exists(self):
        """Special category for Sp. Atk-based moves."""
        assert MoveCategory.SPECIAL.value >= 0

    def test_status_category_exists(self):
        """Status category for non-damaging moves."""
        assert MoveCategory.STATUS.value >= 0

    def test_exactly_3_categories(self):
        """There should be exactly 3 move categories."""
        assert len(MoveCategory) == 3

    def test_categories_are_distinct(self):
        """Each category should have a unique value."""
        values = [c.value for c in MoveCategory]
        assert len(values) == len(set(values))


class TestMoveTargetDefinitions:
    """Test MoveTarget enum covers all targeting modes."""

    def test_normal_target_exists(self):
        """Normal: single adjacent target."""
        assert MoveTarget.NORMAL.value >= 0

    def test_self_target_exists(self):
        """Self: user only."""
        assert MoveTarget.SELF.value >= 0

    def test_adjacent_ally_target_exists(self):
        """Adjacent ally target for doubles."""
        assert MoveTarget.ADJACENT_ALLY.value >= 0

    def test_adjacent_foe_target_exists(self):
        """Adjacent foe target."""
        assert MoveTarget.ADJACENT_FOE.value >= 0

    def test_all_adjacent_foes_target_exists(self):
        """All adjacent foes (spread moves in doubles)."""
        assert MoveTarget.ALL_ADJACENT_FOES.value >= 0

    def test_all_adjacent_target_exists(self):
        """All adjacent Pokemon (like Earthquake in doubles)."""
        assert MoveTarget.ALL_ADJACENT.value >= 0

    def test_any_target_exists(self):
        """Any single Pokemon on the field."""
        assert MoveTarget.ANY.value >= 0

    def test_ally_side_target_exists(self):
        """User's side (for screens, etc.)."""
        assert MoveTarget.ALLY_SIDE.value >= 0

    def test_foe_side_target_exists(self):
        """Opponent's side (for hazards, etc.)."""
        assert MoveTarget.FOE_SIDE.value >= 0


class TestMoveFlagDefinitions:
    """Test MoveFlag bitflags are correctly defined."""

    def test_none_flag_is_zero(self):
        """NONE should be 0 for no flags."""
        assert MoveFlag.NONE == 0

    def test_contact_flag_exists(self):
        """Contact flag for physical contact moves."""
        assert MoveFlag.CONTACT.value > 0

    def test_protect_flag_exists(self):
        """Protect flag for moves blocked by Protect/Detect."""
        assert MoveFlag.PROTECT.value > 0

    def test_mirror_flag_exists(self):
        """Mirror flag for moves copyable by Mirror Move."""
        assert MoveFlag.MIRROR.value > 0

    def test_sound_flag_exists(self):
        """Sound flag for sound-based moves."""
        assert MoveFlag.SOUND.value > 0

    def test_bullet_flag_exists(self):
        """Bullet flag for ballistic moves."""
        assert MoveFlag.BULLET.value > 0

    def test_bite_flag_exists(self):
        """Bite flag for biting moves (Strong Jaw)."""
        assert MoveFlag.BITE.value > 0

    def test_punch_flag_exists(self):
        """Punch flag for punching moves (Iron Fist)."""
        assert MoveFlag.PUNCH.value > 0

    def test_powder_flag_exists(self):
        """Powder flag for powder moves (blocked by Grass/Overcoat)."""
        assert MoveFlag.POWDER.value > 0

    def test_dance_flag_exists(self):
        """Dance flag for dance moves (Dancer ability)."""
        assert MoveFlag.DANCE.value > 0

    def test_slicing_flag_exists(self):
        """Slicing flag for slicing moves (Sharpness ability)."""
        assert MoveFlag.SLICING.value > 0

    def test_wind_flag_exists(self):
        """Wind flag for wind moves (Wind Rider/Power abilities)."""
        assert MoveFlag.WIND.value > 0

    def test_heal_flag_exists(self):
        """Heal flag for healing moves."""
        assert MoveFlag.HEAL.value > 0

    def test_defrost_flag_exists(self):
        """Defrost flag for moves that thaw the user."""
        assert MoveFlag.DEFROST.value > 0

    def test_bypasssub_flag_exists(self):
        """Bypass Substitute flag."""
        assert MoveFlag.BYPASSSUB.value > 0


class TestMoveFlagCombinations:
    """Test that flags can be combined correctly."""

    def test_combine_contact_and_protect(self):
        """Should be able to combine contact and protect flags."""
        combined = MoveFlag.CONTACT | MoveFlag.PROTECT
        assert combined & MoveFlag.CONTACT
        assert combined & MoveFlag.PROTECT
        assert not (combined & MoveFlag.SOUND)

    def test_standard_attack_combination(self):
        """STANDARD_ATTACK should have contact, protect, mirror."""
        assert STANDARD_ATTACK & MoveFlag.CONTACT
        assert STANDARD_ATTACK & MoveFlag.PROTECT
        assert STANDARD_ATTACK & MoveFlag.MIRROR

    def test_special_attack_combination(self):
        """SPECIAL_ATTACK should have protect and mirror but not contact."""
        assert not (SPECIAL_ATTACK & MoveFlag.CONTACT)
        assert SPECIAL_ATTACK & MoveFlag.PROTECT
        assert SPECIAL_ATTACK & MoveFlag.MIRROR

    def test_status_move_combination(self):
        """STATUS_MOVE should have reflectable."""
        assert STATUS_MOVE & MoveFlag.REFLECTABLE

    def test_multiple_flags_combination(self):
        """Should handle multiple flag combinations."""
        flags = MoveFlag.CONTACT | MoveFlag.PUNCH | MoveFlag.PROTECT
        assert flags & MoveFlag.CONTACT
        assert flags & MoveFlag.PUNCH
        assert flags & MoveFlag.PROTECT
        assert not (flags & MoveFlag.SOUND)
        assert not (flags & MoveFlag.BITE)


class TestSecondaryEffectStructure:
    """Test SecondaryEffect dataclass for move secondary effects."""

    def test_create_burn_chance_effect(self):
        """Create a secondary effect that may burn."""
        effect = SecondaryEffect(chance=10, status="brn")
        assert effect.chance == 10
        assert effect.status == "brn"

    def test_create_paralysis_chance_effect(self):
        """Create a secondary effect that may paralyze."""
        effect = SecondaryEffect(chance=30, status="par")
        assert effect.chance == 30
        assert effect.status == "par"

    def test_create_flinch_chance_effect(self):
        """Create a secondary effect that may cause flinch."""
        effect = SecondaryEffect(chance=30, volatile_status="flinch")
        assert effect.chance == 30
        assert effect.volatile_status == "flinch"

    def test_create_stat_drop_effect(self):
        """Create a secondary effect that lowers stats."""
        effect = SecondaryEffect(chance=10, boosts={"spe": -1})
        assert effect.chance == 10
        assert effect.boosts == {"spe": -1}

    def test_create_self_boost_effect(self):
        """Create a secondary effect that boosts user's stats."""
        effect = SecondaryEffect(chance=100, self_boosts={"atk": 1})
        assert effect.chance == 100
        assert effect.self_boosts == {"atk": 1}

    def test_secondary_effect_is_frozen(self):
        """SecondaryEffect should be immutable."""
        effect = SecondaryEffect(chance=50, status="psn")
        with pytest.raises(Exception):
            effect.chance = 100


class TestMoveDataCreation:
    """Test MoveData dataclass creation with various configurations."""

    def test_create_basic_physical_move(self):
        """Create a basic physical attack like Tackle."""
        move = MoveData(
            id=1,
            name="Tackle",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=40,
            accuracy=100,
            pp=35,
            flags=MoveFlag.CONTACT | MoveFlag.PROTECT,
        )
        assert move.id == 1
        assert move.name == "Tackle"
        assert move.type == Type.NORMAL
        assert move.category == MoveCategory.PHYSICAL
        assert move.base_power == 40
        assert move.accuracy == 100
        assert move.pp == 35

    def test_create_special_move_with_secondary(self):
        """Create a special move with secondary effect like Flamethrower."""
        move = MoveData(
            id=2,
            name="Flamethrower",
            type=Type.FIRE,
            category=MoveCategory.SPECIAL,
            base_power=90,
            accuracy=100,
            pp=15,
            secondary=SecondaryEffect(chance=10, status="brn"),
        )
        assert move.category == MoveCategory.SPECIAL
        assert move.secondary is not None
        assert move.secondary.chance == 10
        assert move.secondary.status == "brn"

    def test_create_status_move(self):
        """Create a status move like Thunder Wave."""
        move = MoveData(
            id=3,
            name="Thunder Wave",
            type=Type.ELECTRIC,
            category=MoveCategory.STATUS,
            base_power=0,
            accuracy=90,
            pp=20,
        )
        assert move.category == MoveCategory.STATUS
        assert move.base_power == 0
        assert move.is_status

    def test_create_never_miss_move(self):
        """Create a move that never misses (accuracy=None)."""
        move = MoveData(
            id=4,
            name="Aerial Ace",
            type=Type.FLYING,
            category=MoveCategory.PHYSICAL,
            base_power=60,
            accuracy=None,
            pp=20,
            flags=MoveFlag.CONTACT | MoveFlag.PROTECT | MoveFlag.SLICING,
        )
        assert move.accuracy is None

    def test_create_priority_move(self):
        """Create a priority move like Quick Attack."""
        move = MoveData(
            id=5,
            name="Quick Attack",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=40,
            accuracy=100,
            pp=30,
            priority=1,
        )
        assert move.priority == 1

    def test_create_negative_priority_move(self):
        """Create a negative priority move like Avalanche."""
        move = MoveData(
            id=6,
            name="Avalanche",
            type=Type.ICE,
            category=MoveCategory.PHYSICAL,
            base_power=60,
            accuracy=100,
            pp=10,
            priority=-4,
        )
        assert move.priority == -4

    def test_create_high_crit_move(self):
        """Create a high crit ratio move like Slash."""
        move = MoveData(
            id=7,
            name="Slash",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=70,
            accuracy=100,
            pp=20,
            crit_ratio=2,
        )
        assert move.crit_ratio == 2

    def test_create_drain_move(self):
        """Create a drain move like Drain Punch."""
        move = MoveData(
            id=8,
            name="Drain Punch",
            type=Type.FIGHTING,
            category=MoveCategory.PHYSICAL,
            base_power=75,
            accuracy=100,
            pp=10,
            drain=0.5,
            flags=MoveFlag.CONTACT | MoveFlag.PROTECT | MoveFlag.PUNCH | MoveFlag.HEAL,
        )
        assert move.drain == 0.5

    def test_create_recoil_move(self):
        """Create a recoil move like Flare Blitz."""
        move = MoveData(
            id=9,
            name="Flare Blitz",
            type=Type.FIRE,
            category=MoveCategory.PHYSICAL,
            base_power=120,
            accuracy=100,
            pp=15,
            recoil=0.33,
            flags=MoveFlag.CONTACT | MoveFlag.PROTECT | MoveFlag.DEFROST,
        )
        assert move.recoil == 0.33

    def test_create_multi_hit_move(self):
        """Create a multi-hit move like Bullet Seed."""
        move = MoveData(
            id=10,
            name="Bullet Seed",
            type=Type.GRASS,
            category=MoveCategory.PHYSICAL,
            base_power=25,
            accuracy=100,
            pp=30,
            multi_hit=(2, 5),
            flags=MoveFlag.PROTECT | MoveFlag.BULLET,
        )
        assert move.multi_hit == (2, 5)


class TestMoveDataProperties:
    """Test computed properties on MoveData."""

    def test_is_status_true_for_status_moves(self):
        """is_status should return True for status category moves."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.STATUS,
        )
        assert move.is_status is True

    def test_is_status_false_for_physical_moves(self):
        """is_status should return False for physical moves."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, base_power=50,
        )
        assert move.is_status is False

    def test_is_status_false_for_special_moves(self):
        """is_status should return False for special moves."""
        move = MoveData(
            id=1, name="Test", type=Type.FIRE,
            category=MoveCategory.SPECIAL, base_power=80,
        )
        assert move.is_status is False

    def test_makes_contact_true_with_contact_flag(self):
        """makes_contact should return True if CONTACT flag is set."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, base_power=50,
            flags=MoveFlag.CONTACT,
        )
        assert move.makes_contact is True

    def test_makes_contact_false_without_contact_flag(self):
        """makes_contact should return False if CONTACT flag is not set."""
        move = MoveData(
            id=1, name="Test", type=Type.FIRE,
            category=MoveCategory.SPECIAL, base_power=80,
            flags=MoveFlag.PROTECT,
        )
        assert move.makes_contact is False

    def test_can_protect_true_with_protect_flag(self):
        """can_protect should return True if PROTECT flag is set."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, base_power=50,
            flags=MoveFlag.PROTECT,
        )
        assert move.can_protect is True

    def test_can_protect_false_without_protect_flag(self):
        """can_protect should return False if PROTECT flag is not set."""
        move = MoveData(
            id=1, name="Test", type=Type.PSYCHIC,
            category=MoveCategory.STATUS,
            flags=MoveFlag.NONE,
        )
        assert move.can_protect is False


class TestMoveDataImmutability:
    """Test that MoveData is immutable (frozen dataclass)."""

    def test_cannot_modify_name(self):
        """Should not be able to modify move name."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        with pytest.raises(Exception):
            move.name = "Modified"

    def test_cannot_modify_base_power(self):
        """Should not be able to modify base power."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, base_power=50,
        )
        with pytest.raises(Exception):
            move.base_power = 100

    def test_cannot_modify_type(self):
        """Should not be able to modify move type."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        with pytest.raises(Exception):
            move.type = Type.FIRE


class TestMoveDefaults:
    """Test default values for optional MoveData fields."""

    def test_default_base_power_is_zero(self):
        """Default base_power should be 0."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.STATUS,
        )
        assert move.base_power == 0

    def test_default_accuracy_is_100(self):
        """Default accuracy should be 100."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.accuracy == 100

    def test_default_pp_is_5(self):
        """Default PP should be 5."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.pp == 5

    def test_default_priority_is_zero(self):
        """Default priority should be 0."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.priority == 0

    def test_default_target_is_normal(self):
        """Default target should be NORMAL."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.target == MoveTarget.NORMAL

    def test_default_flags_is_none(self):
        """Default flags should be NONE."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.flags == MoveFlag.NONE

    def test_default_crit_ratio_is_1(self):
        """Default crit_ratio should be 1."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.crit_ratio == 1

    def test_default_drain_is_zero(self):
        """Default drain should be 0.0."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.drain == 0.0

    def test_default_recoil_is_zero(self):
        """Default recoil should be 0.0."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.recoil == 0.0

    def test_default_secondary_is_none(self):
        """Default secondary should be None."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.secondary is None

    def test_default_multi_hit_is_none(self):
        """Default multi_hit should be None."""
        move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        assert move.multi_hit is None


class TestCategoryByNameMapping:
    """Test CATEGORY_BY_NAME string to enum mapping."""

    def test_status_maps_correctly(self):
        assert CATEGORY_BY_NAME["status"] == MoveCategory.STATUS

    def test_physical_maps_correctly(self):
        assert CATEGORY_BY_NAME["physical"] == MoveCategory.PHYSICAL

    def test_special_maps_correctly(self):
        assert CATEGORY_BY_NAME["special"] == MoveCategory.SPECIAL


class TestTargetByNameMapping:
    """Test TARGET_BY_NAME string to enum mapping."""

    def test_normal_maps_correctly(self):
        assert TARGET_BY_NAME["normal"] == MoveTarget.NORMAL

    def test_self_maps_correctly(self):
        assert TARGET_BY_NAME["self"] == MoveTarget.SELF

    def test_all_adjacent_foes_maps_correctly(self):
        assert TARGET_BY_NAME["allAdjacentFoes"] == MoveTarget.ALL_ADJACENT_FOES

    def test_any_maps_correctly(self):
        assert TARGET_BY_NAME["any"] == MoveTarget.ANY


class TestFlagByNameMapping:
    """Test FLAG_BY_NAME string to enum mapping."""

    def test_contact_maps_correctly(self):
        assert FLAG_BY_NAME["contact"] == MoveFlag.CONTACT

    def test_protect_maps_correctly(self):
        assert FLAG_BY_NAME["protect"] == MoveFlag.PROTECT

    def test_sound_maps_correctly(self):
        assert FLAG_BY_NAME["sound"] == MoveFlag.SOUND

    def test_punch_maps_correctly(self):
        assert FLAG_BY_NAME["punch"] == MoveFlag.PUNCH

    def test_bite_maps_correctly(self):
        assert FLAG_BY_NAME["bite"] == MoveFlag.BITE

    def test_dance_maps_correctly(self):
        assert FLAG_BY_NAME["dance"] == MoveFlag.DANCE


class TestTypicalMoveExamples:
    """Test creating typical moves from the games."""

    def test_earthquake_spread_move(self):
        """Earthquake: spread Ground move that hits all adjacent."""
        move = MoveData(
            id=89,
            name="Earthquake",
            type=Type.GROUND,
            category=MoveCategory.PHYSICAL,
            base_power=100,
            accuracy=100,
            pp=10,
            target=MoveTarget.ALL_ADJACENT,
            flags=MoveFlag.PROTECT | MoveFlag.MIRROR,
        )
        assert move.target == MoveTarget.ALL_ADJACENT
        assert not move.makes_contact

    def test_protect_status_move(self):
        """Protect: priority +4 status move targeting self."""
        move = MoveData(
            id=182,
            name="Protect",
            type=Type.NORMAL,
            category=MoveCategory.STATUS,
            base_power=0,
            accuracy=None,
            pp=10,
            priority=4,
            target=MoveTarget.SELF,
        )
        assert move.priority == 4
        assert move.target == MoveTarget.SELF
        assert move.is_status

    def test_stealth_rock_hazard(self):
        """Stealth Rock: targets foe's side."""
        move = MoveData(
            id=446,
            name="Stealth Rock",
            type=Type.ROCK,
            category=MoveCategory.STATUS,
            base_power=0,
            accuracy=None,
            pp=20,
            target=MoveTarget.FOE_SIDE,
            flags=MoveFlag.REFLECTABLE,
        )
        assert move.target == MoveTarget.FOE_SIDE

    def test_extreme_speed_priority(self):
        """Extreme Speed: +2 priority."""
        move = MoveData(
            id=245,
            name="Extreme Speed",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=80,
            accuracy=100,
            pp=5,
            priority=2,
            flags=MoveFlag.CONTACT | MoveFlag.PROTECT | MoveFlag.MIRROR,
        )
        assert move.priority == 2

    def test_scald_burn_chance(self):
        """Scald: 30% burn chance special Water move."""
        move = MoveData(
            id=503,
            name="Scald",
            type=Type.WATER,
            category=MoveCategory.SPECIAL,
            base_power=80,
            accuracy=100,
            pp=15,
            secondary=SecondaryEffect(chance=30, status="brn"),
            flags=MoveFlag.PROTECT | MoveFlag.MIRROR | MoveFlag.DEFROST,
        )
        assert move.secondary.chance == 30
        assert move.secondary.status == "brn"
        assert move.flags & MoveFlag.DEFROST
