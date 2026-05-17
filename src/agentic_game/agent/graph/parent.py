from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import StateGraph

from agentic_game.agent.models import ParentNode
from agentic_game.agent.nodes.parent import (
    make_parent_ask_user_node,
    make_parent_decision_node,
    make_parent_response_node,
    parent_route,
)
from agentic_game.agent.state import ParentState
from agentic_game.agent.transitions import PARENT_DECISION_EDGES, PARENT_DIRECT_EDGES
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.application.usecases.battle import BattleActionResult
from agentic_game.application.usecases.craft import CraftItemResult
from agentic_game.engine.tool_runner import ToolInvoker
from agentic_game.scenarios.registry import (
    make_battle_wrapper,
    make_craft_wrapper,
    make_dialogue_wrapper,
    make_exploration_wrapper,
    make_quest_wrapper,
    make_skill_training_wrapper,
    make_trade_wrapper,
)

SIMPLE_PARENT_WRAPPERS = {
    ParentNode.EXPLORATION: make_exploration_wrapper,
    ParentNode.QUEST: make_quest_wrapper,
    ParentNode.SKILL_TRAINING: make_skill_training_wrapper,
}


def build_parent_graph(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    craft_item_tool: ToolInvoker,
    exchange_item_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleActionResult],
    craft_item: Callable[..., CraftItemResult],
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
        ParentNode.TRADE,
        make_trade_wrapper(
            store,
            exchange_item_tool,
        ),
    )
    builder.add_node(ParentNode.DIALOGUE, make_dialogue_wrapper(store, llm))
    for node, make_wrapper in SIMPLE_PARENT_WRAPPERS.items():
        builder.add_node(node, make_wrapper(store))

    builder.add_node(ParentNode.RESPONSE, make_parent_response_node(llm))
    builder.add_node(ParentNode.ASK_USER, make_parent_ask_user_node(llm))

    builder.set_entry_point(ParentNode.DECISION)

    builder.add_conditional_edges(
        ParentNode.DECISION,
        parent_route,
        PARENT_DECISION_EDGES,
    )

    for source, target in PARENT_DIRECT_EDGES:
        builder.add_edge(source, target)

    return builder.compile()
