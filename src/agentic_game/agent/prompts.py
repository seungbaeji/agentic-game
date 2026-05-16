from __future__ import annotations

from agentic_game.agent.state import BattleState, CraftState
from agentic_game.agent.types import (
    AvailableSubgraphs,
    PromptText,
    ResponseText,
    StoreRefs,
    UserInput,
)
from agentic_game.domain.battle import BattlePhase
from agentic_game.domain.craft import CraftPhase
from agentic_game.flow.models import AvailableActions


def build_parent_decision_prompt(
    *,
    available_subgraphs: AvailableSubgraphs,
    user_input: UserInput,
) -> PromptText:
    """Build the prompt that selects the parent target subgraph."""
    return f"""
Available subgraphs:
{available_subgraphs}

User input:
{user_input}

Choose one target_subgraph from available subgraphs.
If user mentions fighting, monster, attack, choose battle.
If user mentions crafting, item, potion, sword, choose craft.
"""


def build_parent_response_prompt(
    *,
    subgraph_response: ResponseText,
    store_refs: StoreRefs | None,
) -> PromptText:
    """Build the prompt that creates a parent-level final response."""
    return f"""
Subgraph result:
{subgraph_response}

Store refs:
{store_refs}

Write a concise final response.
Preserve the concrete subgraph result instead of replacing it with a generic status.
"""


def build_battle_decision_prompt(
    *,
    phase: BattlePhase,
    available_actions: AvailableActions,
    user_text: UserInput,
) -> PromptText:
    """Build the prompt that selects the next battle event."""
    return f"""
Current battle phase:
{phase}

Available actions:
{available_actions}

User input:
{user_text}

Choose event only from available actions.
Prefer the most specific user action.
If the user explicitly mentions attacking or 공격, choose attack instead of continue.
If the user explicitly mentions defending or 방어, choose defend instead of continue.
If the user explicitly mentions fleeing, 도망, or 회피, choose flee instead of continue.
"""


def build_battle_response_prompt(state: BattleState) -> PromptText:
    """Build the prompt that creates a battle response from graph state."""
    return f"""
Battle phase: {state.get("phase")}
Reason: {state.get("reason")}
Available actions: {state.get("available_actions")}
Latest refs: {state.get("latest_refs")}
History refs: {state.get("history_refs")}
Existing response: {state.get("response")}

Write a concise game response.
If Existing response has a concrete result, include that result.
"""


def build_craft_decision_prompt(
    *,
    phase: CraftPhase,
    available_actions: AvailableActions,
    user_text: UserInput,
) -> PromptText:
    """Build the prompt that selects the next craft event."""
    return f"""
Current craft phase:
{phase}

Available actions:
{available_actions}

User input:
{user_text}

Choose event only from available actions.
Prefer the most specific user action.
If the user explicitly mentions potion, 포션, or 회복 물약, choose craft_potion instead of continue.
If the user explicitly mentions sword, 검, or 칼, choose craft_sword instead of continue.
"""


def build_craft_response_prompt(state: CraftState) -> PromptText:
    """Build the prompt that creates a craft response from graph state."""
    return f"""
Craft phase: {state.get("phase")}
Reason: {state.get("reason")}
Available actions: {state.get("available_actions")}
Latest refs: {state.get("latest_refs")}
History refs: {state.get("history_refs")}
Existing response: {state.get("response")}

Write a concise game response.
If Existing response has a concrete result, include that result.
"""
