from __future__ import annotations

from langgraph.graph import END

from agentic_game.agent.models import ParentNode
from agentic_game.agent.transitions import (
    PARENT_DECISION_EDGES,
    PARENT_DIRECT_EDGES,
)


def test_parent_node_transitions_are_declared_as_tables() -> None:
    assert PARENT_DECISION_EDGES == {
        ParentNode.BATTLE: ParentNode.BATTLE,
        ParentNode.CRAFT: ParentNode.CRAFT,
        ParentNode.EXPLORATION: ParentNode.EXPLORATION,
        ParentNode.TRADE: ParentNode.TRADE,
        ParentNode.QUEST: ParentNode.QUEST,
        ParentNode.DIALOGUE: ParentNode.DIALOGUE,
        ParentNode.SKILL_TRAINING: ParentNode.SKILL_TRAINING,
        ParentNode.ASK_USER: ParentNode.ASK_USER,
    }
    assert PARENT_DIRECT_EDGES == [
        (ParentNode.BATTLE, ParentNode.RESPONSE),
        (ParentNode.CRAFT, ParentNode.RESPONSE),
        (ParentNode.EXPLORATION, ParentNode.RESPONSE),
        (ParentNode.TRADE, ParentNode.RESPONSE),
        (ParentNode.QUEST, ParentNode.RESPONSE),
        (ParentNode.DIALOGUE, ParentNode.RESPONSE),
        (ParentNode.SKILL_TRAINING, ParentNode.RESPONSE),
        (ParentNode.RESPONSE, END),
        (ParentNode.ASK_USER, END),
    ]
