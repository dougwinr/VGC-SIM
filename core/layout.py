"""Packed Pokemon array layout definitions.

This module defines the indices used to access Pokemon data in packed NumPy arrays.
All Pokemon data is stored in a single 1D array per Pokemon for cache efficiency.

Array Layout (indices 0-39):
    0-7:   Identity (species, level, nature, ability, item, types, tera)
    8-13:  Calculated stats (HP, Atk, Def, SpA, SpD, Spe)
    14-16: Battle state (current HP, status, status counter)
    17-23: Stat stages (Atk, Def, SpA, SpD, Spe, Acc, Eva)
    24-27: Move IDs (4 move slots)
    28-31: Move PP (current PP for each slot)
    32-37: IVs (HP, Atk, Def, SpA, SpD, Spe)
    38-43: EVs (HP, Atk, Def, SpA, SpD, Spe)
    44+:   Volatile status flags
"""

# =============================================================================
# Pokemon Array Indices (Single Source of Truth)
# =============================================================================

# --- Identity (0-7) ---
P_SPECIES = 0          # Species ID
P_LEVEL = 1            # Level (1-100)
P_NATURE = 2           # Nature ID
P_ABILITY = 3          # Ability ID
P_ITEM = 4             # Item ID (0 = no item)
P_TYPE1 = 5            # Primary type ID
P_TYPE2 = 6            # Secondary type ID (-1 if single-typed)
P_TERA_TYPE = 7        # Tera type ID (-1 if not terastallized)

# --- Calculated Stats (8-13) ---
P_STAT_HP = 8          # Max HP
P_STAT_ATK = 9         # Attack
P_STAT_DEF = 10        # Defense
P_STAT_SPA = 11        # Special Attack
P_STAT_SPD = 12        # Special Defense
P_STAT_SPE = 13        # Speed

# --- Battle State (14-16) ---
P_CURRENT_HP = 14      # Current HP
P_STATUS = 15          # Non-volatile status (0=none, 1=burn, etc.)
P_STATUS_COUNTER = 16  # Status duration counter (sleep turns, toxic counter)

# --- Stat Stages (17-23) ---
P_STAGE_ATK = 17       # Attack stage (-6 to +6)
P_STAGE_DEF = 18       # Defense stage
P_STAGE_SPA = 19       # Special Attack stage
P_STAGE_SPD = 20       # Special Defense stage
P_STAGE_SPE = 21       # Speed stage
P_STAGE_ACC = 22       # Accuracy stage
P_STAGE_EVA = 23       # Evasion stage

# --- Move Slots (24-27) ---
P_MOVE1 = 24           # Move 1 ID
P_MOVE2 = 25           # Move 2 ID
P_MOVE3 = 26           # Move 3 ID
P_MOVE4 = 27           # Move 4 ID

# --- Move PP (28-31) ---
P_PP1 = 28             # Move 1 current PP
P_PP2 = 29             # Move 2 current PP
P_PP3 = 30             # Move 3 current PP
P_PP4 = 31             # Move 4 current PP

# --- IVs (32-37) ---
P_IV_HP = 32           # HP IV (0-31)
P_IV_ATK = 33          # Attack IV
P_IV_DEF = 34          # Defense IV
P_IV_SPA = 35          # Special Attack IV
P_IV_SPD = 36          # Special Defense IV
P_IV_SPE = 37          # Speed IV

# --- EVs (38-43) ---
P_EV_HP = 38           # HP EV (0-252)
P_EV_ATK = 39          # Attack EV
P_EV_DEF = 40          # Defense EV
P_EV_SPA = 41          # Special Attack EV
P_EV_SPD = 42          # Special Defense EV
P_EV_SPE = 43          # Speed EV

# --- Volatile Flags (44+) ---
P_VOL_PROTECT = 44           # Protect active this turn
P_VOL_SUBSTITUTE = 45        # Has Substitute
P_VOL_SUBSTITUTE_HP = 46     # Substitute remaining HP
P_VOL_ENCORE = 47            # Encore active (turns remaining)
P_VOL_TAUNT = 48             # Taunt active (turns remaining)
P_VOL_TORMENT = 49           # Torment active
P_VOL_DISABLE = 50           # Disabled move slot
P_VOL_DISABLE_TURNS = 51     # Disable turns remaining
P_VOL_CONFUSION = 52         # Confusion turns remaining
P_VOL_ATTRACT = 53           # Attracted to opponent slot
P_VOL_FLINCH = 54            # Flinched this turn
P_VOL_FOCUS_ENERGY = 55      # Focus Energy active (+2 crit stage)
P_VOL_LEECH_SEED = 56        # Leech Seeded
P_VOL_CURSE = 57             # Cursed (Ghost curse)
P_VOL_PERISH_COUNT = 58      # Perish Song counter (-1 if not active)
P_VOL_TRAPPED = 59           # Partially trapped (Bind, Wrap, etc.)
P_VOL_TRAPPED_TURNS = 60     # Trapped turns remaining
P_VOL_MUST_RECHARGE = 61     # Must recharge next turn
P_VOL_BIDE = 62              # Bide active (turns remaining)
P_VOL_BIDE_DAMAGE = 63       # Bide accumulated damage
P_VOL_CHARGING = 64          # Charging a two-turn move
P_VOL_CHARGING_MOVE = 65     # Move being charged
P_VOL_CHOICE_LOCKED = 66     # Choice item locked move slot
P_VOL_LAST_MOVE = 67         # Last move used (ID)
P_VOL_LAST_MOVE_TURN = 68    # Turn last move was used
P_VOL_TIMES_ATTACKED = 69    # Times attacked this turn (for Rage, etc.)
P_VOL_STOCKPILE = 70         # Stockpile count (0-3)
P_VOL_FLASH_FIRE = 71        # Flash Fire activated
P_VOL_ABILITY_SUPPRESSED = 72  # Ability suppressed (Gastro Acid)
P_VOL_TRANSFORM = 73         # Transformed (stores original species)
P_VOL_MINIMIZE = 74          # Used Minimize
P_VOL_DEFENSE_CURL = 75      # Used Defense Curl
P_VOL_DESTINY_BOND = 76      # Destiny Bond active
P_VOL_GRUDGE = 77            # Grudge active
P_VOL_INGRAIN = 78           # Ingrain active
P_VOL_MAGNET_RISE = 79       # Magnet Rise turns remaining
P_VOL_AQUA_RING = 80         # Aqua Ring active
P_VOL_HEAL_BLOCK = 81        # Heal Block turns remaining
P_VOL_EMBARGO = 82           # Embargo turns remaining
P_VOL_POWER_TRICK = 83       # Power Trick active
P_VOL_TYPE_ADDED = 84        # Additional type (Forest's Curse/Trick-or-Treat)
P_VOL_SMACKED_DOWN = 85      # Smack Down (grounded)
P_VOL_TELEKINESIS = 86       # Telekinesis turns remaining

