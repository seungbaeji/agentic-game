from __future__ import annotations

from collections.abc import Callable

from agentic_game.agent.graph.scenario import (
    ScenarioGraphNodes,
    build_scenario_subgraph,
)
from agentic_game.agent.models import BattleNode
from agentic_game.agent.nodes.battle import (
    battle_ask_user_node,
    battle_execute_tool_node,
    battle_flow_node,
    battle_hitl_node,
    battle_route,
    make_battle_decision_node,
    make_battle_response_node,
)
from agentic_game.agent.runtime.tools import ToolInvoker
from agentic_game.agent.state import BattleState
from agentic_game.agent.transitions import (
    BATTLE_DIRECT_EDGES,
    BATTLE_FLOW_EDGES,
    BATTLE_HITL_EDGES,
)
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.battle import BattleResult


def build_battle_subgraph(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleResult],
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

    return build_scenario_subgraph(
        state_schema=BattleState,
        node_names=BattleNode,
        graph_nodes=ScenarioGraphNodes(
            decision=make_battle_decision_node(llm),
            flow=battle_flow_node,
            hitl=battle_hitl_node,
            execute=execute_with_store,
            response=make_battle_response_node(llm),
            ask_user=battle_ask_user_node,
        ),
        route=battle_route,
        flow_edges=BATTLE_FLOW_EDGES,
        hitl_edges=BATTLE_HITL_EDGES,
        direct_edges=BATTLE_DIRECT_EDGES,
    )
