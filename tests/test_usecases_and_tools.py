from __future__ import annotations

from agentic_game.application.usecases import craft_item, resolve_battle_action
from agentic_game.domain.battle import BattleOutcome
from agentic_game.tools import craft_item_tool, resolve_battle_tool
from agentic_game.tools.types import ToolResult
from tests.fakes import FixedRandom


def test_resolve_battle_action_uses_random_port() -> None:
    result = resolve_battle_action("attack", random=FixedRandom(d20=[18], damage=[11]))

    assert result.outcome == BattleOutcome.CRITICAL_HIT
    assert result.damage == 11


def test_craft_item_uses_random_port() -> None:
    result = craft_item("potion", random=FixedRandom(d20=[19]))

    assert result.success is True
    assert result.bonus is True


def test_tool_schema_hides_injected_dependencies() -> None:
    assert resolve_battle_tool.args == {"action": {"title": "Action", "type": "string"}}
    assert craft_item_tool.args == {"recipe": {"title": "Recipe", "type": "string"}}


def test_resolve_battle_tool_returns_internal_dataclass() -> None:
    result = resolve_battle_tool.invoke(
        {
            "action": "attack",
            "resolve_battle_action": resolve_battle_action,
            "random": FixedRandom(d20=[12], damage=[8]),
        }
    )

    assert isinstance(result, ToolResult)
    assert result.raw["outcome"] == BattleOutcome.HIT.value
    assert result.raw["damage"] == 8
    assert result.metadata["system_event"] == "tool.battle.resolve.completed"


def test_craft_item_tool_returns_internal_dataclass() -> None:
    result = craft_item_tool.invoke(
        {
            "recipe": "potion",
            "craft_item": craft_item,
            "random": FixedRandom(d20=[6]),
        }
    )

    assert isinstance(result, ToolResult)
    assert result.raw["success"] is False
    assert result.raw["item_name"] == "healing_potion"
    assert result.metadata["system_event"] == "tool.craft.completed"
