from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from agentic_game.domain.battle import BattleEvent
from agentic_game.domain.craft import CraftCategory, CraftEvent
from agentic_game.domain.dialogue import DialogueEvent
from agentic_game.flow.models import SubgraphName


class ParentDecision(BaseModel):
    target_subgraph: SubgraphName | None = Field(
        description="Target subgraph selected from available subgraphs."
    )
    reason: str


class BattleDecision(BaseModel):
    event: BattleEvent
    reason: str


class CraftPlan(BaseModel):
    category: CraftCategory
    item_name: str = Field(
        description="Stable snake_case item id, for example flame_dagger."
    )
    display_name: str = Field(description="User-facing item name.")
    requested_effect: str | None = Field(
        default=None,
        description="Short effect or fantasy intent requested by the user.",
    )


class CraftDecision(BaseModel):
    intent: Literal["action", "question", "clarify"] = Field(
        description="Use action only when the user is choosing or describing an item to craft."
    )
    event: CraftEvent | None = None
    craft_plan: CraftPlan | None = None
    response: str | None = None
    reason: str


class DialogueDecision(BaseModel):
    intent: Literal["action", "question", "clarify", "smalltalk"] = Field(
        description=(
            "How the current dialogue input should be handled. Use action only "
            "when the user is choosing an available workflow event."
        )
    )
    event: DialogueEvent | None = Field(
        default=None,
        description="Selected dialogue event when intent is action.",
    )
    response: str | None = Field(
        default=None,
        description="Direct response when intent is question, clarify, or smalltalk.",
    )
    reason: str
