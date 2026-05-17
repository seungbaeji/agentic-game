"""Parent-level intent routing between game scenarios."""

from __future__ import annotations

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
