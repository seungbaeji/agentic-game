"""Deterministic keyword intent rules for scenario routing and events."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.domain.dialogue import DialogueEvent, DialoguePhase
from agentic_game.domain.exploration import ExplorationEvent, ExplorationPhase
from agentic_game.domain.quest import QuestEvent, QuestPhase
from agentic_game.domain.skill_training import SkillTrainingEvent, SkillTrainingPhase
from agentic_game.domain.trade import TradeEvent, TradePhase
from agentic_game.flow.battle import serialize_battle_actions
from agentic_game.flow.craft import serialize_craft_actions
from agentic_game.flow.dialogue import serialize_dialogue_actions
from agentic_game.flow.exploration import serialize_exploration_actions
from agentic_game.flow.models import SubgraphName
from agentic_game.flow.quest import serialize_quest_actions
from agentic_game.flow.skill_training import serialize_skill_training_actions
from agentic_game.flow.trade import serialize_trade_actions


def detect_parent_subgraph(user_text: str) -> SubgraphName | None:
    """Detect the top-level subgraph from explicit user intent keywords."""
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
    dialogue_keywords = (
        "dialogue",
        "talk",
        "npc",
        "rumor",
        "대화",
        "말",
        "소문",
        "감사",
        "고마",
        "보상",
    )
    skill_training_keywords = (
        "skill",
        "training",
        "practice",
        "스킬",
        "훈련",
        "연습",
        "검술",
        "연금술",
        "레벨",
    )

    if any(keyword in normalized_text for keyword in battle_keywords):
        return SubgraphName.BATTLE

    if any(keyword in normalized_text for keyword in exploration_keywords):
        return SubgraphName.EXPLORATION

    if any(keyword in normalized_text for keyword in skill_training_keywords):
        return SubgraphName.SKILL_TRAINING

    if any(keyword in normalized_text for keyword in craft_keywords):
        return SubgraphName.CRAFT

    if any(keyword in normalized_text for keyword in quest_keywords):
        return SubgraphName.QUEST

    if any(keyword in normalized_text for keyword in dialogue_keywords):
        return SubgraphName.DIALOGUE

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


def detect_battle_event(phase: BattlePhase, user_text: str) -> BattleEvent | None:
    """Detect a battle event from explicit user action keywords."""
    available_events = {action["event"] for action in serialize_battle_actions(phase)}
    event_by_keywords = {
        BattleEvent.ATTACK: ("attack", "공격"),
        BattleEvent.DEFEND: ("defend", "방어"),
        BattleEvent.FLEE: ("flee", "도망", "회피"),
    }
    return _detect_event(event_by_keywords, available_events, user_text)


def detect_craft_event(phase: CraftPhase, user_text: str) -> CraftEvent | None:
    """Detect a craft event from explicit recipe keywords."""
    available_events = {action["event"] for action in serialize_craft_actions(phase)}
    event_by_keywords = {
        CraftEvent.CRAFT_POTION: ("potion", "포션", "회복 물약"),
        CraftEvent.CRAFT_SWORD: ("sword", "검", "칼"),
    }
    return _detect_event(event_by_keywords, available_events, user_text)


def detect_exploration_event(
    phase: ExplorationPhase,
    user_text: str,
) -> ExplorationEvent | None:
    """Detect an exploration event from explicit path and action keywords."""
    available_events = {
        action["event"] for action in serialize_exploration_actions(phase)
    }
    event_by_keywords = {
        ExplorationEvent.TAKE_FOREST: ("forest", "숲", "숲길"),
        ExplorationEvent.TAKE_RUINS: ("ruins", "유적"),
        ExplorationEvent.INSPECT: ("inspect", "조사", "살펴"),
        ExplorationEvent.RETREAT: ("retreat", "후퇴", "돌아"),
        ExplorationEvent.COMPLETE: ("complete", "완료", "마칠"),
    }
    return _detect_event(event_by_keywords, available_events, user_text)


def detect_trade_event(phase: TradePhase, user_text: str) -> TradeEvent | None:
    """Detect a trade event from explicit commerce keywords."""
    available_events = {action["event"] for action in serialize_trade_actions(phase)}
    event_by_keywords = {
        TradeEvent.SELECT_ITEM: ("select", "item", "아이템", "고를", "선택"),
        TradeEvent.OFFER: ("offer", "price", "제안", "가격", "흥정"),
        TradeEvent.ACCEPT_PRICE: ("accept", "수락", "좋아", "구매"),
        TradeEvent.DECLINE_PRICE: ("decline", "거절", "비싸", "다시"),
        TradeEvent.CONFIRM: ("confirm", "확정", "교환", "완료"),
        TradeEvent.CANCEL: ("cancel", "취소", "그만"),
    }
    return _detect_event(event_by_keywords, available_events, user_text)


def detect_quest_event(phase: QuestPhase, user_text: str) -> QuestEvent | None:
    """Detect a quest event from explicit quest progress keywords."""
    available_events = {action["event"] for action in serialize_quest_actions(phase)}
    event_by_keywords = {
        QuestEvent.ACCEPT: ("accept", "수락", "받을"),
        QuestEvent.START: ("start", "시작", "출발"),
        QuestEvent.PROGRESS: ("progress", "진행", "달성", "목표"),
        QuestEvent.COMPLETE: ("complete", "완료", "보고", "보상"),
        QuestEvent.ABANDON: ("abandon", "포기", "그만"),
        QuestEvent.FAIL: ("fail", "실패"),
    }
    return _detect_event(event_by_keywords, available_events, user_text)


def detect_dialogue_event(
    phase: DialoguePhase,
    user_text: str,
) -> DialogueEvent | None:
    """Detect a dialogue event from explicit NPC conversation keywords."""
    available_events = {action["event"] for action in serialize_dialogue_actions(phase)}
    event_by_keywords = {
        DialogueEvent.ASK_RUMOR: ("rumor", "소문"),
        DialogueEvent.ASK_TRADE: ("trade", "거래"),
        DialogueEvent.THANK: ("thank", "감사", "고마"),
        DialogueEvent.LEAVE: ("leave", "떠날", "종료", "그만"),
        DialogueEvent.CLAIM_REWARD: ("reward", "보상", "받을"),
    }
    return _detect_event(event_by_keywords, available_events, user_text)


def detect_skill_training_event(
    phase: SkillTrainingPhase,
    user_text: str,
) -> SkillTrainingEvent | None:
    """Detect a skill training event from explicit training keywords."""
    available_events = {
        action["event"] for action in serialize_skill_training_actions(phase)
    }
    event_by_keywords = {
        SkillTrainingEvent.SELECT_SWORDSMANSHIP: ("sword", "검술"),
        SkillTrainingEvent.SELECT_ALCHEMY: ("alchemy", "연금술"),
        SkillTrainingEvent.PRACTICE: ("practice", "train", "훈련", "연습"),
        SkillTrainingEvent.RETRY: ("retry", "다시"),
        SkillTrainingEvent.LEVEL_UP: ("level", "레벨", "성장"),
        SkillTrainingEvent.COMPLETE: ("complete", "완료", "마칠"),
    }
    return _detect_event(event_by_keywords, available_events, user_text)


def _detect_event[EventT](
    event_by_keywords: Mapping[EventT, Sequence[str]],
    available_events: set[Any],
    user_text: str,
) -> EventT | None:
    normalized_text = user_text.lower()
    for event, keywords in event_by_keywords.items():
        event_value = getattr(event, "value", event)
        if event_value in available_events and any(
            keyword in normalized_text for keyword in keywords
        ):
            return event

    return None
