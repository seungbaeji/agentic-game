from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.flow.battle import serialize_battle_actions
from agentic_game.flow.craft import serialize_craft_actions
from agentic_game.flow.exploration import serialize_exploration_actions
from agentic_game.flow.models import SubgraphName


def infer_parent_subgraph(user_text: str) -> SubgraphName | None:
    """Infer the top-level subgraph from explicit user intent keywords."""
    normalized_text = user_text.lower()
    battle_keywords = (
        "battle",
        "fight",
        "monster",
        "attack",
        "전투",
        "몬스터",
        "공격",
        "방어",
        "도망",
    )
    craft_keywords = ("craft", "item", "potion", "sword", "제작", "아이템", "포션", "검", "칼")
    exploration_keywords = (
        "explore",
        "exploration",
        "forest",
        "ruins",
        "탐험",
        "숲",
        "숲길",
        "유적",
    )

    if any(keyword in normalized_text for keyword in battle_keywords):
        return SubgraphName.BATTLE

    if any(keyword in normalized_text for keyword in craft_keywords):
        return SubgraphName.CRAFT

    if any(keyword in normalized_text for keyword in exploration_keywords):
        return SubgraphName.EXPLORATION

    return None


def is_capability_question(user_text: str) -> bool:
    """Return whether the user is asking what the system can do."""
    normalized_text = user_text.lower()
    return any(
        keyword in normalized_text
        for keyword in ("할 수", "뭐 할", "무엇을", "어떤걸", "what can", "capabil")
    )


def infer_battle_event(phase: BattlePhase, user_text: str) -> BattleEvent | None:
    """Infer a battle event from explicit user action keywords."""
    available_events = {action["event"] for action in serialize_battle_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        BattleEvent.ATTACK: ("attack", "공격"),
        BattleEvent.DEFEND: ("defend", "방어"),
        BattleEvent.FLEE: ("flee", "도망", "회피"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None


def infer_craft_event(phase: CraftPhase, user_text: str) -> CraftEvent | None:
    """Infer a craft event from explicit recipe keywords."""
    available_events = {action["event"] for action in serialize_craft_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        CraftEvent.CRAFT_POTION: ("potion", "포션", "회복 물약"),
        CraftEvent.CRAFT_SWORD: ("sword", "검", "칼"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None


def infer_exploration_event(
    phase: ExplorationPhase,
    user_text: str,
) -> ExplorationEvent | None:
    """Infer an exploration event from explicit path and action keywords."""
    available_events = {
        action["event"] for action in serialize_exploration_actions(phase)
    }
    normalized_text = user_text.lower()
    event_by_keywords = {
        ExplorationEvent.TAKE_FOREST: ("forest", "숲", "숲길"),
        ExplorationEvent.TAKE_RUINS: ("ruins", "유적"),
        ExplorationEvent.INSPECT: ("inspect", "조사", "살펴"),
        ExplorationEvent.RETREAT: ("retreat", "후퇴", "돌아"),
        ExplorationEvent.COMPLETE: ("complete", "완료", "마칠"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
