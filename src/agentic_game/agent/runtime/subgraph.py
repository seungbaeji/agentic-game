from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from agentic_game.agent.graph.battle import build_battle_subgraph
from agentic_game.agent.graph.craft import build_craft_subgraph
from agentic_game.agent.graph.dialogue import build_dialogue_subgraph
from agentic_game.agent.graph.exploration import build_exploration_subgraph
from agentic_game.agent.graph.quest import build_quest_subgraph
from agentic_game.agent.graph.trade import build_trade_subgraph
from agentic_game.agent.models import ParentNode, SubgraphName
from agentic_game.agent.runtime.tools import ToolInvoker
from agentic_game.agent.state import CraftState, ParentState
from agentic_game.agent.types import RuntimePayload, StoreRefs
from agentic_game.application.ports import LLMPort, RandomPort, StorePort
from agentic_game.domain.battle import BattlePhase, BattleResult
from agentic_game.domain.craft import CraftPhase, CraftResult
from agentic_game.domain.dialogue import DialoguePhase
from agentic_game.domain.exploration import ExplorationPhase
from agentic_game.domain.quest import QuestPhase
from agentic_game.domain.trade import TradePhase
from agentic_game.flow.craft import answer_craft_result_question


class InvokableGraph(Protocol):
    def invoke(self, input: RuntimePayload) -> RuntimePayload:
        """Run a compiled graph with runtime state."""
        ...


type BeforeInvokeHook = Callable[
    [StorePort, RuntimePayload, ParentState, StoreRefs],
    ParentState | None,
]


def remove_runtime_routing(state: RuntimePayload) -> RuntimePayload:
    """Remove routing-only keys before persisting graph state."""
    persisted_state = dict(state)
    persisted_state.pop("next_node", None)
    return persisted_state


def load_latest_craft_result(
    store: StorePort,
    saved_state: CraftState,
) -> RuntimePayload | None:
    """Load the latest persisted craft UI result when one is referenced."""
    latest_refs = saved_state.get("latest_refs", {})
    if "result.ui" not in latest_refs:
        return None

    try:
        latest_result = store.get(
            namespace=("craft", "result", "ui"),
            key="latest",
        )
    except KeyError:
        return None

    return latest_result


def make_subgraph_wrapper(
    *,
    store: StorePort,
    graph: InvokableGraph,
    subgraph: SubgraphName,
    state_ref_key: str,
    state_namespace: tuple[str, str],
    initial_state: RuntimePayload,
    before_invoke: BeforeInvokeHook | None = None,
):
    """Create a parent node that loads, invokes, and persists a subgraph."""

    def subgraph_node(state: ParentState) -> ParentState:
        refs = dict(state.get("store_refs", {}))
        state_ref = refs.get(state_ref_key)

        if state_ref:
            saved_state = store.get(namespace=state_namespace, key="latest")
        else:
            saved_state = dict(initial_state)

        if before_invoke is not None:
            hook_result = before_invoke(store, saved_state, state, refs)
            if hook_result is not None:
                return hook_result

        subgraph_state = {
            **saved_state,
            "user_input": state.get("user_input", ""),
            "human_input": state.get("user_input", ""),
        }

        result = graph.invoke(subgraph_state)

        refs[state_ref_key] = store.put(
            namespace=state_namespace,
            key="latest",
            value=remove_runtime_routing(result),
        )

        return {
            "current_subgraph": subgraph,
            "store_refs": refs,
            "response": result.get("response", ""),
            "next_node": ParentNode.RESPONSE,
        }

    return subgraph_node


def make_battle_wrapper(
    store: StorePort,
    llm: LLMPort,
    resolve_battle_tool: ToolInvoker,
    resolve_battle_action: Callable[..., BattleResult],
    random: RandomPort,
):
    """Create the parent node that invokes and persists the battle subgraph."""
    battle_graph = build_battle_subgraph(
        store,
        llm,
        resolve_battle_tool,
        resolve_battle_action,
        random,
    )

    return make_subgraph_wrapper(
        store=store,
        graph=battle_graph,
        subgraph=SubgraphName.BATTLE,
        state_ref_key="battle_state",
        state_namespace=("battle", "state"),
        initial_state={
            "phase": BattlePhase.PREPARE,
            "latest_refs": {},
            "history_refs": {},
        },
    )


def make_craft_wrapper(
    store: StorePort,
    llm: LLMPort,
    craft_item_tool: ToolInvoker,
    craft_item: Callable[..., CraftResult],
    random: RandomPort,
):
    """Create the parent node that invokes and persists the craft subgraph."""
    craft_graph = build_craft_subgraph(
        store,
        llm,
        craft_item_tool,
        craft_item,
        random,
    )

    def answer_followup(
        store: StorePort,
        saved_state: RuntimePayload,
        state: ParentState,
        refs: StoreRefs,
    ) -> ParentState | None:
        followup_response = answer_craft_result_question(
            phase=saved_state.get("phase", CraftPhase.SELECT_RECIPE),
            latest_result=load_latest_craft_result(store, saved_state),
            user_input=state.get("user_input", ""),
        )
        if followup_response is not None:
            return {
                "current_subgraph": SubgraphName.CRAFT,
                "store_refs": refs,
                "response": followup_response,
                "next_node": ParentNode.RESPONSE,
            }

        return None

    return make_subgraph_wrapper(
        store=store,
        graph=craft_graph,
        subgraph=SubgraphName.CRAFT,
        state_ref_key="craft_state",
        state_namespace=("craft", "state"),
        initial_state={
            "phase": CraftPhase.SELECT_RECIPE,
            "latest_refs": {},
            "history_refs": {},
        },
        before_invoke=answer_followup,
    )


def make_exploration_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the exploration subgraph."""
    exploration_graph = build_exploration_subgraph()

    return make_subgraph_wrapper(
        store=store,
        graph=exploration_graph,
        subgraph=SubgraphName.EXPLORATION,
        state_ref_key="exploration_state",
        state_namespace=("exploration", "state"),
        initial_state={
            "phase": ExplorationPhase.START,
            "latest_refs": {},
            "history_refs": {},
        },
    )


def make_trade_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the trade subgraph."""
    trade_graph = build_trade_subgraph()

    return make_subgraph_wrapper(
        store=store,
        graph=trade_graph,
        subgraph=SubgraphName.TRADE,
        state_ref_key="trade_state",
        state_namespace=("trade", "state"),
        initial_state={
            "phase": TradePhase.BROWSE,
            "latest_refs": {},
            "history_refs": {},
        },
    )


def make_quest_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the quest subgraph."""
    quest_graph = build_quest_subgraph()

    return make_subgraph_wrapper(
        store=store,
        graph=quest_graph,
        subgraph=SubgraphName.QUEST,
        state_ref_key="quest_state",
        state_namespace=("quest", "state"),
        initial_state={
            "phase": QuestPhase.AVAILABLE,
            "latest_refs": {},
            "history_refs": {},
        },
    )


def make_dialogue_wrapper(store: StorePort):
    """Create the parent node that invokes and persists the dialogue subgraph."""
    dialogue_graph = build_dialogue_subgraph()

    return make_subgraph_wrapper(
        store=store,
        graph=dialogue_graph,
        subgraph=SubgraphName.DIALOGUE,
        state_ref_key="dialogue_state",
        state_namespace=("dialogue", "state"),
        initial_state={
            "phase": DialoguePhase.GREETING,
            "latest_refs": {},
            "history_refs": {},
        },
    )
