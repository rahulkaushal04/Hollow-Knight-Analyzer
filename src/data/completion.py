"""
Completion calculator for Hollow Knight.


This module calculates the breakdown of game completion toward the
112 percent maximum completion.


The calculation reads a SaveData instance and evaluates progress
across all categories that contribute to completion. The result
is returned as a CompletionBreakdown object which contains:


    - Overall completion percent from the save file
    - Per category progress
    - Lists of missing items for each category


The rules follow the official Hollow Knight completion system.
"""


from __future__ import annotations


from dataclasses import dataclass, field


from src.data.save_model import SaveData



# =============================================================================
# Data structures
# =============================================================================


@dataclass
class CompletionCategory:
    """
    Progress of a single completion category.
    """


    name: str
    current: int
    total: int
    percent: float
    counts_toward_112: bool



@dataclass
class CompletionBreakdown:
    """
    Full completion summary for a save file.
    """


    overall_percent: int


    categories: list[CompletionCategory] = field(default_factory=list)


    missing_items: dict[str, list[str]] = field(default_factory=dict)



# =============================================================================
# Helper utilities
# =============================================================================


def _percent(current: int, total: int) -> float:
    """
    Calculate completion percent safely.
    """
    if total == 0:
        return 0.0
    return (current / total) * 100



# =============================================================================
# Category counters
# =============================================================================


def _count_defeated_main_bosses(save: SaveData) -> tuple[int, list[str]]:
    """
    Count main bosses that contribute to completion.

    14 bosses, each worth 1%.
    """


    completion_boss_ids = {
        "gruz_mother",
        "false_knight",
        "hornet_protector",
        "brooding_mawlek",
        "mantis_lords",
        "soul_master",
        "dung_defender",
        "nosk",
        "broken_vessel",
        "watcher_knights",
        "uumuu",
        "traitor_lord",
        "hornet_sentinel",
        "the_collector",
    }


    count = 0
    missing: list[str] = []


    for boss in save.bosses:
        if boss.id not in completion_boss_ids:
            continue


        if boss.defeated:
            count += 1
        else:
            missing.append(boss.display_name)


    return count, missing



def _count_warrior_dreams(save: SaveData) -> tuple[int, list[str]]:
    """
    Count defeated warrior dream ghosts.

    7 warriors, each worth 1%.
    """


    warrior_ids = {
        "xero",
        "elder_hu",
        "galien",
        "marmu",
        "no_eyes",
        "markoth",
        "gorb",
    }


    count = 0
    missing: list[str] = []


    for boss in save.bosses:
        if boss.id not in warrior_ids:
            continue


        if boss.defeated:
            count += 1
        else:
            missing.append(boss.display_name)


    return count, missing



def _count_dreamers(save: SaveData) -> tuple[int, list[str]]:
    """
    Count sealed Dreamers.

    3 dreamers, each worth 1%.
    """


    dreamer_ids = {
        "lurien",
        "monomon",
        "herrah",
    }


    count = 0
    missing: list[str] = []


    for dreamer in save.dreamers:
        if dreamer.id not in dreamer_ids:
            continue


        if dreamer.defeated:
            count += 1
        else:
            missing.append(dreamer.display_name)


    return count, missing



def _count_dream_nail(save: SaveData) -> tuple[int, list[str]]:
    """
    Count Dream Nail milestones.

    - Obtaining the Dream Nail: 1%
    - Awakening the Dream Nail (1800 Essence): 1%
    - Seer's final words (2400 Essence): 1%

    Total: 3%
    """


    count = 0
    missing: list[str] = []


    has_dream_nail = any(
        ability.unlocked and ability.id == "dream_nail"
        for ability in save.abilities.dream
    )

    dream_nail_awakened = any(
        ability.unlocked and ability.id == "dream_nail_awakened"
        for ability in save.abilities.dream
    )

    if has_dream_nail:
        count += 1
    else:
        missing.append("Dream Nail not obtained")

    if dream_nail_awakened:
        count += 1
    else:
        missing.append("Dream Nail not awakened (1800 Essence required)")

    if save.seer_departed:
        count += 1
    else:
        missing.append("Seer not departed (2400 Essence required)")


    return count, missing



