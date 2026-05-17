from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from agentic_game.agent.state import BattleState, CraftState, TradeState
from agentic_game.agent.types import PhasePayloadRefs, RuntimeState, ToolInput
from agentic_game.application.game_state import GameStateRepository
from agentic_game.application.ports import RandomPort, StorePort
from agentic_game.domain.battle import BattlePhase
from agentic_game.domain.craft import CraftPhase
from agentic_game.domain.trade import TradePhase
from agentic_game.flow.battle import BATTLE_TOOL_BINDINGS
from agentic_game.flow.craft import CRAFT_TOOL_BINDINGS
from agentic_game.flow.models import ToolBinding
from agentic_game.flow.trade import TRADE_TOOL_BINDINGS
from agentic_game.scenarios.spec import ScenarioNode
from agentic_game.tools.types import ToolResult


class ToolInvoker(Protocol):
    def invoke(self, input: ToolInput) -> ToolResult:
        """Invoke a hydrated LangChain tool and return its internal result."""
        ...


def persist_tool_result(
    *,
    store: StorePort,
    state: RuntimeState,
    subgraph: str,
    phase: str,
    tool_result: ToolResult,
) -> PhasePayloadRefs:
    """Persist raw, LLM, and UI tool payloads and return updated refs."""
    raw_update = store.persist_phase_payload(
        state=state,
        subgraph=subgraph,
        phase=phase,
        payload_name="raw",
        value=tool_result.raw,
    )
    llm_update = store.persist_phase_payload(
        state={**state, **raw_update},
        subgraph=subgraph,
        phase=phase,
        payload_name="llm",
        value=tool_result.llm,
    )
    return store.persist_phase_payload(
        state={**state, **llm_update},
        subgraph=subgraph,
        phase=phase,
        payload_name="ui",
        value=tool_result.ui,
    )


def execute_bound_tool[StateT: RuntimeState, EventT](
    *,
    state: StateT,
    store: StorePort,
    binding: ToolBinding[EventT],
    tool: ToolInvoker,
    injected_input: ToolInput,
    subgraph: str,
    phase: str,
    summarize_tool_result: Callable[[ToolResult], str] | None = None,
) -> StateT:
    """Invoke a bound tool, persist its payloads, and return a graph state update."""
    tool_result = tool.invoke(
        {
            **binding.tool_input,
            **injected_input,
        }
    )
    ref_update = persist_tool_result(
        store=store,
        state=state,
        subgraph=subgraph,
        phase=phase,
        tool_result=tool_result,
    )

    return {
        "latest_refs": ref_update["latest_refs"],
        "history_refs": ref_update["history_refs"],
        "response": (
            summarize_tool_result(tool_result)
            if summarize_tool_result is not None
            else tool_result.llm["summary"]
        ),
        "next_node": ScenarioNode.RESPONSE,
    }


def execute_battle_tool(
    *,
    state: BattleState,
    store: StorePort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., object],
    random: RandomPort,
    summarize_tool_result: Callable[[ToolResult], str] | None = None,
) -> BattleState:
    """Invoke the battle tool and return the battle graph state update."""
    event = state["event"]
    binding = BATTLE_TOOL_BINDINGS.get(event)
    if binding is None:
        return {
            "reason": f"tool로 실행할 수 없는 battle event입니다: {event}",
            "next_node": ScenarioNode.ASK_USER,
        }

    return execute_bound_tool(
        state=state,
        store=store,
        binding=binding,
        tool=resolve_battle_tool,
        injected_input={
            "resolve_battle_action": resolve_battle_action,
            "random": random,
            "game_state": GameStateRepository(store),
        },
        subgraph="battle",
        phase=BattlePhase.RESOLVE.value,
        summarize_tool_result=summarize_tool_result,
    )


def execute_craft_tool(
    *,
    state: CraftState,
    store: StorePort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., object],
    random: RandomPort,
    summarize_tool_result: Callable[[ToolResult], str] | None = None,
) -> CraftState:
    """Invoke the craft tool and return the craft graph state update."""
    event = state["event"]
    binding = CRAFT_TOOL_BINDINGS.get(event)
    if binding is None:
        return {
            "reason": f"tool로 실행할 수 없는 craft event입니다: {event}",
            "next_node": ScenarioNode.ASK_USER,
        }

    return execute_bound_tool(
        state=state,
        store=store,
        binding=binding,
        tool=craft_item_tool,
        injected_input={
            **state.get("craft_plan", {}),
            "craft_item": craft_item,
            "random": random,
            "game_state": GameStateRepository(store),
        },
        subgraph="craft",
        phase=CraftPhase.RESULT.value,
        summarize_tool_result=summarize_tool_result,
    )


def execute_trade_tool(
    *,
    state: TradeState,
    store: StorePort,
    exchange_item_tool: ToolInvoker,
    exchange_item: Callable[..., object],
) -> TradeState:
    """Invoke the trade exchange tool and return the trade graph state update."""
    event = state["event"]
    binding = TRADE_TOOL_BINDINGS.get(event)
    if binding is None:
        return {
            "reason": f"tool로 실행할 수 없는 trade event입니다: {event}",
            "next_node": ScenarioNode.ASK_USER,
        }

    return execute_bound_tool(
        state=state,
        store=store,
        binding=binding,
        tool=exchange_item_tool,
        injected_input={
            "exchange_item": exchange_item,
            "game_state": GameStateRepository(store),
        },
        subgraph="trade",
        phase=TradePhase.EXCHANGE.value,
    )
