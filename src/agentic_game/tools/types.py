from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolResult:
    raw: dict[str, Any]
    llm: dict[str, Any]
    ui: dict[str, Any]
    metadata: dict[str, Any]
