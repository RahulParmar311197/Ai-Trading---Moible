"""Safe AI-to-Strategy-DSL translation boundary.

An eventual LLM provider may return structured JSON, but this boundary accepts
only declarative data and validates it with the existing Pydantic strategy
contracts. Executable code and broker instructions are rejected outright.
"""

import json
from typing import Any, Mapping

from pydantic import ValidationError

from app.strategy.dsl import StrategyDefinition


_FORBIDDEN_KEYS = frozenset(
    {
        "code",
        "python",
        "script",
        "command",
        "exec",
        "execute",
        "broker_order",
        "place_order",
        "submit_order",
    }
)


class StrategyDslTranslationError(ValueError):
    """Raised when AI output cannot be safely translated into the DSL."""


class StrategyDslTranslator:
    """Validate AI-produced declarative strategy data without executing it."""

    def translate(self, payload: Mapping[str, Any] | str) -> StrategyDefinition:
        data = self._decode(payload)
        self._reject_executable_keys(data)
        try:
            return StrategyDefinition.model_validate(data)
        except ValidationError as exc:
            raise StrategyDslTranslationError("AI strategy output failed DSL validation") from exc

    @staticmethod
    def _decode(payload: Mapping[str, Any] | str) -> dict[str, Any]:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise StrategyDslTranslationError("AI strategy output is not valid JSON") from exc
        if not isinstance(payload, Mapping):
            raise StrategyDslTranslationError("AI strategy output must be a JSON object")
        return dict(payload)

    def _reject_executable_keys(self, value: Any, path: str = "strategy") -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if str(key).lower() in _FORBIDDEN_KEYS:
                    raise StrategyDslTranslationError(f"executable field rejected at {path}.{key}")
                self._reject_executable_keys(child, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                self._reject_executable_keys(child, f"{path}[{index}]")
