from __future__ import annotations

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.nodes.trade import (
    make_trade_execute_node,
    trade_ask_user_node,
    trade_decision_node,
    trade_flow_node,
    trade_hitl_node,
    trade_response_node,
)
from agentic_game.agent.state import TradeState
from agentic_game.application.ports import StorePort
from agentic_game.engine.tool_runner import ToolInvoker


def build_trade_subgraph(
    store: StorePort,
    exchange_item_tool: ToolInvoker,
):
    """Build the LangGraph subgraph that runs the trade workflow."""
    return build_simple_scenario_subgraph(
        state_schema=TradeState,
        graph_nodes=ScenarioGraphNodes(
            decision=trade_decision_node,
            flow=trade_flow_node,
            hitl=trade_hitl_node,
            execute=make_trade_execute_node(store, exchange_item_tool),
            response=trade_response_node,
            ask_user=trade_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
