"""Save parser — raw dict to SaveData dataclass.

This is the ONLY file that reads raw JSON key strings from the decrypted save.
Every other module accesses save state through the typed dataclasses in save_model.py.
"""

from __future__ import annotations

import logging
from typing import Any

from src.data.save_model import (
    AbilityState,
    AbilityTree,
    AreaState,
    BossState,
    CharmState,
    ColosseumState,
    CollectibleState,
    DreamerState,
    GodhomeState,
    GrubState,
    NPCQuestState,
    PantheonState,
    PlayerStats,
    RelicState,
    SaveData,
    StatueState,
    WhitePalaceState,
)
from src.data.game_data import (
    get_bosses,
    get_charms,
    get_areas,
    get_abilities,
    get_npcs,
    get_relics,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================
TOTAL_GRUBS = 46
TOTAL_CHARMS = 40
TOTAL_MASK_SHARDS = 16
TOTAL_VESSEL_FRAGMENTS = 9
TOTAL_PALE_ORE = 6
TOTAL_DREAM_REWARDS = 9

# Fragile charm IDs
FRAGILE_HEART_ID = 23
FRAGILE_GREED_ID = 24
FRAGILE_STRENGTH_ID = 25

# Nail tier thresholds (nailSmithUpgrades values)
NAIL_TIER_NAMES = [
    "Old Nail",
    "Sharpened Nail",
    "Channelled Nail",
    "Coiled Nail",
    "Pure Nail",
]
NAIL_DAMAGE_BY_TIER = [5, 9, 13, 17, 21]


def _g(d: dict, key: str, default: Any = None) -> Any:
    """Safe get from a dict — shorthand for .get() with a default."""
    return d.get(key, default)


def _gb(d: dict, key: str) -> bool:
    """Safe bool get from a dict."""
    return bool(d.get(key, False))


def _gi(d: dict, key: str, default: int = 0) -> int:
    """Safe int get from a dict."""
    val = d.get(key, default)
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _gf(d: dict, key: str, default: float = 0.0) -> float:
    """Safe float get from a dict."""
    val = d.get(key, default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# =============================================================================
# Charm Parsing
# =============================================================================


def _parse_charms(pd: dict) -> list[CharmState]:
    """Parse all 40 charms from playerData."""
    charm_data = get_charms()
    charm_lookup = {c["id"]: c for c in charm_data}
    charms: list[CharmState] = []

    for i in range(1, TOTAL_CHARMS + 1):
        info = charm_lookup.get(i, {})
        owned = _gb(pd, f"gotCharm_{i}")
        equipped = _gb(pd, f"equippedCharm_{i}")
        cost = _gi(pd, f"charmCost_{i}", info.get("default_notch_cost", 1))

        broken = False
        unbreakable = False
        if i == FRAGILE_HEART_ID:
            broken = _gb(pd, "brokenCharm_23")
            unbreakable = _gb(pd, "fragileHealth_unbreakable")
        elif i == FRAGILE_GREED_ID:
            broken = _gb(pd, "brokenCharm_24")
            unbreakable = _gb(pd, "fragileGreed_unbreakable")
        elif i == FRAGILE_STRENGTH_ID:
            broken = _gb(pd, "brokenCharm_25")
            unbreakable = _gb(pd, "fragileStrength_unbreakable")

        # Kingsoul / Void Heart (charm 36)
        if i == 36:
            owned = _gb(pd, "gotCharm_36") or _gb(pd, "gotShadeCharm")

        charms.append(
            CharmState(
                id=i,
                name=info.get("name", f"Charm {i}"),
                owned=owned,
                equipped=equipped,
                broken=broken,
                unbreakable=unbreakable,
                notch_cost=cost,
                default_notch_cost=info.get("default_notch_cost", 1),
                area=info.get("area", ""),
                description=info.get("description", ""),
                how_to_get=info.get("how_to_get", ""),
            )
        )

    return charms


# =============================================================================
# Boss Parsing
# =============================================================================


def _parse_bosses(pd: dict) -> list[BossState]:
    """Parse all bosses from playerData using bosses.json."""
    boss_data = get_bosses()
    bosses: list[BossState] = []

    for boss in boss_data:
        killed_key = boss.get("killed_key", "")
        kills_key = boss.get("kills_key", "")
        dream_killed_key = boss.get("dream_killed_key")

        defeated = _gb(pd, killed_key) if killed_key else False
        kill_count = _gi(pd, kills_key) if kills_key else 0
        dream_defeated = _gb(pd, dream_killed_key) if dream_killed_key else False

        # Special dream boss defeat counts
        dream_kills = 0
        if boss["id"] == "grey_prince_zote":
            dream_kills = _gi(pd, "greyPrinceDefeats")
        elif boss["id"] == "white_defender":
            dream_kills = _gi(pd, "whiteDefenderDefeats")

        bosses.append(
            BossState(
                id=boss["id"],
                display_name=boss["display_name"],
                category=boss.get("category", "main"),
                area=boss.get("area", ""),
                defeated=defeated,
                kill_count=kill_count,
                dream_defeated=dream_defeated,
                dream_kills=dream_kills,
                sub_area=boss.get("sub_area", ""),
                difficulty=boss.get("difficulty", ""),
                map_pixel_x=boss.get("map_pixel_x"),
                map_pixel_y=boss.get("map_pixel_y"),
                statue_key=boss.get("statue_key"),
            )
        )

    return bosses


# =============================================================================
# Ability Parsing
# =============================================================================


def _parse_abilities(pd: dict) -> AbilityTree:
    """Parse all abilities from playerData."""
    ability_data = get_abilities()
    tree = AbilityTree()

    for ability in ability_data:
        save_key = ability.get("save_key", "")
        category = ability.get("category", "")
        aid = ability.get("id", "")

        # Determine unlocked and level
        unlocked = False
        level = 0

        if save_key in ("fireballLevel", "quakeLevel", "screamLevel"):
            raw_level = _gi(pd, save_key, 0)
            if aid in ("vengeful_spirit", "desolate_dive", "howling_wraiths"):
                unlocked = raw_level >= 1
                level = raw_level
            elif aid in ("shade_soul", "descending_dark", "abyss_shriek"):
                unlocked = raw_level >= 2
                level = raw_level
            else:
                unlocked = raw_level >= 1
                level = raw_level
        elif save_key == "dreamNailUpgraded":
            unlocked = _gb(pd, save_key)
            level = 2 if unlocked else 0
        elif save_key:
            unlocked = _gb(pd, save_key)
            level = 1 if unlocked else 0

        state = AbilityState(
            id=aid,
            display_name=ability.get("display_name", ""),
            category=category,
            unlocked=unlocked,
            level=level,
            description=ability.get("description", ""),
            how_to_get=ability.get("how_to_get", ""),
            map_pixel_x=ability.get("map_pixel_x"),
            map_pixel_y=ability.get("map_pixel_y"),
        )

        if category == "movement":
            tree.movement.append(state)
        elif category == "dream":
            tree.dream.append(state)
        elif category == "spell":
            tree.spells.append(state)
        elif category == "nail_art":
            tree.nail_arts.append(state)
        elif category == "key_item":
            tree.key_items.append(state)

    tree.nail_upgrade = _gi(pd, "nailSmithUpgrades", 0)

    return tree


# =============================================================================
# Collectible Parsing
# =============================================================================


def _parse_grubs(pd: dict) -> GrubState:
    """Parse grub collection state."""
    return GrubState(
        grubs_collected=_gi(pd, "grubsCollected"),
        total_grubs=TOTAL_GRUBS,
        rewards_received=_gi(pd, "grubRewards"),
        final_reward=_gb(pd, "finalGrubRewardCollected"),
        grubfather_met=_gb(pd, "fatGrubKing"),
    )


def _parse_relics(pd: dict) -> list[RelicState]:
    """Parse relic states from playerData."""
    relic_data = get_relics()
    relics: list[RelicState] = []

    for relic in relic_data:
        trinket_key = relic.get("trinket_key", "")
        found_key = relic.get("found_key", "")
        held = _gi(pd, trinket_key)
        sold = _gi(pd, f"sold{trinket_key.capitalize()}" if trinket_key else "")
        total_found = held + sold

        relics.append(
            RelicState(
                id=relic["id"],
                display_name=relic["display_name"],
                held_count=held,
                sold_count=sold,
                total_found=total_found,
                total_in_world=relic.get("total_in_world", 0),
                sell_value=relic.get("sell_value", 0),
            )
        )

    return relics


def _parse_collectibles(pd: dict) -> CollectibleState:
    """Parse all collectible counts from playerData."""
    # Dream rewards
    dream_rewards: list[bool] = []
    for i in range(1, TOTAL_DREAM_REWARDS + 1):
        dream_rewards.append(_gb(pd, f"dreamReward{i}"))

    return CollectibleState(
        mask_shards=_gi(pd, "heartPieces"),
        mask_shard_max=TOTAL_MASK_SHARDS,
        vessel_fragments=_gi(pd, "vesselFragments"),
        vessel_fragment_max=TOTAL_VESSEL_FRAGMENTS,
        pale_ore=_gi(pd, "ore"),
        dream_orbs=_gi(pd, "dreamOrbs"),
        dream_orbs_spent=_gi(pd, "dreamOrbsSpent"),
        dream_rewards=dream_rewards,
        rancid_eggs=_gi(pd, "ghostCoins"),
        jiji_eggs_sold=_gi(pd, "jinnEggsSold"),
        relics=_parse_relics(pd),
        grubs=_parse_grubs(pd),
        flames_collected=_gi(pd, "flamesCollected"),
        flames_required=_gi(pd, "flamesRequired", 3),
        grimmchild_level=_gi(pd, "grimmChildLevel"),
    )


# =============================================================================
# Dreamers Parsing
# =============================================================================

_DREAMERS = [
    ("lurien", "Lurien the Watcher", "lurienDefeated", "City of Tears"),
    ("monomon", "Monomon the Teacher", "monomonDefeated", "Fog Canyon"),
    ("herrah", "Herrah the Beast", "hegemolDefeated", "Deepnest"),
]


def _parse_dreamers(pd: dict) -> list[DreamerState]:
    """Parse the three Dreamer seals from playerData."""

    dreamers = []
    for did, name, key, area in _DREAMERS:
        dreamers.append(
            DreamerState(
                id=did,
                display_name=name,
                defeated=_gb(pd, key),
                area=area,
            )
        )
    return dreamers


# =============================================================================
# Area Parsing
# =============================================================================


def _parse_areas(pd: dict) -> list[AreaState]:
    """Parse area visited/map/cornifer/stag states."""
    area_data = get_areas()
    areas: list[AreaState] = []

    for area in area_data:
        visited_key = area.get("visited_key", "")
        cornifer_key = area.get("cornifer_encountered_key")
        stag_key = area.get("stag_key")
        infected_key = area.get("infected_key")

        visited = _gb(pd, visited_key) if visited_key else False
        cornifer_found = _gb(pd, cornifer_key) if cornifer_key else False
        stag_unlocked = _gb(pd, stag_key) if stag_key else False
        is_infected = _gb(pd, infected_key) if infected_key else False

        # Map obtained — use area-specific map key or fall back to generic
        map_obtained = (
            _gb(pd, "mapCrossroads") if area["id"] == "forgotten_crossroads" else False
        )
        if area["id"] == "greenpath":
            map_obtained = _gb(pd, "mapGreenpath")
        elif area["id"] == "fungal_wastes":
            map_obtained = _gb(pd, "mapFungalWastes")
        elif area["id"] == "city_of_tears":
            map_obtained = _gb(pd, "mapCity")
        elif area["id"] == "crystal_peak":
            map_obtained = _gb(pd, "mapMines")
        elif area["id"] == "resting_grounds":
            map_obtained = _gb(pd, "mapRestingGrounds")
        elif area["id"] == "royal_waterways":
            map_obtained = _gb(pd, "mapWaterways")
        elif area["id"] == "deepnest":
            map_obtained = _gb(pd, "mapDeepnest")
        elif area["id"] == "ancient_basin":
            map_obtained = _gb(pd, "mapAbyss")
        elif area["id"] == "kingdoms_edge":
            map_obtained = _gb(pd, "mapOutskirts")
        elif area["id"] == "fog_canyon":
            map_obtained = _gb(pd, "mapFogCanyon")
        elif area["id"] == "queens_gardens":
            map_obtained = _gb(pd, "mapRoyalGardens")
        elif area["id"] == "howling_cliffs":
            map_obtained = _gb(pd, "mapCliffs")
        elif area["id"] == "forgotten_crossroads":
            map_obtained = _gb(pd, "mapCrossroads")
        elif area["id"] == "dirtmouth":
            map_obtained = _gb(pd, "mapDirtmouth")

        areas.append(
            AreaState(
                id=area["id"],
                display_name=area["display_name"],
                visited=visited,
                map_obtained=map_obtained,
                cornifer_found=cornifer_found,
                stag_unlocked=stag_unlocked,
                is_infected=is_infected,
                tile_colour=area.get("tile_colour", "#5A5A72"),
            )
        )

    return areas


# =============================================================================
# NPC Quest Parsing
# =============================================================================


def _parse_npc_quests(pd: dict) -> list[NPCQuestState]:
    """Parse NPC quest progress from playerData."""
    npc_data = get_npcs()
    quests: list[NPCQuestState] = []

    for npc in npc_data:
        stages = npc.get("stages", [])
        stage_names: list[str] = []
        stage_completed: list[bool] = []
        current_stage = 0

        for i, stage in enumerate(stages):
            stage_names.append(stage.get("label", f"Stage {i+1}"))
            completed = _gb(pd, stage.get("key", ""))
            stage_completed.append(completed)
            if completed:
                current_stage = i + 1

        total_stages = len(stages)
        all_done = current_stage >= total_stages and total_stages > 0

        is_dead = False
        dead_key = npc.get("dead_key")
        if dead_key:
            is_dead = _gb(pd, dead_key)

        quests.append(
            NPCQuestState(
                id=npc["id"],
                display_name=npc["display_name"],
                current_stage=current_stage,
                total_stages=total_stages,
                stage_names=stage_names,
                stage_completed=stage_completed,
                completed=all_done,
                can_die=npc.get("can_die", False),
                is_dead=is_dead,
            )
        )

    return quests


# =============================================================================
# Godhome Parsing
# =============================================================================

_STATUE_BOSSES = [
    ("statueStateFalseKnight", "False Knight"),
    ("statueStateGruzMother", "Gruz Mother"),
    ("statueStateVengefly", "Vengefly King"),
    ("statueStateHornet1", "Hornet Protector"),
    ("statueStateMegaMossCharger", "Massive Moss Charger"),
    ("statueStateSoulMaster", "Soul Master"),
    ("statueStateMantisLords", "Mantis Lords"),
    ("statueStateDungDefender", "Dung Defender"),
    ("statueStateFlukemarm", "Flukemarm"),
    ("statueStateBrokenVessel", "Broken Vessel"),
    ("statueStateBroodingMawlek", "Brooding Mawlek"),
    ("statueStateNosk", "Nosk"),
    ("statueStateCollector", "The Collector"),
    ("statueStateWatcherKnights", "Watcher Knights"),
    ("statueStateCrystalGuardian1", "Crystal Guardian"),
    ("statueStateCrystalGuardian2", "Enraged Guardian"),
    ("statueStateUumuu", "Uumuu"),
    ("statueStateHiveKnight", "Hive Knight"),
    ("statueStateTraitorLord", "Traitor Lord"),
    ("statueStateHornet2", "Hornet Sentinel"),
    ("statueStateHollowKnight", "Hollow Knight"),
    ("statueStateRadiance", "The Radiance"),
    ("statueStateGodTamer", "God Tamer"),
    ("statueStateGrimm", "Grimm"),
    ("statueStateNightmareGrimm", "Nightmare King Grimm"),
    ("statueStateFailedChampion", "Failed Champion"),
    ("statueStateSoulTyrant", "Soul Tyrant"),
    ("statueStateLostKin", "Lost Kin"),
    ("statueStateWhiteDefender", "White Defender"),
    ("statueStateGreyPrince", "Grey Prince Zote"),
    ("statueStateXero", "Xero"),
    ("statueStateElderHu", "Elder Hu"),
    ("statueStateGalien", "Galien"),
    ("statueStateMarmu", "Marmu"),
    ("statueStateNoEyes", "No Eyes"),
    ("statueStateMarkoth", "Markoth"),
    ("statueStateGorb", "Gorb"),
    ("statueStateOblobbles", "Oblobbles"),
    ("statueStateNailmasters", "Brothers Oro & Mato"),
    ("statueStatePaintmaster", "Paintmaster Sheo"),
    ("statueStateSly", "Great Nailsage Sly"),
    ("statueStateMageKnight", "Soul Warrior"),
]


def _parse_statue(pd: dict, key: str, name: str) -> StatueState:
    """Parse a single Hall of Gods statue."""
    statue_data = _g(pd, key, {})
    if not isinstance(statue_data, dict):
        statue_data = {}

    return StatueState(
        id=key,
        display_name=name,
        is_unlocked=_gb(statue_data, "isUnlocked"),
        tier1=_gb(statue_data, "completedTier1"),
        tier2=_gb(statue_data, "completedTier2"),
        tier3=_gb(statue_data, "completedTier3"),
        radiant=_gb(statue_data, "noHits"),
        alt_version=_gb(statue_data, "usingAltVersion"),
    )


def _parse_pantheon(pd: dict, tier: int) -> PantheonState:
    """Parse a single Pantheon's state."""
    key = f"bossDoorStateTier{tier}"
    door_data = _g(pd, key, {})
    if not isinstance(door_data, dict):
        door_data = {}

    return PantheonState(
        tier=tier,
        unlocked=True,  # Pantheons are progressively unlocked
        completed=_gb(door_data, "completed"),
        no_hit=_gb(door_data, "noHits"),
        all_bindings=_gb(door_data, "allBindings"),
        bound_nail=_gb(door_data, "boundNail"),
        bound_shell=_gb(door_data, "boundShell"),
        bound_soul=_gb(door_data, "boundSoul"),
        bound_charms=_gb(door_data, "boundCharms"),
    )


def _parse_godhome(pd: dict) -> GodhomeState:
    """Parse all Hall of Gods and Pantheon data."""
    godtuner_found = _gb(pd, "hasGodfinder")
    statues = [_parse_statue(pd, key, name) for key, name in _STATUE_BOSSES]
    pantheons = [_parse_pantheon(pd, tier) for tier in range(1, 6)]

    return GodhomeState(
        godtuner_found=godtuner_found, statues=statues, pantheons=pantheons
    )


# =============================================================================
# Colosseum Parsing
# =============================================================================


def _parse_colosseum(pd: dict) -> ColosseumState:
    """Parse Colosseum of Fools progress."""
    return ColosseumState(
        bronze_opened=_gb(pd, "colosseumBronzeOpened"),
        bronze_completed=_gb(pd, "colosseumBronzeCompleted"),
        silver_opened=_gb(pd, "colosseumSilverOpened"),
        silver_completed=_gb(pd, "colosseumSilverCompleted"),
        gold_opened=_gb(pd, "colosseumGoldOpened"),
        gold_completed=_gb(pd, "colosseumGoldCompleted"),
    )


# =============================================================================
# White Palace Parsing
# =============================================================================


def _parse_white_palace(pd: dict) -> WhitePalaceState:
    """Parse White Palace progress."""
    return WhitePalaceState(
        visited=_gb(pd, "visitedWhitePalace"),
        orb_1=_gb(pd, "whitePalaceOrb_1"),
        orb_2=_gb(pd, "whitePalaceOrb_2"),
        orb_3=_gb(pd, "whitePalaceOrb_3"),
        secret_room_visited=_gb(pd, "whitePalaceSecretRoomVisited"),
        mid_warp=_gb(pd, "whitePalaceMidWarp"),
    )


# =============================================================================
# Player Stats
# =============================================================================


def _parse_player_stats(pd: dict) -> PlayerStats:
    """Parse player statistics from playerData."""
    nail_upgrades = _gi(pd, "nailSmithUpgrades", 0)

    return PlayerStats(
        geo=_gi(pd, "geo"),
        geo_pool=_gi(pd, "geoPool"),
        banker_balance=_gi(pd, "bankerBalance"),
        health=_gi(pd, "health", 5),
        max_health=_gi(pd, "maxHealth", 5),
        max_health_base=_gi(pd, "maxHealthBase", 5),
        soul=_gi(pd, "MPCharge"),
        max_soul=99,
        mp_reserve_cap=_gi(pd, "MPReserveCap"),
        notches=_gi(pd, "charmSlots", 3),
        notches_used=_gi(pd, "charmSlotsFilled"),
        nail_damage=_gi(pd, "nailDamage", 5),
        nail_tier=nail_upgrades,
        charms_owned=_gi(pd, "charmsOwned"),
        overcharmed=_gb(pd, "overcharmed"),
        can_overcharm=_gb(pd, "canOvercharm"),
        current_area=str(_g(pd, "currentArea", "")),
        play_time=_gf(pd, "playTime"),
        completion_percent=_gi(pd, "completionPercentage"),
    )


# =============================================================================
# Public API
# =============================================================================


def parse_save(raw_dict: dict) -> SaveData:
    """Parse a raw decrypted save dict into a fully typed SaveData object.

    This is the single entry point for converting raw JSON data from the
    Hollow Knight save file into the application's typed data model.
    """
    # The save file wraps everything under a "playerData" key
    pd = raw_dict.get("playerData", raw_dict)

    logger.info("Parsing save data...")

    charms = _parse_charms(pd)
    bosses = _parse_bosses(pd)
    abilities = _parse_abilities(pd)
    collectibles = _parse_collectibles(pd)
    dreamers = _parse_dreamers(pd)
    areas = _parse_areas(pd)
    npc_quests = _parse_npc_quests(pd)
    godhome = _parse_godhome(pd)
    colosseum = _parse_colosseum(pd)
    white_palace = _parse_white_palace(pd)
    player_stats = _parse_player_stats(pd)

    completion_pct = _gi(pd, "completionPercentage", 0)

    save_data = SaveData(
        player_stats=player_stats,
        charms=charms,
        bosses=bosses,
        abilities=abilities,
        collectibles=collectibles,
        dreamers=dreamers,
        areas=areas,
        npc_quests=npc_quests,
        godhome=godhome,
        colosseum=colosseum,
        white_palace=white_palace,
        completion_percent=completion_pct,
        save_version=str(_g(pd, "version", "")),
        profile_id=_gi(pd, "profileID", 0),
        journal_entries_completed=_gi(pd, "journalEntriesCompleted"),
        journal_entries_total=_gi(pd, "journalEntriesTotal"),
        journal_notes_completed=_gi(pd, "journalNotesCompleted"),
    )

    logger.info(
        f"Save parsed: completion={completion_pct}%, "
        f"charms={player_stats.charms_owned}/{TOTAL_CHARMS}, "
        f"grubs={collectibles.grubs.grubs_collected if collectibles.grubs else 0}/{TOTAL_GRUBS}"
    )

    return save_data
