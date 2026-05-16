from __future__ import annotations

from typing import TypedDict

from agentic_game.agent.models import (
    BattleNode,
    CraftNode,
    ParentNode,
    SubgraphName,
)
from agentic_game.agent.types import (
    HistoryRefs,
    HumanInput,
    ReasonText,
    ResponseText,
    StoreRefs,
    UserInput,
)
from agentic_game.domain.battle import (
    BattleEvent,
    BattlePhase,
)
from agentic_game.domain.craft import (
    CraftEvent,
    CraftPhase,
)
from agentic_game.domain.exploration import (
    ExplorationEvent,
    ExplorationPhase,
)
from agentic_game.domain.quest import (
    QuestEvent,
    QuestPhase,
)
from agentic_game.domain.trade import (
    TradeEvent,
    TradePhase,
)
from agentic_game.flow.models import AvailableActions


class ParentState(TypedDict, total=False):
    user_input: UserInput
    target_subgraph: SubgraphName
    current_subgraph: SubgraphName
    store_refs: StoreRefs
    response: ResponseText
    reason: ReasonText
    next_node: ParentNode


class BattleState(TypedDict, total=False):
    user_input: UserInput
    human_input: HumanInput

    phase: BattlePhase
    event: BattleEvent

    latest_refs: StoreRefs
    history_refs: HistoryRefs

    available_actions: AvailableActions
    response: ResponseText
    reason: ReasonText
    next_node: BattleNode


class CraftState(TypedDict, total=False):
    user_input: UserInput
    human_input: HumanInput

    phase: CraftPhase
    event: CraftEvent

    latest_refs: StoreRefs
    history_refs: HistoryRefs

    available_actions: AvailableActions
    response: ResponseText
    reason: ReasonText
    next_node: CraftNode


class ExplorationState(TypedDict, total=False):
    user_input: UserInput
    human_input: HumanInput

    phase: ExplorationPhase
    event: ExplorationEvent

    latest_refs: StoreRefs
    history_refs: HistoryRefs

    available_actions: AvailableActions
    response: ResponseText
    reason: ReasonText
    next_node: str


class TradeState(TypedDict, total=False):
    user_input: UserInput
    human_input: HumanInput

    phase: TradePhase
    event: TradeEvent

    latest_refs: StoreRefs
    history_refs: HistoryRefs

    available_actions: AvailableActions
    response: ResponseText
    reason: ReasonText
    next_node: str


class QuestState(TypedDict, total=False):
    user_input: UserInput
    human_input: HumanInput

    phase: QuestPhase
    event: QuestEvent

    latest_refs: StoreRefs
    history_refs: HistoryRefs

    available_actions: AvailableActions
    response: ResponseText
    reason: ReasonText
    next_node: str
