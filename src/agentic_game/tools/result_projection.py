from __future__ import annotations

from agentic_game.application.usecases.battle import BattleActionResult
from agentic_game.application.usecases.craft import CraftItemResult
from agentic_game.application.usecases.trade import TradeResult
from agentic_game.tools.types import ToolResult


def battle_result_to_tool_result(result: BattleActionResult) -> ToolResult:
    """Project a battle domain result into raw, LLM, UI, and metadata payloads."""
    raw = {
        "action": result.action,
        "dice": result.dice,
        "outcome": result.outcome.value,
        "damage": result.damage,
        "player_delta": (
            {
                "hp_change": result.player_delta.hp_change,
                "exp_gain": result.player_delta.exp_gain,
            }
            if result.player_delta is not None
            else None
        ),
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
        "category": result.category,
        "item_name": result.item_name,
        "display_name": result.display_name,
        "requested_effect": result.requested_effect,
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
            "summary": f"{result.display_name} 제작 {'성공' if result.success else '실패'}",
            "category": result.category,
            "item_name": result.item_name,
            "display_name": result.display_name,
            "requested_effect": result.requested_effect,
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


def trade_result_to_tool_result(result: TradeResult) -> ToolResult:
    """Project a trade usecase result into raw, LLM, UI, and metadata payloads."""
    raw = {
        "item_id": result.item_id,
        "price": result.price,
        "player_gold": result.player.gold,
        "inventory_items": [
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
            }
            for item in result.inventory.items
        ],
    }

    return ToolResult(
        raw=raw,
        llm={
            "summary": (
                f"거래가 성사되었습니다. {result.item_id}을 구매하고 "
                f"{result.price} gold를 지불했습니다."
            ),
            "item_id": result.item_id,
            "price": result.price,
        },
        ui={
            "type": "trade_result",
            **raw,
        },
        metadata={
            "system_event": "tool.trade.exchange.completed",
        },
    )
