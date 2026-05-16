from __future__ import annotations

from agentic_game.agent.models import BattleNode, CraftNode
from agentic_game.agent.scenario import ScenarioNode, ScenarioSpec
from agentic_game.agent.scenarios import BATTLE_SCENARIO, CRAFT_SCENARIO
from agentic_game.domain.battle import BattlePhase
from agentic_game.domain.craft import CraftPhase

_BATTLE_NODE_BY_SCENARIO_NODE = {
    ScenarioNode.HITL: BattleNode.HITL,
    ScenarioNode.EXECUTE: BattleNode.EXECUTE,
    ScenarioNode.RESPONSE: BattleNode.RESPONSE,
    ScenarioNode.ASK_USER: BattleNode.ASK_USER,
}

_CRAFT_NODE_BY_SCENARIO_NODE = {
    ScenarioNode.HITL: CraftNode.HITL,
    ScenarioNode.EXECUTE: CraftNode.EXECUTE,
    ScenarioNode.RESPONSE: CraftNode.RESPONSE,
    ScenarioNode.ASK_USER: CraftNode.ASK_USER,
}


def scenario_node_after_phase[PhaseT, EventT](
    spec: ScenarioSpec[PhaseT, EventT],
    phase: PhaseT,
) -> ScenarioNode:
    """Return the generic runtime node for a resolved scenario phase."""
    return spec.phase_to_node.get(phase, ScenarioNode.RESPONSE)


def battle_node_for_scenario_node(node: ScenarioNode) -> BattleNode:
    """Map a generic scenario node role to the battle graph node."""
    return _BATTLE_NODE_BY_SCENARIO_NODE.get(node, BattleNode.RESPONSE)


def battle_node_after_phase(phase: BattlePhase) -> BattleNode:
    """Return the next battle graph node for a resolved battle phase."""
    scenario_node = scenario_node_after_phase(BATTLE_SCENARIO, phase)
    return battle_node_for_scenario_node(scenario_node)


def craft_node_for_scenario_node(node: ScenarioNode) -> CraftNode:
    """Map a generic scenario node role to the craft graph node."""
    return _CRAFT_NODE_BY_SCENARIO_NODE.get(node, CraftNode.RESPONSE)


def craft_node_after_phase(phase: CraftPhase) -> CraftNode:
    """Return the next craft graph node for a resolved craft phase."""
    scenario_node = scenario_node_after_phase(CRAFT_SCENARIO, phase)
    return craft_node_for_scenario_node(scenario_node)