def _count_nail_arts(save: SaveData) -> tuple[int, list[str]]:
    """
    Count learned Nail Arts.

    3 arts, each worth 1%.
    """


    count = 0
    missing: list[str] = []


    for ability in save.abilities.nail_arts:
        if ability.unlocked:
            count += 1
        else:
            missing.append(ability.display_name)


    return count, missing



def _count_equipment(save: SaveData) -> tuple[int, list[str]]:
    """
    Count unlocked equipment / movement abilities.

    7 items, each worth 2% (14% total).
    """


    count = 0
    missing: list[str] = []


    for ability in save.abilities.movement:
        if ability.unlocked:
            count += 1
        else:
            missing.append(ability.display_name)


    return count, missing



def _count_spells(save: SaveData) -> tuple[int, list[str]]:
    """
    Count unlocked spells.

    6 spells, each worth 1%.
    """


    count = 0
    missing: list[str] = []


    for ability in save.abilities.spells:
        if ability.unlocked:
            count += 1
        else:
            missing.append(ability.display_name)


    return count, missing



def _count_colosseum(save: SaveData) -> tuple[int, list[str]]:
    """
    Count completed Colosseum trials.
    """


    trials = [
        ("Trial of the Warrior (Bronze)", save.colosseum.bronze_completed),
        ("Trial of the Conqueror (Silver)", save.colosseum.silver_completed),
        ("Trial of the Fool (Gold)", save.colosseum.gold_completed),
    ]


    count = 0
    missing: list[str] = []


    for name, completed in trials:
        if completed:
            count += 1
        else:
            missing.append(name)


    return count, missing



def _count_grimm_troupe(save: SaveData) -> tuple[int, list[str]]:
    """
    Count Grimm Troupe DLC completion items.

    Includes 2 bosses and 4 DLC charms, each worth 1% (6% total).

    Bosses:
        - Troupe Master Grimm
        - Nightmare King Grimm (or Banishment)

    Charms:
        - Grimmchild / Carefree Melody (charm 40)
        - Dreamshield (charm 38)
        - Sprintmaster (charm 37)
        - Weaversong (charm 39)
    """


    count = 0
    missing: list[str] = []


    grimm_defeated = any(b.id == "grimm" and b.defeated for b in save.bosses)
    nkg_defeated = any(b.id == "nightmare_king_grimm" and b.defeated for b in save.bosses)


    if grimm_defeated:
        count += 1
    else:
        missing.append("Troupe Master Grimm")


    if nkg_defeated:
        count += 1
    else:
        missing.append("Nightmare King Grimm or Banishment")


    dlc_charm_ids = {38, 39, 40, 37}
    dlc_charm_names = {
        37: "Sprintmaster",
        38: "Dreamshield",
        39: "Weaversong",
        40: "Grimmchild / Carefree Melody",
    }


    for charm in save.charms:
        if charm.id not in dlc_charm_ids:
            continue

        if charm.owned:
            count += 1
        else:
            missing.append(dlc_charm_names[charm.id])


    return count, missing



def _count_godhome(save: SaveData) -> tuple[int, list[str]]:
    """
    Count Godhome DLC completion items.

    - Finding Godhome (Godtuner): 1%
    - Pantheon of the Master (1): 1%
    - Pantheon of the Artist (2): 1%
    - Pantheon of the Sage (3): 1%
    - Pantheon of the Knight (4): 1%

    Total: 5%

    Note: Pantheon of the Hallownest (5th) does not contribute to completion %.
    """


    pantheon_names = [
        "Pantheon of the Master",
        "Pantheon of the Artist",
        "Pantheon of the Sage",
        "Pantheon of the Knight",
    ]


    count = 0
    missing: list[str] = []


    if save.godhome.godtuner_found:
        count += 1
    else:
        missing.append("Godhome not found (Godtuner)")


    for index, pantheon in enumerate(save.godhome.pantheons[:4]):
        if pantheon.completed:
            count += 1
        else:
            name = pantheon_names[index] if index < len(pantheon_names) else f"Pantheon {index + 1}"
            missing.append(name)


    return count, missing



