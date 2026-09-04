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
        auth_header: str = "Authorization",
        auth_scheme: str = "Bearer",
    ) -> None:
        if session is not None and access_token:
            raise ValueError("provide either access_token or session, not both")
        if not auth_header.strip():
            raise ValueError("auth_header must be non-empty")
        self.base_url = base_url.rstrip("/")
        self._access_token = access_token
        self._session = session
        self.timeout = timeout
        self._auth_header = auth_header
        self._auth_scheme = auth_scheme

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

    def _authorization_value(self, token: str) -> str:
        return f"{self._auth_scheme} {token}" if self._auth_scheme else token

    @staticmethod
    def _safe_provider_error(response: httpx.Response) -> str | None:
        """Extract only bounded, non-secret provider error fields."""
        try:
            payload = response.json()
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None

        # DhanHQ documents errorCode/errorMessage for v2. Keep support for
        # the provider's legacy internalErrorCode/internalErrorMessage shape
        # as well, without ever exposing an unbounded raw response body.
        code = payload.get("errorCode") or payload.get("internalErrorCode")
        message = payload.get("errorMessage") or payload.get("internalErrorMessage")
        error_type = payload.get("errorType")
        if not code and not message and not error_type:
            return None

        safe_code = str(code).strip()[:32] if code else ""
        safe_message = str(message).strip()[:160] if message else ""
        safe_type = str(error_type).strip()[:64] if error_type else ""
        if safe_code and safe_message:
            return f"{safe_code}: {safe_message}"
        if safe_code:
            return safe_code
        if safe_message:
            return safe_message
        return safe_type or None

    async def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("Accept", "application/json")
        try:
            headers[self._auth_header] = self._authorization_value(self._token())
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise BrokerHTTPError(f"broker transport failure: {type(exc).__name__}") from exc
        except RuntimeError as exc:
            # Session/transport implementations are allowed to raise RuntimeError,
            # but their messages may contain provider-specific or secret material.
            raise BrokerHTTPError(f"broker session/transport failure: {type(exc).__name__}") from exc
        if response.is_error:
            provider_error = self._safe_provider_error(response)
            if provider_error:
                raise BrokerHTTPError(f"broker API returned HTTP {response.status_code} ({provider_error})")
            raise BrokerHTTPError(f"broker API returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise BrokerHTTPError("broker API returned invalid JSON") from exc


def decimal_value(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))
