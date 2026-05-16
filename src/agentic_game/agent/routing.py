from __future__ import annotations

from agentic_game.agent.models import BattleNode, CraftNode
from agentic_game.domain.battle import BattlePhase
from agentic_game.domain.craft import CraftPhase


def battle_node_after_phase(phase: BattlePhase) -> BattleNode:
    """Return the next battle graph node for a resolved battle phase."""
    if phase == BattlePhase.ACTION:
        return BattleNode.HITL
    if phase == BattlePhase.RESOLVE:
        return BattleNode.EXECUTE
    return BattleNode.RESPONSE


def craft_node_after_phase(phase: CraftPhase) -> CraftNode:
    """Return the next craft graph node for a resolved craft phase."""
    if phase == CraftPhase.CRAFT:
        return CraftNode.HITL
    if phase == CraftPhase.RESULT:
        return CraftNode.EXECUTE
    return CraftNode.RESPONSE
