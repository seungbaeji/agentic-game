from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.battle import serialize_battle_actions
from agentic_game.flow.craft import serialize_craft_actions
from agentic_game.flow.exploration import serialize_exploration_actions
from agentic_game.flow.models import SubgraphName
from agentic_game.flow.quest import serialize_quest_actions
from agentic_game.flow.trade import serialize_trade_actions


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
    trade_keywords = (
        "trade",
        "shop",
        "merchant",
        "buy",
        "sell",
        "거래",
        "상점",
        "상인",
        "구매",
        "판매",
        "흥정",
        "가격",
        "수락",
    )
    quest_keywords = (
        "quest",
        "mission",
        "퀘스트",
        "임무",
        "의뢰",
        "진행",
        "목표",
        "달성",
        "보고",
        "완료",
        "포기",
    )

    if any(keyword in normalized_text for keyword in battle_keywords):
        return SubgraphName.BATTLE

    if any(keyword in normalized_text for keyword in craft_keywords):
        return SubgraphName.CRAFT

    if any(keyword in normalized_text for keyword in exploration_keywords):
        return SubgraphName.EXPLORATION

    if any(keyword in normalized_text for keyword in quest_keywords):
        return SubgraphName.QUEST

    if any(keyword in normalized_text for keyword in trade_keywords):
        return SubgraphName.TRADE

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


def infer_trade_event(phase: TradePhase, user_text: str) -> TradeEvent | None:
    """Infer a trade event from explicit commerce keywords."""
    available_events = {action["event"] for action in serialize_trade_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        TradeEvent.SELECT_ITEM: ("select", "item", "아이템", "고를", "선택"),
        TradeEvent.OFFER: ("offer", "price", "제안", "가격", "흥정"),
        TradeEvent.ACCEPT_PRICE: ("accept", "수락", "좋아", "구매"),
        TradeEvent.DECLINE_PRICE: ("decline", "거절", "비싸", "다시"),
        TradeEvent.CONFIRM: ("confirm", "확정", "교환", "완료"),
        TradeEvent.CANCEL: ("cancel", "취소", "그만"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None


def infer_quest_event(phase: QuestPhase, user_text: str) -> QuestEvent | None:
    """Infer a quest event from explicit quest progress keywords."""
    available_events = {action["event"] for action in serialize_quest_actions(phase)}
    normalized_text = user_text.lower()
    event_by_keywords = {
        QuestEvent.ACCEPT: ("accept", "수락", "받을"),
        QuestEvent.START: ("start", "시작", "출발"),
        QuestEvent.PROGRESS: ("progress", "진행", "달성", "목표"),
        QuestEvent.COMPLETE: ("complete", "완료", "보고", "보상"),
        QuestEvent.ABANDON: ("abandon", "포기", "그만"),
        QuestEvent.FAIL: ("fail", "실패"),
    }

    for event, keywords in event_by_keywords.items():
        if event.value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
