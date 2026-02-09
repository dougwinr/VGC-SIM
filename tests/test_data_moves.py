"""Tests for data/moves.py - Move dataclass and enums."""
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


class TestMoveCategory:
    """Tests for the MoveCategory enum."""

    def test_category_count(self):
        """Should have exactly 3 categories."""
        assert len(MoveCategory) == 3

    def test_category_values(self):
        """Categories should have expected values."""
        assert MoveCategory.STATUS == 0
        assert MoveCategory.PHYSICAL == 1
        assert MoveCategory.SPECIAL == 2

    def test_category_by_name_mapping(self):
        """Should map category strings to enums."""
        assert CATEGORY_BY_NAME["status"] == MoveCategory.STATUS
        assert CATEGORY_BY_NAME["physical"] == MoveCategory.PHYSICAL
        assert CATEGORY_BY_NAME["special"] == MoveCategory.SPECIAL


class TestMoveTarget:
    """Tests for the MoveTarget enum."""

    def test_target_count(self):
        """Should have expected number of targeting modes."""
        assert len(MoveTarget) >= 10  # At least 10 targeting modes

    def test_common_targets_exist(self):
        """Common targeting modes should be defined."""
        assert MoveTarget.NORMAL.value >= 0
        assert MoveTarget.SELF.value >= 0
        assert MoveTarget.ALL_ADJACENT_FOES.value >= 0
        assert MoveTarget.ANY.value >= 0

    def test_target_by_name_mapping(self):
        """Should map target strings to enums."""
        assert TARGET_BY_NAME["normal"] == MoveTarget.NORMAL
        assert TARGET_BY_NAME["self"] == MoveTarget.SELF
        assert TARGET_BY_NAME["allAdjacentFoes"] == MoveTarget.ALL_ADJACENT_FOES


class TestMoveFlag:
    """Tests for the MoveFlag bitflags."""

    def test_none_flag_is_zero(self):
        """NONE flag should be 0."""
        assert MoveFlag.NONE == 0

    def test_flags_are_powers_of_two(self):
        """Each flag (except NONE) should be a power of 2."""
        for flag in MoveFlag:
            if flag != MoveFlag.NONE:
                # Power of 2: only one bit set
                assert flag.value & (flag.value - 1) == 0

    def test_flags_are_unique(self):
        """Each flag should have a unique value."""
        values = [f.value for f in MoveFlag]
        assert len(values) == len(set(values))

    def test_flag_combinations(self):
        """Flags should combine correctly with bitwise OR."""
        combined = MoveFlag.CONTACT | MoveFlag.PROTECT
        assert combined & MoveFlag.CONTACT
        assert combined & MoveFlag.PROTECT
        assert not (combined & MoveFlag.SOUND)

    def test_flag_by_name_mapping(self):
        """Should map flag strings to enums."""
        assert FLAG_BY_NAME["contact"] == MoveFlag.CONTACT
        assert FLAG_BY_NAME["protect"] == MoveFlag.PROTECT
        assert FLAG_BY_NAME["sound"] == MoveFlag.SOUND


class TestSecondaryEffect:
    """Tests for the SecondaryEffect dataclass."""

    def test_create_status_effect(self):
        """Should create secondary effect with status."""
        effect = SecondaryEffect(chance=30, status="brn")
        assert effect.chance == 30
        assert effect.status == "brn"
        assert effect.volatile_status is None
        assert effect.boosts is None

    def test_create_stat_boost_effect(self):
        """Should create secondary effect with stat boosts."""
        effect = SecondaryEffect(chance=10, boosts={"spe": -1})
        assert effect.chance == 10
        assert effect.boosts == {"spe": -1}

    def test_secondary_effect_is_frozen(self):
        """SecondaryEffect should be immutable."""
        effect = SecondaryEffect(chance=100, status="par")
        with pytest.raises(Exception):  # FrozenInstanceError
            effect.chance = 50


class TestMoveData:
    """Tests for the MoveData dataclass."""

    def test_create_physical_move(self):
        """Should create a physical attack move."""
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

    def test_create_special_move(self):
        """Should create a special attack move."""
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

    def test_create_status_move(self):
        """Should create a status move."""
        move = MoveData(
            id=3,
            name="Thunder Wave",
            type=Type.ELECTRIC,
            category=MoveCategory.STATUS,
            base_power=0,
            accuracy=90,
            pp=20,
        )
        assert move.is_status
        assert move.base_power == 0

    def test_move_with_priority(self):
        """Should handle priority moves."""
        move = MoveData(
            id=4,
            name="Quick Attack",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            base_power=40,
            priority=1,
        )
        assert move.priority == 1

    def test_move_with_never_miss(self):
        """Should handle never-miss moves (accuracy=None)."""
        move = MoveData(
            id=5,
            name="Aerial Ace",
            type=Type.FLYING,
            category=MoveCategory.PHYSICAL,
            base_power=60,
            accuracy=None,  # Never misses
        )
        assert move.accuracy is None

    def test_move_is_frozen(self):
        """MoveData should be immutable."""
        move = MoveData(
            id=1,
            name="Test",
            type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            move.base_power = 100


class TestMoveProperties:
    """Tests for MoveData computed properties."""

    def test_is_status_property(self):
        """is_status should return True for status moves."""
        status_move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.STATUS,
        )
        physical_move = MoveData(
            id=2, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL, base_power=50,
        )
        assert status_move.is_status
        assert not physical_move.is_status

    def test_makes_contact_property(self):
        """makes_contact should check CONTACT flag."""
        contact_move = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            flags=MoveFlag.CONTACT,
        )
        ranged_move = MoveData(
            id=2, name="Test", type=Type.NORMAL,
            category=MoveCategory.SPECIAL,
            flags=MoveFlag.NONE,
        )
        assert contact_move.makes_contact
        assert not ranged_move.makes_contact

    def test_can_protect_property(self):
        """can_protect should check PROTECT flag."""
        protectable = MoveData(
            id=1, name="Test", type=Type.NORMAL,
            category=MoveCategory.PHYSICAL,
            flags=MoveFlag.PROTECT,
        )
        unprotectable = MoveData(
            id=2, name="Test", type=Type.NORMAL,
            category=MoveCategory.STATUS,
            flags=MoveFlag.NONE,
        )
        assert protectable.can_protect
        assert not unprotectable.can_protect


class TestFlagCombinations:
    """Tests for pre-defined flag combinations."""

    def test_standard_attack_flags(self):
        """STANDARD_ATTACK should include contact, protect, mirror."""
        assert STANDARD_ATTACK & MoveFlag.CONTACT
        assert STANDARD_ATTACK & MoveFlag.PROTECT
        assert STANDARD_ATTACK & MoveFlag.MIRROR

    def test_special_attack_flags(self):
        """SPECIAL_ATTACK should include protect and mirror but not contact."""
        assert not (SPECIAL_ATTACK & MoveFlag.CONTACT)
        assert SPECIAL_ATTACK & MoveFlag.PROTECT
        assert SPECIAL_ATTACK & MoveFlag.MIRROR

    def test_status_move_flags(self):
        """STATUS_MOVE should include reflectable."""
        assert STATUS_MOVE & MoveFlag.REFLECTABLE
