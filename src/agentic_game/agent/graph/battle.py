from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.graph.scenario_graph import (
    ScenarioGraphNodes,
    build_simple_scenario_subgraph,
)
from agentic_game.agent.nodes.battle import (
    battle_ask_user_node,
    battle_execute_tool_node,
    battle_flow_node,
    battle_hitl_node,
    make_battle_decision_node,
    make_battle_response_node,
)
from agentic_game.agent.nodes.scenario_nodes import scenario_decision_route, scenario_route
from agentic_game.agent.state import BattleState
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.application.usecases.battle import BattleActionResult
from agentic_game.engine.tool_runner import ToolInvoker


def build_battle_subgraph(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleActionResult],
    random: RandomPort,
):
    """Build the LangGraph subgraph that runs the battle workflow."""
    def execute_with_store(state: BattleState) -> BattleState:
        """Execute the battle tool with dependencies closed over from bootstrap."""
        return battle_execute_tool_node(
            state,
            store=store,
            resolve_battle_tool=resolve_battle_tool,
            resolve_battle_action=resolve_battle_action,
            random=random,
        )

    return build_simple_scenario_subgraph(
        state_schema=BattleState,
        graph_nodes=ScenarioGraphNodes(
            decision=make_battle_decision_node(llm),
            flow=battle_flow_node,
            hitl=battle_hitl_node,
            execute=execute_with_store,
            response=make_battle_response_node(llm),
            ask_user=battle_ask_user_node,
        ),
        route=scenario_route,
        decision_route=scenario_decision_route,
    )
