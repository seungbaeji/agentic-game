from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InventoryItem:
    item_id: str
    quantity: int


@dataclass(frozen=True, slots=True)
class InventoryState:
    items: tuple[InventoryItem, ...] = ()


@dataclass(frozen=True, slots=True)
class PlayerState:
    hp: int = 100
    exp: int = 0
    gold: int = 100


@dataclass(frozen=True, slots=True)
class SkillProgress:
    skill_id: str
    level: int
    exp: int


@dataclass(frozen=True, slots=True)
class SkillBook:
    skills: tuple[SkillProgress, ...] = ()


@dataclass(frozen=True, slots=True)
class QuestProgress:
    quest_id: str
    status: str
    progress: int


@dataclass(frozen=True, slots=True)
class QuestLog:
    quests: tuple[QuestProgress, ...] = ()


@dataclass(frozen=True, slots=True)
class WorldState:
    current_location: str = "town"
    discovered_locations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NpcState:
    npc_id: str
    relation: int = 0
    memories: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NpcMemory:
    npcs: tuple[NpcState, ...] = ()


def add_inventory_item(
    inventory: InventoryState,
    *,
    item_id: str,
    quantity: int = 1,
) -> InventoryState:
    """Return inventory with quantity added for the given item."""
    if quantity <= 0:
        return inventory

    updated_items: list[InventoryItem] = []
    item_found = False

    for item in inventory.items:
        if item.item_id == item_id:
            updated_items.append(
                InventoryItem(
                    item_id=item.item_id,
                    quantity=item.quantity + quantity,
                )
            )
            item_found = True
        else:
            updated_items.append(item)

    if not item_found:
        updated_items.append(InventoryItem(item_id=item_id, quantity=quantity))

    return InventoryState(items=tuple(updated_items))


def apply_player_delta(
    player: PlayerState,
    *,
    hp_change: int = 0,
    exp_gain: int = 0,
    gold_change: int = 0,
) -> PlayerState:
    """Return player state after applying bounded HP, EXP, and gold changes."""
    return PlayerState(
        hp=max(0, player.hp + hp_change),
        exp=max(0, player.exp + exp_gain),
        gold=max(0, player.gold + gold_change),
    )


def add_skill_exp(
    skill_book: SkillBook,
    *,
    skill_id: str,
    exp: int,
) -> SkillBook:
    """Return skill book with exp added for the given skill."""
    if exp <= 0:
        return skill_book

    updated_skills: list[SkillProgress] = []
    skill_found = False

    for skill in skill_book.skills:
        if skill.skill_id == skill_id:
            updated_skills.append(
                SkillProgress(
                    skill_id=skill.skill_id,
                    level=skill.level,
                    exp=skill.exp + exp,
                )
            )
            skill_found = True
        else:
            updated_skills.append(skill)

    if not skill_found:
        updated_skills.append(SkillProgress(skill_id=skill_id, level=1, exp=exp))

    return SkillBook(skills=tuple(updated_skills))


def update_quest_progress(
    quest_log: QuestLog,
    *,
    quest_id: str,
    status: str,
    progress: int,
) -> QuestLog:
    """Return quest log with an updated quest entry."""
    updated_quests: list[QuestProgress] = []
    quest_found = False

    for quest in quest_log.quests:
        if quest.quest_id == quest_id:
            updated_quests.append(
                QuestProgress(
                    quest_id=quest.quest_id,
                    status=status,
                    progress=progress,
                )
            )
            quest_found = True
        else:
            updated_quests.append(quest)

    if not quest_found:
        updated_quests.append(
            QuestProgress(
                quest_id=quest_id,
                status=status,
                progress=progress,
            )
        )

    return QuestLog(quests=tuple(updated_quests))


def discover_location(
    world: WorldState,
    *,
    location_id: str,
) -> WorldState:
    """Return world state after visiting and discovering a location."""
    discovered = list(world.discovered_locations)
    if location_id not in discovered:
        discovered.append(location_id)

    return WorldState(
        current_location=location_id,
        discovered_locations=tuple(discovered),
    )


def update_npc_memory(
    npc_memory: NpcMemory,
    *,
    npc_id: str,
    relation_delta: int = 0,
    memory: str | None = None,
) -> NpcMemory:
    """Return NPC memory with relation and memory changes applied."""
    updated_npcs: list[NpcState] = []
    npc_found = False

    for npc in npc_memory.npcs:
        if npc.npc_id == npc_id:
            memories = list(npc.memories)
            if memory is not None and memory not in memories:
                memories.append(memory)
            updated_npcs.append(
                NpcState(
                    npc_id=npc.npc_id,
                    relation=npc.relation + relation_delta,
                    memories=tuple(memories),
                )
            )
            npc_found = True
        else:
            updated_npcs.append(npc)

    if not npc_found:
        memories = (memory,) if memory is not None else ()
        updated_npcs.append(
            NpcState(
                npc_id=npc_id,
                relation=relation_delta,
                memories=memories,
            )
        )

    return NpcMemory(npcs=tuple(updated_npcs))


def level_up_skill(
    skill_book: SkillBook,
    *,
    skill_id: str,
) -> SkillBook:
    """Return skill book with level increased for the given skill."""
    updated_skills: list[SkillProgress] = []
    skill_found = False

    for skill in skill_book.skills:
        if skill.skill_id == skill_id:
            updated_skills.append(
                SkillProgress(
                    skill_id=skill.skill_id,
                    level=skill.level + 1,
                    exp=0,
                )
            )
            skill_found = True
        else:
            updated_skills.append(skill)

    if not skill_found:
        updated_skills.append(SkillProgress(skill_id=skill_id, level=2, exp=0))

    return SkillBook(skills=tuple(updated_skills))
