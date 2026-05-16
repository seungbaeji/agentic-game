from __future__ import annotations

from collections.abc import Mapping

from langgraph.store.base import BaseStore

from agentic_game.application.ports import (
    PayloadName,
    PhaseName,
    PhasePayloadRefs,
    StoreKey,
    StoreNamespace,
    StoreRef,
    StoreValue,
)


class LangGraphStoreAdapter:
    def __init__(self, store: BaseStore) -> None:
        """Wrap a LangGraph store behind the application store port."""
        self._store = store

    def put(
        self,
        *,
        namespace: StoreNamespace,
        key: StoreKey,
        value: StoreValue,
    ) -> StoreRef:
        """Persist a value in LangGraph store and return a store URI."""
        self._store.put(namespace, key, value)
        return f"store://{'/'.join(namespace)}/{key}"

    def get(
        self,
        *,
        namespace: StoreNamespace,
        key: StoreKey,
    ) -> StoreValue:
        """Load a value from LangGraph store or raise when it is missing."""
        item = self._store.get(namespace, key)
        if item is None:
            raise KeyError(f"Store item not found: {namespace}/{key}")
        return item.value

    def persist_phase_payload(
        self,
        *,
        state: Mapping[str, StoreValue],
        subgraph: str,
        phase: PhaseName,
        payload_name: PayloadName,
        value: StoreValue,
    ) -> PhasePayloadRefs:
        """Persist a payload under latest and history references for a phase."""
        latest_refs = dict(state.get("latest_refs", {}))
        history_refs = dict(state.get("history_refs", {}))

        phase_key = f"{phase}.{payload_name}"
        history = list(history_refs.get(phase_key, []))
        version = len(history) + 1

        history_ref = self.put(
            namespace=(subgraph, phase, payload_name, "history"),
            key=str(version),
            value=value,
        )
        latest_ref = self.put(
            namespace=(subgraph, phase, payload_name),
            key="latest",
            value=value,
        )

        latest_refs[phase_key] = latest_ref
        history_refs[phase_key] = [*history, history_ref]

        return {
            "latest_refs": latest_refs,
            "history_refs": history_refs,
        }
