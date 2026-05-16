from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import StateGraph

from agentic_game.agent.models import ParentNode
from agentic_game.agent.nodes.parent import (
    make_parent_decision_node,
    make_parent_response_node,
    parent_ask_user_node,
    parent_route,
)
from agentic_game.agent.runtime.subgraph import (
    make_battle_wrapper,
    make_craft_wrapper,
    make_exploration_wrapper,
    make_quest_wrapper,
    make_trade_wrapper,
)
from agentic_game.agent.runtime.tools import ToolInvoker
from agentic_game.agent.state import ParentState
from agentic_game.agent.transitions import PARENT_DECISION_EDGES, PARENT_DIRECT_EDGES
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.battle import BattleResult
from agentic_game.domain.craft import CraftResult


def build_parent_graph(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    craft_item_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleResult],
    craft_item: Callable[..., CraftResult],
    random: RandomPort,
):
    """Build the top-level LangGraph that routes between available workflows."""
    builder = StateGraph(ParentState)

    builder.add_node(ParentNode.DECISION, make_parent_decision_node(llm))
    builder.add_node(
        ParentNode.BATTLE,
        make_battle_wrapper(
            store,
            llm,
            resolve_battle_tool,
            resolve_battle_action,
            random,
        ),
    )
    builder.add_node(
        ParentNode.CRAFT,
        make_craft_wrapper(
            store,
            llm,
            craft_item_tool,
            craft_item,
            random,
        ),
    )
    builder.add_node(
        ParentNode.EXPLORATION,
        make_exploration_wrapper(store),
    )
    builder.add_node(
        ParentNode.TRADE,
        make_trade_wrapper(store),
    )
    builder.add_node(
        ParentNode.QUEST,
        make_quest_wrapper(store),
    )
    builder.add_node(ParentNode.RESPONSE, make_parent_response_node(llm))
    builder.add_node(ParentNode.ASK_USER, parent_ask_user_node)

    builder.set_entry_point(ParentNode.DECISION)

    builder.add_conditional_edges(
        ParentNode.DECISION,
        parent_route,
        PARENT_DECISION_EDGES,
    )

    for source, target in PARENT_DIRECT_EDGES:
        builder.add_edge(source, target)

    return builder.compile()
