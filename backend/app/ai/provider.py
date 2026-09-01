"""Provider-neutral AI transport boundary.

The adapter sends structured prompts to a configured JSON LLM endpoint. It never
receives or sends broker credentials and never executes trading actions.
"""

import json
from collections.abc import Mapping
from typing import Any, Protocol

import httpx


class AIProvider(Protocol):
    def complete(self, *, system: str, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


class AIProviderError(RuntimeError):
    """Raised when the configured AI provider cannot produce a response."""


class HttpAIProvider:
    """Minimal provider-neutral JSON adapter with explicit timeout and auth."""

    def __init__(self, endpoint: str, api_key: str = "", model: str = "", timeout: float = 20.0) -> None:
        if not endpoint:
            raise ValueError("AI provider endpoint is required")
        if timeout <= 0:
            raise ValueError("AI provider timeout must be positive")
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, *, system: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = {"model": self.model, "system": system, "input": dict(payload)}
        try:
            response = httpx.post(self.endpoint, json=body, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AIProviderError("AI provider request failed") from exc
        return self._extract_mapping(data)

    @staticmethod
    def _extract_mapping(data: Any) -> Mapping[str, Any]:
        if isinstance(data, Mapping):
            if isinstance(data.get("output"), Mapping):
                return data["output"]
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                message = choices[0].get("message") if isinstance(choices[0], Mapping) else None
                content = message.get("content") if isinstance(message, Mapping) else None
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                    except json.JSONDecodeError as exc:
                        raise AIProviderError("AI provider returned non-JSON content") from exc
                    if isinstance(parsed, Mapping):
                        return parsed
            return data
        raise AIProviderError("AI provider returned an invalid JSON object")
