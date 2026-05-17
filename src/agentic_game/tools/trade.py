from __future__ import annotations

from typing import Annotated, Any

from langchain_core.tools import InjectedToolArg, tool

from agentic_game.tools.result_projection import trade_result_to_tool_result
from agentic_game.tools.types import ToolResult


@tool
def exchange_item_tool(
    item_id: str,
    price: int,
    exchange_item: Annotated[Any, InjectedToolArg],
    game_state: Annotated[Any, InjectedToolArg],
) -> ToolResult:
    """Exchange player gold for an item."""
    result = exchange_item(item_id=item_id, price=price, game_state=game_state)
    return trade_result_to_tool_result(result)