# Total array size
POKEMON_ARRAY_SIZE = 87

# =============================================================================
# Status Constants
# =============================================================================

STATUS_NONE = 0
STATUS_BURN = 1
STATUS_FREEZE = 2
STATUS_PARALYSIS = 3
STATUS_POISON = 4
STATUS_BADLY_POISONED = 5
STATUS_SLEEP = 6

# Status name mapping
STATUS_NAMES = {
    STATUS_NONE: "none",
    STATUS_BURN: "brn",
    STATUS_FREEZE: "frz",
    STATUS_PARALYSIS: "par",
    STATUS_POISON: "psn",
    STATUS_BADLY_POISONED: "tox",
    STATUS_SLEEP: "slp",
}

# =============================================================================
# Stat Stage Multipliers
# =============================================================================

# Stage multipliers for stats (stages -6 to +6)
# Index with stage + 6 to get multiplier numerator/denominator
STAGE_MULTIPLIERS = [
    (2, 8),   # -6: 2/8 = 0.25
    (2, 7),   # -5: 2/7 ≈ 0.286
    (2, 6),   # -4: 2/6 ≈ 0.333
    (2, 5),   # -3: 2/5 = 0.4
    (2, 4),   # -2: 2/4 = 0.5
    (2, 3),   # -1: 2/3 ≈ 0.667
    (2, 2),   #  0: 2/2 = 1.0
    (3, 2),   # +1: 3/2 = 1.5
    (4, 2),   # +2: 4/2 = 2.0
    (5, 2),   # +3: 5/2 = 2.5
    (6, 2),   # +4: 6/2 = 3.0
    (7, 2),   # +5: 7/2 = 3.5
    (8, 2),   # +6: 8/2 = 4.0
]

# Accuracy/Evasion stage multipliers (different formula)
ACC_EVA_MULTIPLIERS = [
    (3, 9),   # -6: 3/9 ≈ 0.333
    (3, 8),   # -5: 3/8 = 0.375
    (3, 7),   # -4: 3/7 ≈ 0.429
    (3, 6),   # -3: 3/6 = 0.5
    (3, 5),   # -2: 3/5 = 0.6
    (3, 4),   # -1: 3/4 = 0.75
    (3, 3),   #  0: 3/3 = 1.0
    (4, 3),   # +1: 4/3 ≈ 1.333
    (5, 3),   # +2: 5/3 ≈ 1.667
    (6, 3),   # +3: 6/3 = 2.0
    (7, 3),   # +4: 7/3 ≈ 2.333
    (8, 3),   # +5: 8/3 ≈ 2.667
    (9, 3),   # +6: 9/3 = 3.0
]


def get_stage_multiplier(stage: int) -> float:
    """Get the stat multiplier for a given stage (-6 to +6).

    Args:
        stage: Stage value from -6 to +6

    Returns:
        Multiplier as a float
    """
    stage = max(-6, min(6, stage))  # Clamp to valid range
    num, denom = STAGE_MULTIPLIERS[stage + 6]
    return num / denom


def get_acc_eva_multiplier(stage: int) -> float:
    """Get the accuracy/evasion multiplier for a given stage.

    Args:
        stage: Stage value from -6 to +6

    Returns:
        Multiplier as a float
    """
    stage = max(-6, min(6, stage))
    num, denom = ACC_EVA_MULTIPLIERS[stage + 6]
    return num / denom


# =============================================================================
# Index Ranges (for iteration)
# =============================================================================

# Stat indices
STAT_INDICES = (P_STAT_HP, P_STAT_ATK, P_STAT_DEF, P_STAT_SPA, P_STAT_SPD, P_STAT_SPE)

# Stage indices (excludes HP since HP has no stage)
STAGE_INDICES = (P_STAGE_ATK, P_STAGE_DEF, P_STAGE_SPA, P_STAGE_SPD, P_STAGE_SPE)

# Move slot indices
MOVE_INDICES = (P_MOVE1, P_MOVE2, P_MOVE3, P_MOVE4)

# PP indices
PP_INDICES = (P_PP1, P_PP2, P_PP3, P_PP4)

# IV indices
IV_INDICES = (P_IV_HP, P_IV_ATK, P_IV_DEF, P_IV_SPA, P_IV_SPD, P_IV_SPE)

# EV indices
EV_INDICES = (P_EV_HP, P_EV_ATK, P_EV_DEF, P_EV_SPA, P_EV_SPD, P_EV_SPE)
