from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from agentic_game.flow.models import SubgraphName


class ParentNode(StrEnum):
    DECISION = "parent_decision"
    NAVIGATE = "parent_navigate"
    BATTLE = "battle_subgraph"
    CRAFT = "craft_subgraph"
    EXPLORATION = "exploration_subgraph"
    TRADE = "trade_subgraph"
    QUEST = "quest_subgraph"
    DIALOGUE = "dialogue_subgraph"
    RESPONSE = "parent_response"
    ASK_USER = "parent_ask_user"


class BattleNode(StrEnum):
    DECISION = "battle_decision"
    FLOW = "battle_flow"
    HITL = "battle_hitl"
    EXECUTE = "battle_execute_tool"
    RESPONSE = "battle_response"
    ASK_USER = "battle_ask_user"


class CraftNode(StrEnum):
    DECISION = "craft_decision"
    FLOW = "craft_flow"
    HITL = "craft_hitl"
    EXECUTE = "craft_execute_tool"
    RESPONSE = "craft_response"
    ASK_USER = "craft_ask_user"


@dataclass(frozen=True)
class SubgraphEntry:
    name: SubgraphName
    label: str
    description: str
    node: ParentNode


SUBGRAPH_REGISTRY: dict[SubgraphName, SubgraphEntry] = {
    SubgraphName.BATTLE: SubgraphEntry(
        name=SubgraphName.BATTLE,
        label="전투",
        description="몬스터와 싸우고 랜덤 전투 결과를 처리합니다.",
        node=ParentNode.BATTLE,
    ),
    SubgraphName.CRAFT: SubgraphEntry(
        name=SubgraphName.CRAFT,
        label="제작",
        description="아이템 제작을 시도하고 랜덤 성공/실패를 처리합니다.",
        node=ParentNode.CRAFT,
    ),
    SubgraphName.EXPLORATION: SubgraphEntry(
        name=SubgraphName.EXPLORATION,
        label="탐험",
        description="갈림길을 선택하고 조우나 발견을 처리합니다.",
        node=ParentNode.EXPLORATION,
    ),
    SubgraphName.TRADE: SubgraphEntry(
        name=SubgraphName.TRADE,
        label="거래",
        description="아이템을 선택하고 가격 확인과 교환을 처리합니다.",
        node=ParentNode.TRADE,
    ),
    SubgraphName.QUEST: SubgraphEntry(
        name=SubgraphName.QUEST,
        label="퀘스트",
        description="퀘스트 수락, 진행, 보고, 완료 또는 실패를 처리합니다.",
        node=ParentNode.QUEST,
    ),
    SubgraphName.DIALOGUE: SubgraphEntry(
        name=SubgraphName.DIALOGUE,
        label="대화",
        description="NPC 대화 선택지, 반응, 보상 수령을 처리합니다.",
        node=ParentNode.DIALOGUE,
    ),
}
