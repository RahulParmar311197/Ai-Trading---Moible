from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx


class BrokerHTTPError(RuntimeError):
    """Provider HTTP/API failure with a safe, non-secret message."""


class LiveBrokerDisabled(RuntimeError):
    """Raised when an adapter is asked to submit/cancel a live order while gated."""


class HTTPBrokerClient:
    """Small provider-neutral HTTP transport for broker adapters."""

    def __init__(self, base_url: str, access_token: str, *, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._access_token = access_token
        self.timeout = timeout

    @property
    def authenticated(self) -> bool:
        return bool(self._access_token.strip())

    async def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        if not self.authenticated:
            raise BrokerHTTPError("broker credentials are not configured")
        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("Accept", "application/json")
        headers["Authorization"] = f"Bearer {self._access_token}"
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise BrokerHTTPError(f"broker transport failure: {type(exc).__name__}") from exc
        if response.is_error:
            raise BrokerHTTPError(f"broker API returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise BrokerHTTPError("broker API returned invalid JSON") from exc


def decimal_value(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))
