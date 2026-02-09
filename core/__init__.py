"""Pokemon battle simulator core module.

This package provides the core battle runtime with:
- Packed Pokemon layout for NumPy arrays
- Stat calculation functions
- Battle state management
"""
from .layout import (
    # Pokemon array indices
    P_SPECIES,
    P_LEVEL,
    P_NATURE,
    P_ABILITY,
    P_ITEM,
    P_TYPE1,
    P_TYPE2,
    P_TERA_TYPE,
    P_STAT_HP,
    P_STAT_ATK,
    P_STAT_DEF,
    P_STAT_SPA,
    P_STAT_SPD,
    P_STAT_SPE,
    P_CURRENT_HP,
    P_STATUS,
    P_STATUS_COUNTER,
    P_STAGE_ATK,
    P_STAGE_DEF,
    P_STAGE_SPA,
    P_STAGE_SPD,
    P_STAGE_SPE,
    P_STAGE_ACC,
    P_STAGE_EVA,
    P_MOVE1,
    P_MOVE2,
    P_MOVE3,
    P_MOVE4,
    POKEMON_ARRAY_SIZE,
    # Status constants
    STATUS_NONE,
    STATUS_BURN,
    STATUS_FREEZE,
    STATUS_PARALYSIS,
    STATUS_POISON,
    STATUS_BADLY_POISONED,
    STATUS_SLEEP,
)

from .pokemon import (
    Pokemon,
    calculate_stat,
    calculate_hp,
    calculate_all_stats,
)

from .battle_state import (
    BattleState,
    BattlePRNG,
    # Side condition indices
    SC_REFLECT,
    SC_LIGHT_SCREEN,
    SC_AURORA_VEIL,
    SC_SAFEGUARD,
    SC_MIST,
    SC_TAILWIND,
    SC_LUCKY_CHANT,
    SC_SPIKES,
    SC_TOXIC_SPIKES,
    SC_STEALTH_ROCK,
    SC_STICKY_WEB,
    SC_WIDE_GUARD,
    SC_QUICK_GUARD,
    SC_MAT_BLOCK,
    SC_CRAFTY_SHIELD,
    SC_WISH,
    SC_WISH_AMOUNT,
    SC_HEALING_WISH,
    SC_LUNAR_DANCE,
    SIDE_CONDITION_SIZE,
    # Slot condition indices
    SLOT_FUTURE_SIGHT,
    SLOT_FUTURE_SIGHT_DMG,
    SLOT_FUTURE_SIGHT_USER,
    SLOT_DOOM_DESIRE,
    SLOT_DOOM_DESIRE_DMG,
    SLOT_DOOM_DESIRE_USER,
    SLOT_HEALING_WISH,
    SLOT_LUNAR_DANCE,
    SLOT_CONDITION_SIZE,
    # Pseudo-weather indices
    PW_TRICK_ROOM,
    PW_GRAVITY,
    PW_MAGIC_ROOM,
    PW_WONDER_ROOM,
    PW_FAIRY_LOCK,
    PW_MUD_SPORT,
    PW_WATER_SPORT,
    PW_ION_DELUGE,
    PSEUDO_WEATHER_SIZE,
    # Field indices
    FIELD_WEATHER,
    FIELD_WEATHER_TURNS,
    FIELD_TERRAIN,
    FIELD_TERRAIN_TURNS,
    FIELD_TRICK_ROOM,
    FIELD_GRAVITY,
    FIELD_MAGIC_ROOM,
    FIELD_WONDER_ROOM,
    FIELD_MUD_SPORT,
    FIELD_WATER_SPORT,
    FIELD_ION_DELUGE,
    FIELD_FAIRY_LOCK,
    FIELD_STATE_SIZE,
    # Weather constants
    WEATHER_NONE,
    WEATHER_SUN,
    WEATHER_RAIN,
    WEATHER_SAND,
    WEATHER_HAIL,
    WEATHER_SNOW,
    WEATHER_HARSH_SUN,
    WEATHER_HEAVY_RAIN,
    WEATHER_STRONG_WINDS,
    WEATHER_NAMES,
    # Terrain constants
    TERRAIN_NONE,
    TERRAIN_ELECTRIC,
    TERRAIN_GRASSY,
    TERRAIN_MISTY,
    TERRAIN_PSYCHIC,
    TERRAIN_NAMES,
)

