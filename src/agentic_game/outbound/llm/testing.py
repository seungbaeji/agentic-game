from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

T = TypeVar("T")


class TestingLLMAdapter:
    def __init__(
        self,
        *,
        structured_outputs: Mapping[type[Any], Sequence[Any]] | None = None,
        responses: Sequence[str] | None = None,
    ) -> None:
        """Create a deterministic LLM adapter for tests."""
        self._structured_outputs = {
            schema: deque(values)
            for schema, values in (structured_outputs or {}).items()
        }
        self._responses = deque(responses or ())

    def structured_output(self, schema: type[T], prompt: str) -> T:
        """Return the next registered structured output for the schema."""
        values = self._structured_outputs.get(schema)
        if not values:
            raise RuntimeError(f"No testing structured output registered for {schema.__name__}.")

        value = values.popleft()
        if isinstance(value, schema):
            return value

        model_validate = getattr(schema, "model_validate", None)
        if model_validate is not None:
            return model_validate(value)

        return schema(value)

    def respond(self, prompt: str) -> str:
        """Return the next registered plain text response."""
        if not self._responses:
            return ""
        return self._responses.popleft()
