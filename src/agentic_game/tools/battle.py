from __future__ import annotations

from typing import Annotated, Any

from langchain_core.tools import InjectedToolArg, tool

from agentic_game.tools.projections import battle_result_to_tool_result
from agentic_game.tools.types import ToolResult


@tool
def resolve_battle_tool(
    action: str,
    resolve_battle_action: Annotated[Any, InjectedToolArg],
    random: Annotated[Any, InjectedToolArg],
    game_state: Annotated[Any, InjectedToolArg],
) -> ToolResult:
    """Resolve a battle action. Input action must be attack, defend, or flee."""
    result = resolve_battle_action(action, random=random, game_state=game_state)
    return battle_result_to_tool_result(result)
