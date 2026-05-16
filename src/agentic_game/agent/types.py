from __future__ import annotations

from typing import Any, TypedDict

type UserInput = str
type HumanInput = str
type PromptText = str
type ResponseText = str
type ReasonText = str

type StoreRef = str
type StoreRefs = dict[str, StoreRef]
type HistoryRefs = dict[str, list[StoreRef]]

type RuntimePayload = dict[str, Any]
type RuntimeState = dict[str, Any]
type ToolInput = dict[str, Any]


class PhasePayloadRefs(TypedDict):
    latest_refs: StoreRefs
    history_refs: HistoryRefs


class SubgraphSpec(TypedDict):
    name: str
    label: str
    description: str


type AvailableSubgraphs = list[SubgraphSpec]
