from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from agentic_game.agent.models import ParentNode, SubgraphName
from agentic_game.agent.state import ParentState
from agentic_game.agent.types import RuntimePayload, StoreRefs
from agentic_game.application.ports import StorePort


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


def make_subgraph_wrapper(
    *,
    store: StorePort,
    graph: InvokableGraph,
    subgraph: SubgraphName,
    state_ref_key: str,
    state_namespace: tuple[str, str],
    initial_state: RuntimePayload,
    terminal_phases: Sequence[object] = (),
    before_invoke: BeforeInvokeHook | None = None,
):
    """Create a parent node that loads, invokes, and persists a subgraph."""
    terminal_phase_set = set(terminal_phases)

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

        current_subgraph = None if result.get("phase") in terminal_phase_set else subgraph

        return {
            "current_subgraph": current_subgraph,
            "store_refs": refs,
            "response": result.get("response", ""),
            "next_node": ParentNode.RESPONSE,
        }

    return subgraph_node


def make_simple_subgraph_wrapper(
    *,
    store: StorePort,
    graph: InvokableGraph,
    subgraph: SubgraphName,
    initial_phase: object,
    terminal_phases: Sequence[object] = (),
):
    """Create a wrapper for a scenario with standard state persistence keys."""
    subgraph_name = subgraph.value
    return make_subgraph_wrapper(
        store=store,
        graph=graph,
        subgraph=subgraph,
        state_ref_key=f"{subgraph_name}_state",
        state_namespace=(subgraph_name, "state"),
        initial_state={
            "phase": initial_phase,
            "latest_refs": {},
            "history_refs": {},
        },
        terminal_phases=terminal_phases,
    )