# =============================================================================
# Main calculation
# =============================================================================


def calculate_completion(save: SaveData) -> CompletionBreakdown:
    """
    Compute the full 112 percent completion breakdown.


    Parameters
    ----------
    save
        Parsed save file.


    Returns
    -------
    CompletionBreakdown
        Structured completion analysis.
    """


    categories: list[CompletionCategory] = []
    all_missing: dict[str, list[str]] = {}


    # -------------------------------------------------------------------------
    # Bosses (14%)
    # -------------------------------------------------------------------------


    boss_count, boss_missing = _count_defeated_main_bosses(save)


    categories.append(
        CompletionCategory(
            "Bosses",
            boss_count,
            14,
            _percent(boss_count, 14),
            True,
        )
    )


    if boss_missing:
        all_missing["Bosses"] = boss_missing


    # -------------------------------------------------------------------------
    # Charms — base game only, 36 charms (36%)
    # DLC charms (37, 38, 39, 40) are counted under Grimm Troupe
    # -------------------------------------------------------------------------


    charm_count = sum(1 for charm in save.charms if charm.owned and charm.id <= 36)
    charm_missing = [c.name for c in save.charms if not c.owned and c.id <= 36]


    categories.append(
        CompletionCategory(
            "Charms",
            charm_count,
            36,
            _percent(charm_count, 36),
            True,
        )
    )


    if charm_missing:
        all_missing["Charms"] = charm_missing


    # -------------------------------------------------------------------------
    # Mask shards (4%)
    # -------------------------------------------------------------------------


    masks_complete = save.collectibles.mask_shards // 4
    mask_missing_count = 16 - save.collectibles.mask_shards


    categories.append(
        CompletionCategory(
            "Mask Shards",
            masks_complete,
            4,
            _percent(masks_complete, 4),
            True,
        )
    )


    if mask_missing_count > 0:
        all_missing["Mask Shards"] = [f"{mask_missing_count} shards remaining"]


    # -------------------------------------------------------------------------
    # Vessel fragments (3%)
    # -------------------------------------------------------------------------


    vessels_complete = save.collectibles.vessel_fragments // 3
    vessel_missing_count = 9 - save.collectibles.vessel_fragments


    categories.append(
        CompletionCategory(
            "Vessel Fragments",
            vessels_complete,
            3,
            _percent(vessels_complete, 3),
            True,
        )
    )


    if vessel_missing_count > 0:
        all_missing["Vessel Fragments"] = [f"{vessel_missing_count} fragments remaining"]


    # -------------------------------------------------------------------------
    # Nail upgrades (4%)
    # -------------------------------------------------------------------------


    nail_level = save.abilities.nail_upgrade


    categories.append(
        CompletionCategory(
            "Nail Upgrades",
            nail_level,
            4,
            _percent(nail_level, 4),
            True,
        )
    )


    if nail_level < 4:
        all_missing["Nail Upgrades"] = [f"{4 - nail_level} upgrades remaining"]


    # -------------------------------------------------------------------------
    # Nail Arts (3%)
    # -------------------------------------------------------------------------


    arts_count, arts_missing = _count_nail_arts(save)


    categories.append(
        CompletionCategory(
            "Nail Arts",
            arts_count,
            3,
            _percent(arts_count, 3),
            True,
        )
    )


    if arts_missing:
        all_missing["Nail Arts"] = arts_missing


    # -------------------------------------------------------------------------
    # Equipment / Movement abilities (14%)
    # 7 items, each worth 2%
    # -------------------------------------------------------------------------


    equip_count, equip_missing = _count_equipment(save)


    categories.append(
        CompletionCategory(
            "Equipment",
            equip_count,
            7,
            _percent(equip_count, 7),
            True,
        )
    )


    if equip_missing:
        all_missing["Equipment"] = equip_missing


    # -------------------------------------------------------------------------
    # Spells (6%)
    # -------------------------------------------------------------------------


    spell_count, spell_missing = _count_spells(save)


    categories.append(
        CompletionCategory(
            "Spells",
            spell_count,
            6,
            _percent(spell_count, 6),
            True,
        )
    )


    if spell_missing:
        all_missing["Spells"] = spell_missing


    # -------------------------------------------------------------------------
    # Dreamers (3%)
    # -------------------------------------------------------------------------


    dreamer_count, dreamer_missing = _count_dreamers(save)


    categories.append(
        CompletionCategory(
            "Dreamers",
            dreamer_count,
            3,
            _percent(dreamer_count, 3),
            True,
        )
    )


    if dreamer_missing:
        all_missing["Dreamers"] = dreamer_missing


    # -------------------------------------------------------------------------
    # Dream Nail (3%)
    # Obtain + Awaken + Seer's final words
    # -------------------------------------------------------------------------


    dn_count, dn_missing = _count_dream_nail(save)


    categories.append(
        CompletionCategory(
            "Dream Nail",
            dn_count,
            3,
            _percent(dn_count, 3),
            True,
        )
    )


    if dn_missing:
        all_missing["Dream Nail"] = dn_missing


    # -------------------------------------------------------------------------
    # Warrior Dreams (7%)
    # -------------------------------------------------------------------------


    warrior_count, warrior_missing = _count_warrior_dreams(save)


    categories.append(
        CompletionCategory(
            "Warrior Dreams",
            warrior_count,
            7,
            _percent(warrior_count, 7),
            True,
        )
    )


    if warrior_missing:
        all_missing["Warrior Dreams"] = warrior_missing


    # -------------------------------------------------------------------------
    # Colosseum (3%)
    # -------------------------------------------------------------------------


    col_count, col_missing = _count_colosseum(save)


    categories.append(
        CompletionCategory(
            "Colosseum",
            col_count,
            3,
            _percent(col_count, 3),
            True,
        )
    )


    if col_missing:
        all_missing["Colosseum"] = col_missing


    # -------------------------------------------------------------------------
    # Hive Knight — Lifeblood DLC (1%)
    # -------------------------------------------------------------------------


    hive_knight_defeated = any(b.id == "hive_knight" and b.defeated for b in save.bosses)
    hk_count = 1 if hive_knight_defeated else 0


    categories.append(
        CompletionCategory(
            "Lifeblood",
            hk_count,
            1,
            _percent(hk_count, 1),
            True,
        )
    )


    if not hive_knight_defeated:
        all_missing["Lifeblood"] = ["Hive Knight not defeated"]


    # -------------------------------------------------------------------------
    # Grimm Troupe DLC (6%)
    # 2 bosses + 4 charms
    # -------------------------------------------------------------------------


    grimm_count, grimm_missing = _count_grimm_troupe(save)


    categories.append(
        CompletionCategory(
            "Grimm Troupe",
            grimm_count,
            6,
            _percent(grimm_count, 6),
            True,
        )
    )


    if grimm_missing:
        all_missing["Grimm Troupe"] = grimm_missing


    # -------------------------------------------------------------------------
    # Godhome DLC (5%)
    # Godtuner + Pantheons 1-4
    # -------------------------------------------------------------------------


    godhome_count, godhome_missing = _count_godhome(save)


    categories.append(
        CompletionCategory(
            "Godhome Pantheons",
            godhome_count,
            5,
            _percent(godhome_count, 5),
            True,
        )
    )


    if godhome_missing:
        all_missing["Godhome Pantheons"] = godhome_missing


    return CompletionBreakdown(
        overall_percent=save.completion_percent,
        categories=categories,
        missing_items=all_missing,
    )
