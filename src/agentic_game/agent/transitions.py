from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.models import BattleNode, CraftNode, ParentNode

PARENT_DECISION_EDGES = {
    ParentNode.BATTLE: ParentNode.BATTLE,
    ParentNode.CRAFT: ParentNode.CRAFT,
    ParentNode.EXPLORATION: ParentNode.EXPLORATION,
    ParentNode.TRADE: ParentNode.TRADE,
    ParentNode.QUEST: ParentNode.QUEST,
    ParentNode.DIALOGUE: ParentNode.DIALOGUE,
    ParentNode.ASK_USER: ParentNode.ASK_USER,
}

PARENT_DIRECT_EDGES = [
    (ParentNode.BATTLE, ParentNode.RESPONSE),
    (ParentNode.CRAFT, ParentNode.RESPONSE),
    (ParentNode.EXPLORATION, ParentNode.RESPONSE),
    (ParentNode.TRADE, ParentNode.RESPONSE),
    (ParentNode.QUEST, ParentNode.RESPONSE),
    (ParentNode.DIALOGUE, ParentNode.RESPONSE),
    (ParentNode.RESPONSE, END),
    (ParentNode.ASK_USER, END),
]

BATTLE_FLOW_EDGES = {
    BattleNode.HITL: BattleNode.HITL,
    BattleNode.EXECUTE: BattleNode.EXECUTE,
    BattleNode.RESPONSE: BattleNode.RESPONSE,
    BattleNode.ASK_USER: BattleNode.ASK_USER,
}

BATTLE_HITL_EDGES = {
    BattleNode.DECISION: BattleNode.DECISION,
    BattleNode.RESPONSE: BattleNode.RESPONSE,
}

BATTLE_DIRECT_EDGES = [
    (BattleNode.DECISION, BattleNode.FLOW),
    (BattleNode.EXECUTE, BattleNode.RESPONSE),
    (BattleNode.RESPONSE, END),
    (BattleNode.ASK_USER, END),
]

CRAFT_DECISION_EDGES = {
    CraftNode.FLOW: CraftNode.FLOW,
    CraftNode.ASK_USER: CraftNode.ASK_USER,
}

CRAFT_FLOW_EDGES = {
    CraftNode.HITL: CraftNode.HITL,
    CraftNode.EXECUTE: CraftNode.EXECUTE,
    CraftNode.RESPONSE: CraftNode.RESPONSE,
    CraftNode.ASK_USER: CraftNode.ASK_USER,
}

CRAFT_HITL_EDGES = {
    CraftNode.DECISION: CraftNode.DECISION,
    CraftNode.RESPONSE: CraftNode.RESPONSE,
    CraftNode.ASK_USER: CraftNode.ASK_USER,
}

CRAFT_DIRECT_EDGES = [
    (CraftNode.EXECUTE, CraftNode.RESPONSE),
    (CraftNode.RESPONSE, END),
    (CraftNode.ASK_USER, END),
]
