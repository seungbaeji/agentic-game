from __future__ import annotations

from agentic_game.domain.battle import BattleEvent, BattlePhase
from agentic_game.domain.craft import CraftEvent, CraftPhase
from agentic_game.flow.battle import resolve_battle_transition, serialize_battle_actions
from agentic_game.flow.craft import resolve_craft_transition, serialize_craft_actions


def test_battle_flow_exposes_only_current_phase_actions() -> None:
    actions = serialize_battle_actions(BattlePhase.ACTION)

    assert {action["event"] for action in actions} == {
        BattleEvent.ATTACK.value,
        BattleEvent.DEFEND.value,
        BattleEvent.FLEE.value,
    }


def test_battle_flow_resolves_allowed_transition() -> None:
    rule = resolve_battle_transition(BattlePhase.ACTION, BattleEvent.ATTACK)

    assert rule is not None
    assert rule.to_phase == BattlePhase.RESOLVE


def test_battle_flow_rejects_unavailable_transition() -> None:
    assert resolve_battle_transition(BattlePhase.PREPARE, BattleEvent.RETRY) is None


def test_battle_flow_allows_direct_action_from_prepare() -> None:
    rule = resolve_battle_transition(BattlePhase.PREPARE, BattleEvent.ATTACK)

    assert rule is not None
    assert rule.to_phase == BattlePhase.RESOLVE


def test_craft_flow_exposes_only_current_phase_actions() -> None:
    actions = serialize_craft_actions(CraftPhase.CRAFT)

    assert {action["event"] for action in actions} == {
        CraftEvent.CRAFT_POTION.value,
        CraftEvent.CRAFT_SWORD.value,
    }


def test_craft_flow_resolves_allowed_transition() -> None:
    rule = resolve_craft_transition(CraftPhase.CRAFT, CraftEvent.CRAFT_POTION)

    assert rule is not None
    assert rule.to_phase == CraftPhase.RESULT


def test_craft_flow_rejects_unavailable_transition() -> None:
    assert resolve_craft_transition(CraftPhase.SELECT_RECIPE, CraftEvent.RETRY) is None


def test_craft_flow_allows_direct_recipe_from_select_recipe() -> None:
    rule = resolve_craft_transition(CraftPhase.SELECT_RECIPE, CraftEvent.CRAFT_POTION)

    assert rule is not None
    assert rule.to_phase == CraftPhase.RESULT
