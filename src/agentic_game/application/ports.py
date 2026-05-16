from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, TypedDict, TypeVar

T = TypeVar("T")

type StoreNamespace = tuple[str, ...]
type StoreKey = str
type StoreRef = str
type StoreValue = Any
type PhaseName = str
type PayloadName = str


class PhasePayloadRefs(TypedDict):
    latest_refs: dict[str, StoreRef]
    history_refs: dict[str, list[StoreRef]]


class LLMPort(Protocol):
    def structured_output(self, schema: type[T], prompt: str) -> T:
        """Return an LLM response parsed into the requested schema."""
        ...

    def respond(self, prompt: str) -> str:
        """Return a plain text LLM response for the given prompt."""
        ...


class RandomPort(Protocol):
    def roll_d20(self) -> int:
        """Roll a twenty-sided die."""
        ...

    def roll_damage(self, low: int, high: int) -> int:
        """Roll damage within the inclusive low/high range."""
        ...


class StorePort(Protocol):
    def put(
        self,
        *,
        namespace: StoreNamespace,
        key: StoreKey,
        value: StoreValue,
    ) -> StoreRef:
        """Persist a value and return a stable store reference."""
        ...

    def get(
        self,
        *,
        namespace: StoreNamespace,
        key: StoreKey,
    ) -> StoreValue:
        """Load a value from the store by namespace and key."""
        ...

    def persist_phase_payload(
        self,
        *,
        state: Mapping[str, StoreValue],
        subgraph: str,
        phase: PhaseName,
        payload_name: PayloadName,
        value: StoreValue,
    ) -> PhasePayloadRefs:
        """Persist a phase payload and return updated latest/history references."""
        ...