from .battle import (
    BattleEngine,
    Action,
    ActionType,
    Choice,
    compare_actions,
    sort_actions,
    resolve_targets,
)

from .events import (
    EventType,
    BattleEvent,
    create_switch_event,
    create_move_event,
    create_damage_event,
    create_heal_event,
    create_faint_event,
    create_status_event,
    create_boost_event,
    create_weather_event,
    create_terrain_event,
    create_win_event,
    create_choice_event,
)

from .battle_log import (
    BattleLog,
    BattleLogMetadata,
    BattleRecorder,
    replay_from_choices,
    compare_states,
    verify_replay_determinism,
)

from .damage import (
    DamageResult,
    calculate_damage,
    calculate_base_damage,
    calculate_confusion_damage,
    calculate_recoil,
    calculate_drain,
    calculate_type_effectiveness,
    get_stab_modifier,
    get_weather_modifier,
    get_terrain_modifier,
    is_grounded,
    get_crit_chance,
    calculate_crit_stage,
    calculate_accuracy,
    check_accuracy,
    calculate_fixed_damage,
    is_ohko_move,
    calculate_ohko_accuracy,
    get_multi_hit_count,
    get_parental_bond_modifier,
    trunc,
    clamp,
    get_stat_with_stage,
    GRASSY_TERRAIN_WEAK_MOVES,
    # Stellar Tera and Tera power boost
    TERA_STELLAR,
    get_stellar_tera_modifier,
    get_tera_power_boost,
    # Additional recoil types
    calculate_struggle_recoil,
    calculate_max_hp_recoil,
    MAX_HP_RECOIL_MOVES,
    get_move_max_hp_recoil,
    # Spread and protect modifiers
    get_spread_modifier,
    get_broken_protect_modifier,
    get_explosion_defense_modifier,
    calculate_minimum_damage,
)

