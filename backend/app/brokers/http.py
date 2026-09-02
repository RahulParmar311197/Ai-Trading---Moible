from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

from .session import BrokerSession


class BrokerHTTPError(RuntimeError):
    """Provider HTTP/API failure with a safe, non-secret message."""


class LiveBrokerDisabled(RuntimeError):
    """Raised when an adapter is asked to submit/cancel a live order while gated."""


class HTTPBrokerClient:
    """Small provider-neutral HTTP transport for broker adapters."""

    def __init__(
        self,
        base_url: str,
        access_token: str = "",
        *,
        session: BrokerSession | None = None,
        timeout: float = 10.0,
    ) -> None:
        if session is not None and access_token:
            raise ValueError("provide either access_token or session, not both")
        self.base_url = base_url.rstrip("/")
        self._access_token = access_token
        self._session = session
        self.timeout = timeout

    @property
    def authenticated(self) -> bool:
        if self._session is not None:
            return self._session.authentication().authenticated
        return bool(self._access_token.strip())

    def _token(self) -> str:
        if self._session is not None:
            return self._session.access_token()
        if not self._access_token.strip():
            raise BrokerHTTPError("broker credentials are not configured")
        return self._access_token

    async def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("Accept", "application/json")
        try:
            headers["Authorization"] = f"Bearer {self._token()}"
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise BrokerHTTPError(f"broker transport failure: {type(exc).__name__}") from exc
        except RuntimeError as exc:
            # Session/transport implementations are allowed to raise RuntimeError,
            # but their messages may contain provider-specific or secret material.
            raise BrokerHTTPError(f"broker session/transport failure: {type(exc).__name__}") from exc
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
