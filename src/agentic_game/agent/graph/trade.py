from __future__ import annotations

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.nodes.trade import (
    trade_ask_user_node,
    trade_decision_node,
    trade_execute_node,
    trade_flow_node,
    trade_hitl_node,
    trade_response_node,
)
from agentic_game.agent.state import TradeState


def build_trade_subgraph():
    """Build the LangGraph subgraph that runs the trade workflow."""
    return build_simple_scenario_subgraph(
        state_schema=TradeState,
        graph_nodes=ScenarioGraphNodes(
            decision=trade_decision_node,
            flow=trade_flow_node,
            hitl=trade_hitl_node,
            execute=trade_execute_node,
            response=trade_response_node,
            ask_user=trade_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