__all__ = [
    # Layout indices
    "P_SPECIES", "P_LEVEL", "P_NATURE", "P_ABILITY", "P_ITEM",
    "P_TYPE1", "P_TYPE2", "P_TERA_TYPE",
    "P_STAT_HP", "P_STAT_ATK", "P_STAT_DEF", "P_STAT_SPA", "P_STAT_SPD", "P_STAT_SPE",
    "P_CURRENT_HP", "P_STATUS", "P_STATUS_COUNTER",
    "P_STAGE_ATK", "P_STAGE_DEF", "P_STAGE_SPA", "P_STAGE_SPD", "P_STAGE_SPE",
    "P_STAGE_ACC", "P_STAGE_EVA",
    "P_MOVE1", "P_MOVE2", "P_MOVE3", "P_MOVE4",
    "POKEMON_ARRAY_SIZE",
    # Status
    "STATUS_NONE", "STATUS_BURN", "STATUS_FREEZE", "STATUS_PARALYSIS",
    "STATUS_POISON", "STATUS_BADLY_POISONED", "STATUS_SLEEP",
    # Pokemon
    "Pokemon", "calculate_stat", "calculate_hp", "calculate_all_stats",
    # Battle State
    "BattleState", "BattlePRNG",
    # Side conditions
    "SC_REFLECT", "SC_LIGHT_SCREEN", "SC_AURORA_VEIL", "SC_SAFEGUARD",
    "SC_MIST", "SC_TAILWIND", "SC_LUCKY_CHANT", "SC_SPIKES", "SC_TOXIC_SPIKES",
    "SC_STEALTH_ROCK", "SC_STICKY_WEB", "SC_WIDE_GUARD", "SC_QUICK_GUARD",
    "SC_MAT_BLOCK", "SC_CRAFTY_SHIELD", "SC_WISH", "SC_WISH_AMOUNT",
    "SC_HEALING_WISH", "SC_LUNAR_DANCE", "SIDE_CONDITION_SIZE",
    # Slot conditions
    "SLOT_FUTURE_SIGHT", "SLOT_FUTURE_SIGHT_DMG", "SLOT_FUTURE_SIGHT_USER",
    "SLOT_DOOM_DESIRE", "SLOT_DOOM_DESIRE_DMG", "SLOT_DOOM_DESIRE_USER",
    "SLOT_HEALING_WISH", "SLOT_LUNAR_DANCE", "SLOT_CONDITION_SIZE",
    # Pseudo-weather
    "PW_TRICK_ROOM", "PW_GRAVITY", "PW_MAGIC_ROOM", "PW_WONDER_ROOM",
    "PW_FAIRY_LOCK", "PW_MUD_SPORT", "PW_WATER_SPORT", "PW_ION_DELUGE",
    "PSEUDO_WEATHER_SIZE",
    # Field conditions
    "FIELD_WEATHER", "FIELD_WEATHER_TURNS", "FIELD_TERRAIN", "FIELD_TERRAIN_TURNS",
    "FIELD_TRICK_ROOM", "FIELD_GRAVITY", "FIELD_MAGIC_ROOM", "FIELD_WONDER_ROOM",
    "FIELD_MUD_SPORT", "FIELD_WATER_SPORT", "FIELD_ION_DELUGE", "FIELD_FAIRY_LOCK",
    "FIELD_STATE_SIZE",
    # Weather
    "WEATHER_NONE", "WEATHER_SUN", "WEATHER_RAIN", "WEATHER_SAND", "WEATHER_HAIL", "WEATHER_SNOW",
    "WEATHER_HARSH_SUN", "WEATHER_HEAVY_RAIN", "WEATHER_STRONG_WINDS", "WEATHER_NAMES",
    # Terrain
    "TERRAIN_NONE", "TERRAIN_ELECTRIC", "TERRAIN_GRASSY", "TERRAIN_MISTY", "TERRAIN_PSYCHIC",
    "TERRAIN_NAMES",
    # Damage
    "DamageResult", "calculate_damage", "calculate_base_damage",
    "calculate_confusion_damage", "calculate_recoil", "calculate_drain",
    "calculate_type_effectiveness", "get_stab_modifier", "get_weather_modifier",
    "get_terrain_modifier", "is_grounded", "GRASSY_TERRAIN_WEAK_MOVES",
    "get_crit_chance", "calculate_crit_stage",
    "calculate_accuracy", "check_accuracy",
    "calculate_fixed_damage", "is_ohko_move", "calculate_ohko_accuracy",
    "get_multi_hit_count", "get_parental_bond_modifier",
    "trunc", "clamp", "get_stat_with_stage",
    # Stellar Tera and Tera power boost
    "TERA_STELLAR", "get_stellar_tera_modifier", "get_tera_power_boost",
    # Additional recoil types
    "calculate_struggle_recoil", "calculate_max_hp_recoil",
    "MAX_HP_RECOIL_MOVES", "get_move_max_hp_recoil",
    # Spread and protect modifiers
    "get_spread_modifier", "get_broken_protect_modifier",
    "get_explosion_defense_modifier", "calculate_minimum_damage",
    # Battle Engine
    "BattleEngine", "Action", "ActionType", "Choice",
    "compare_actions", "sort_actions", "resolve_targets",
    # Events
    "EventType", "BattleEvent",
    "create_switch_event", "create_move_event", "create_damage_event",
    "create_heal_event", "create_faint_event", "create_status_event",
    "create_boost_event", "create_weather_event", "create_terrain_event",
    "create_win_event", "create_choice_event",
    # Battle Log
    "BattleLog", "BattleLogMetadata", "BattleRecorder",
    "replay_from_choices", "compare_states", "verify_replay_determinism",
]
