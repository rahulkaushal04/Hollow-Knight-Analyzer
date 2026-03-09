"""
Hallownest Codex save data model.

This module defines the canonical typed representation of a parsed
Hollow Knight save file.

All decrypted save data is converted into these dataclasses by
save_parser.py. The rest of the application must interact only with
these typed models and should not access raw dictionaries.

The model layer provides:

    - Strong typing for all save state
    - Structured grouping of game systems
    - Clear separation between gameplay systems
    - Safe defaults for partially parsed data
"""

from __future__ import annotations

from typing import Optional
from dataclasses import dataclass, field


# ------------------------------------------------------------
# Charm System
# ------------------------------------------------------------


@dataclass
class CharmState:
    """
    State of a single charm.

    Represents ownership and equip status along with metadata
    sourced from static game data.
    """

    id: int
    name: str

    owned: bool
    equipped: bool
    broken: bool
    unbreakable: bool

    notch_cost: int
    default_notch_cost: int

    area: str = ""
    description: str = ""
    how_to_get: str = ""


# ------------------------------------------------------------
# Boss System
# ------------------------------------------------------------


@dataclass
class BossState:
    """
    State of a single boss encounter.
    """

    id: str
    display_name: str

    category: str
    area: str

    defeated: bool
    kill_count: int

    dream_defeated: bool = False
    dream_kills: int = 0

    sub_area: str = ""
    difficulty: str = ""

    map_pixel_x: Optional[int] = None
    map_pixel_y: Optional[int] = None

    statue_key: Optional[str] = None


# ------------------------------------------------------------
# Dreamer System
# ------------------------------------------------------------


@dataclass
class DreamerState:
    """
    State of a single Dreamer seal.

    Dreamers are the three higher beings whose seals lock the
    Black Egg Temple. Each defeated Dreamer contributes 1% to
    completion.
    """

    id: str
    display_name: str

    defeated: bool

    area: str = ""


# ------------------------------------------------------------
# Ability System
# ------------------------------------------------------------


@dataclass
class AbilityState:
    """
    State of a player ability or key progression item.
    """

    id: str
    display_name: str

    category: str
    unlocked: bool

    level: int = 1

    description: str = ""
    how_to_get: str = ""

    map_pixel_x: Optional[int] = None
    map_pixel_y: Optional[int] = None


@dataclass
class AbilityTree:
    """
    Groups player abilities by functional category.
    """

    movement: list[AbilityState] = field(default_factory=list)
    dream: list[AbilityState] = field(default_factory=list)
    spells: list[AbilityState] = field(default_factory=list)
    nail_arts: list[AbilityState] = field(default_factory=list)

    nail_upgrade: int = 0

    key_items: list[AbilityState] = field(default_factory=list)


# ------------------------------------------------------------
# Grubs
# ------------------------------------------------------------


@dataclass
class GrubState:
    """
    Overall progress of grub collection.
    """

    grubs_collected: int
    total_grubs: int

    rewards_received: int
    final_reward: bool

    grubfather_met: bool


# ------------------------------------------------------------
# Relics
# ------------------------------------------------------------


@dataclass
class RelicState:
    """
    State of a relic item type.

    Relics are sellable collectibles that can be traded to
    Lemm in City of Tears.
    """

    id: str
    display_name: str

    held_count: int
    sold_count: int

    total_found: int
    total_in_world: int

    sell_value: int


# ------------------------------------------------------------
# Collectibles
# ------------------------------------------------------------


@dataclass
class CollectibleState:
    """
    Aggregate state of all collectible systems.
    """

    mask_shards: int
    mask_shard_max: int

    vessel_fragments: int
    vessel_fragment_max: int

    pale_ore: int

    dream_orbs: int
    dream_orbs_spent: int

    dream_rewards: list[bool] = field(default_factory=list)

    rancid_eggs: int = 0
    jiji_eggs_sold: int = 0

    relics: list[RelicState] = field(default_factory=list)

    grubs: Optional[GrubState] = None

    flames_collected: int = 0
    flames_required: int = 3
    grimmchild_level: int = 0


# ------------------------------------------------------------
# NPC Quest System
# ------------------------------------------------------------


