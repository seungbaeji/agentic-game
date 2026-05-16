from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.models import BattleNode, CraftNode, ParentNode
from agentic_game.agent.transitions import (
    BATTLE_DIRECT_EDGES,
    BATTLE_FLOW_EDGES,
    BATTLE_HITL_EDGES,
    CRAFT_DECISION_EDGES,
    CRAFT_DIRECT_EDGES,
    CRAFT_FLOW_EDGES,
    CRAFT_HITL_EDGES,
    PARENT_DECISION_EDGES,
    PARENT_DIRECT_EDGES,
)


def test_parent_node_transitions_are_declared_as_tables() -> None:
    assert PARENT_DECISION_EDGES == {
        ParentNode.BATTLE: ParentNode.BATTLE,
        ParentNode.CRAFT: ParentNode.CRAFT,
        ParentNode.ASK_USER: ParentNode.ASK_USER,
    }
    assert PARENT_DIRECT_EDGES == [
        (ParentNode.BATTLE, ParentNode.RESPONSE),
        (ParentNode.CRAFT, ParentNode.RESPONSE),
        (ParentNode.RESPONSE, END),
        (ParentNode.ASK_USER, END),
    ]


def test_battle_node_transitions_are_declared_as_tables() -> None:
    assert BATTLE_FLOW_EDGES == {
        BattleNode.HITL: BattleNode.HITL,
        BattleNode.EXECUTE: BattleNode.EXECUTE,
        BattleNode.RESPONSE: BattleNode.RESPONSE,
        BattleNode.ASK_USER: BattleNode.ASK_USER,
    }
    assert BATTLE_HITL_EDGES == {
        BattleNode.DECISION: BattleNode.DECISION,
        BattleNode.RESPONSE: BattleNode.RESPONSE,
    }
    assert BATTLE_DIRECT_EDGES == [
        (BattleNode.DECISION, BattleNode.FLOW),
        (BattleNode.EXECUTE, BattleNode.RESPONSE),
        (BattleNode.RESPONSE, END),
        (BattleNode.ASK_USER, END),
    ]


def test_craft_node_transitions_are_declared_as_tables() -> None:
    assert CRAFT_DECISION_EDGES == {
        CraftNode.FLOW: CraftNode.FLOW,
        CraftNode.ASK_USER: CraftNode.ASK_USER,
    }
    assert CRAFT_FLOW_EDGES == {
        CraftNode.HITL: CraftNode.HITL,
        CraftNode.EXECUTE: CraftNode.EXECUTE,
        CraftNode.RESPONSE: CraftNode.RESPONSE,
        CraftNode.ASK_USER: CraftNode.ASK_USER,
    }
    assert CRAFT_HITL_EDGES == {
        CraftNode.DECISION: CraftNode.DECISION,
        CraftNode.RESPONSE: CraftNode.RESPONSE,
        CraftNode.ASK_USER: CraftNode.ASK_USER,
    }
    assert CRAFT_DIRECT_EDGES == [
        (CraftNode.EXECUTE, CraftNode.RESPONSE),
        (CraftNode.RESPONSE, END),
        (CraftNode.ASK_USER, END),
    ]
