from __future__ import annotations

from agentic_game.application.usecases.craft import CraftItemResult
from agentic_game.domain.battle import BattleResult
from agentic_game.tools.types import ToolResult


def battle_result_to_tool_result(result: BattleResult) -> ToolResult:
    """Project a battle domain result into raw, LLM, UI, and metadata payloads."""
    raw = {
        "action": result.action,
        "dice": result.dice,
        "outcome": result.outcome.value,
        "damage": result.damage,
    }

    return ToolResult(
        raw=raw,
        llm={
            "summary": f"전투 행동 '{result.action}' 결과는 {result.outcome.value}입니다.",
            "outcome": result.outcome.value,
            "damage": result.damage,
        },
        ui={
            "type": "battle_result",
            **raw,
        },
        metadata={
            "system_event": "tool.battle.resolve.completed",
        },
    )


def craft_result_to_tool_result(result: CraftItemResult) -> ToolResult:
    """Project a craft domain result into raw, LLM, UI, and metadata payloads."""
    raw = {
        "recipe": result.recipe,
        "item_name": result.item_name,
        "dice": result.dice,
        "success": result.success,
        "bonus": result.bonus,
        "inventory_delta": (
            {
                "item_id": result.inventory_delta.item_id,
                "quantity": result.inventory_delta.quantity,
            }
            if result.inventory_delta is not None
            else None
        ),
    }

    return ToolResult(
        raw=raw,
        llm={
            "summary": f"{result.recipe} 제작 {'성공' if result.success else '실패'}",
            "item_name": result.item_name,
            "success": result.success,
            "bonus": result.bonus,
        },
        ui={
            "type": "craft_result",
            **raw,
        },
        metadata={
            "system_event": "tool.craft.completed",
        },
    )