@dataclass
class NPCQuestState:
    """
    State of an NPC questline.
    """

    id: str
    display_name: str

    current_stage: int
    total_stages: int

    stage_names: list[str] = field(default_factory=list)
    stage_completed: list[bool] = field(default_factory=list)

    completed: bool = False

    can_die: bool = False
    is_dead: bool = False


# ------------------------------------------------------------
# Godhome
# ------------------------------------------------------------


@dataclass
class StatueState:
    """
    State of a Hall of Gods statue.
    """

    id: str
    display_name: str

    is_unlocked: bool

    tier1: bool = False
    tier2: bool = False
    tier3: bool = False
    radiant: bool = False

    alt_version: bool = False


@dataclass
class PantheonState:
    """
    State of a Godhome pantheon challenge.
    """

    tier: int

    unlocked: bool
    completed: bool

    no_hit: bool = False
    all_bindings: bool = False

    bound_nail: bool = False
    bound_shell: bool = False
    bound_soul: bool = False
    bound_charms: bool = False


@dataclass
class GodhomeState:
    """
    Complete Godhome progression state.
    """

    godtuner_found: bool = False

    statues: list[StatueState] = field(default_factory=list)
    pantheons: list[PantheonState] = field(default_factory=list)


# ------------------------------------------------------------
# Map Areas
# ------------------------------------------------------------


@dataclass
class AreaState:
    """
    State of a world map area.
    """

    id: str
    display_name: str

    visited: bool

    map_obtained: bool = False
    cornifer_found: bool = False
    stag_unlocked: bool = False

    is_infected: bool = False

    tile_colour: str = "#5A5A72"


# ------------------------------------------------------------
# Player Statistics
# ------------------------------------------------------------


@dataclass
class PlayerStats:
    """
    Current player statistics and progression values.
    """

    geo: int
    geo_pool: int
    banker_balance: int

    health: int
    max_health: int
    max_health_base: int

    soul: int
    max_soul: int
    mp_reserve_cap: int

    notches: int
    notches_used: int

    nail_damage: int
    nail_tier: int

    charms_owned: int

    overcharmed: bool
    can_overcharm: bool

    current_area: str = ""
    play_time: float = 0.0

    completion_percent: int = 0


# ------------------------------------------------------------
# Special Areas
# ------------------------------------------------------------


@dataclass
class ColosseumState:
    """
    Colosseum of Fools progression.
    """

    bronze_opened: bool = False
    bronze_completed: bool = False

    silver_opened: bool = False
    silver_completed: bool = False

    gold_opened: bool = False
    gold_completed: bool = False


@dataclass
class WhitePalaceState:
    """
    White Palace progression state.
    """

    visited: bool = False

    orb_1: bool = False
    orb_2: bool = False
    orb_3: bool = False

    secret_room_visited: bool = False

    mid_warp: bool = False


# ------------------------------------------------------------
# Root Save Container
# ------------------------------------------------------------


@dataclass
class SaveData:
    """
    Top level container representing a fully parsed save file.
    """

    player_stats: PlayerStats

    charms: list[CharmState] = field(default_factory=list)
    bosses: list[BossState] = field(default_factory=list)
    dreamers: list[DreamerState] = field(default_factory=list)

    abilities: AbilityTree = field(default_factory=AbilityTree)

    collectibles: CollectibleState = field(
        default_factory=lambda: CollectibleState(
            mask_shards=0,
            mask_shard_max=16,
            vessel_fragments=0,
            vessel_fragment_max=9,
            pale_ore=0,
            dream_orbs=0,
            dream_orbs_spent=0,
        )
    )

    areas: list[AreaState] = field(default_factory=list)

    npc_quests: list[NPCQuestState] = field(default_factory=list)

    godhome: GodhomeState = field(default_factory=GodhomeState)

    colosseum: ColosseumState = field(default_factory=ColosseumState)

    white_palace: WhitePalaceState = field(default_factory=WhitePalaceState)

    seer_departed: bool = False

    completion_percent: int = 0

    save_version: str = ""
    profile_id: int = 0

    # Future expansion fields

    journal_entries_completed: int = 0
    journal_entries_total: int = 0

    journal_notes_completed: int = 0
