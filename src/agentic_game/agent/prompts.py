from __future__ import annotations

from agentic_game.agent.state import BattleState, CraftState, DialogueState
from agentic_game.agent.types import (
    AvailableSubgraphs,
    PromptText,
    ResponseText,
    StoreRefs,
    UserInput,
)
from agentic_game.domain.battle import BattlePhase
from agentic_game.domain.craft import CraftPhase
from agentic_game.domain.dialogue import DialoguePhase
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
If user mentions exploring, forest, ruins, or 탐험, choose exploration.
If user mentions trading, shop, merchant, or 거래, choose trade.
If user mentions quest, mission, or 퀘스트, choose quest.
If user mentions dialogue, NPC, rumor, or 대화, choose dialogue.
If user mentions skill, training, or 훈련, choose skill_training.
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


def build_cli_startup_prompt(
    *,
    available_subgraphs: AvailableSubgraphs,
    exit_commands: tuple[str, ...],
) -> PromptText:
    """Build the prompt that creates the first CLI greeting."""
    return f"""
Available scenarios:
{available_subgraphs}

Exit commands:
{exit_commands}

Write a warm, concise Korean CLI startup message.
The message must ask the user what they want to do first.
Mention the available scenarios in user-facing language.
Mention the exit commands briefly.
Do not expose internal names like subgraph, graph, node, phase, or event.
Include 2-3 short example inputs.
"""


def build_capability_response_prompt(
    *,
    available_subgraphs: AvailableSubgraphs,
    user_input: UserInput,
) -> PromptText:
    """Build the prompt that explains what the agent can do."""
    return f"""
Available scenarios:
{available_subgraphs}

User input:
{user_input}

Answer in Korean.
Explain what the user can choose now.
End by asking what they want to do.
Do not expose internal names like subgraph, graph, node, phase, or event.
Keep the answer concise and practical.
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

Classify the user input for crafting.

Use intent=action when the user names or describes an item to craft.
When intent=action, choose event only from Available actions and provide craft_plan.
Map item details into one category:
- consumable: potion, food, scroll, bomb, temporary-use item
- weapon: sword, dagger, bow, staff, arrow, offensive gear
- armor: armor, shield, helmet, defensive gear
- accessory: ring, necklace, charm, trinket
- tool: key, pickaxe, fishing rod, utility tool
- material: ingot, leather, essence, refined ingredient

Use intent=clarify when the user only says they want to craft but gives no item detail.
Use intent=question when the user asks about crafting or the latest result.

Never invent an event outside Available actions.
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


def build_dialogue_decision_prompt(
    *,
    phase: DialoguePhase,
    available_actions: AvailableActions,
    user_text: UserInput,
    last_topic: str | None,
    last_response: ResponseText | None,
) -> PromptText:
    """Build the prompt that classifies a dialogue input."""
    return f"""
Current dialogue phase:
{phase}

Available actions:
{available_actions}

Last topic:
{last_topic}

Last response:
{last_response}

User input:
{user_text}

Classify the user input.

Use intent=action only when the user is choosing one of the available actions.
When intent=action, choose event only from Available actions.

Use intent=question when the user asks about the current NPC, the latest response,
or the latest topic. Answer without changing the workflow phase.

Use intent=clarify when the user input is unclear and you need a more specific choice.
Use intent=smalltalk for conversational input that should not change the workflow.

Never invent an event outside Available actions.
"""


def build_dialogue_response_prompt(state: DialogueState) -> PromptText:
    """Build the prompt that creates a dialogue response from graph state."""
    return f"""
Dialogue phase: {state.get("phase")}
Reason: {state.get("reason")}
Available actions: {state.get("available_actions")}
Last topic: {state.get("last_topic")}
Existing response: {state.get("response")}

Write a concise in-character NPC response.
Preserve concrete details from Existing response when present.
If the player can continue, naturally mention the next available choices.
"""
