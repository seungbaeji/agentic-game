from __future__ import annotations

from pydantic import BaseModel, Field

from agentic_game.domain.battle import BattleEvent
from agentic_game.domain.craft import CraftEvent
from agentic_game.flow.models import SubgraphName


class ParentDecision(BaseModel):
    target_subgraph: SubgraphName | None = Field(
        description="Target subgraph selected from available subgraphs."
    )
    reason: str


class BattleDecision(BaseModel):
    event: BattleEvent
    reason: str


class CraftDecision(BaseModel):
    event: CraftEvent
    reason: str
