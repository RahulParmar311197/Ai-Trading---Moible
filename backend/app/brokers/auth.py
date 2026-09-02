from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from .session import StaticTokenBrokerSession


class BrokerAuthError(RuntimeError):
    """Safe authentication/refresh failure without credential contents."""


@dataclass(frozen=True)
class BrokerToken:
    """Secret-bearing token result kept outside broker domain DTOs."""

    access_token: str
    expires_at: datetime | None = None

    def session(self, provider: str, account_id: str) -> StaticTokenBrokerSession:
        """Convert an acquired token directly into the secret-safe session boundary."""
        return StaticTokenBrokerSession(provider, account_id, self.access_token, expires_at=self.expires_at)


class UpstoxOAuth:
    """Upstox OAuth authorization-code exchange."""

    token_url = "https://api.upstox.com/v2/login/authorization/token"

    def __init__(self, *, timeout: float = 10.0, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.timeout = timeout
        self.transport = transport

    async def exchange_code(self, *, code: str, client_id: str, client_secret: str, redirect_uri: str) -> BrokerToken:
        for value, label in ((code, "authorization code"), (client_id, "client id"), (client_secret, "client secret"), (redirect_uri, "redirect uri")):
            self._require(value, label)
        payload = await self._post(self.token_url, data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        return BrokerToken(self._token_from(payload, "access_token"), self._next_upstox_expiry())

    async def _post(self, url: str, *, data: dict[str, str]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                response = await client.post(url, data=data, headers={"Accept": "application/json"})
        except httpx.HTTPError as exc:
            raise BrokerAuthError(f"broker authentication transport failure: {type(exc).__name__}") from exc
        if response.is_error:
            raise BrokerAuthError(f"broker authentication returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise BrokerAuthError("broker authentication returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise BrokerAuthError("broker authentication returned an invalid response")
        return payload

    @staticmethod
    def _token_from(payload: dict[str, Any], field: str) -> str:
        token = payload.get(field)
        if not isinstance(token, str) or not token.strip():
            raise BrokerAuthError("broker authentication response did not contain an access token")
        return token

    @staticmethod
    def _require(value: str, label: str) -> None:
        if not value.strip():
            raise ValueError(f"{label} must be non-empty")

    @staticmethod
    def _next_upstox_expiry() -> datetime:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        expiry = now.replace(hour=3, minute=30, second=0, microsecond=0)
        if expiry <= now:
            expiry += timedelta(days=1)
        return expiry.astimezone(timezone.utc)


class DhanOAuth:
    """Dhan consent/token exchange and supported token renewal boundary."""

    consent_url = "https://auth.dhan.co/app/generate-consent"
    consume_url = "https://auth.dhan.co/app/consumeApp-consent"
    renew_url = "https://api.dhan.co/v2/RenewToken"

    def __init__(self, *, timeout: float = 10.0, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.timeout = timeout
        self.transport = transport

    async def generate_consent(self, *, client_id: str, api_key: str, api_secret: str) -> str:
        for value, label in ((client_id, "client id"), (api_key, "api key"), (api_secret, "api secret")):
            self._require(value, label)
        payload = await self._request("POST", self.consent_url, params={"client_id": client_id}, headers={"app_id": api_key, "app_secret": api_secret})
        redirect = payload.get("redirect_URL", payload.get("redirectUrl"))
        if not isinstance(redirect, str) or "tokenId=" not in redirect:
            raise BrokerAuthError("Dhan consent response did not contain a token id")
        return redirect.split("tokenId=", 1)[1].split("&", 1)[0]

    async def consume_consent(self, *, token_id: str, api_key: str, api_secret: str) -> BrokerToken:
        for value, label in ((token_id, "token id"), (api_key, "api key"), (api_secret, "api secret")):
            self._require(value, label)
        payload = await self._request("POST", self.consume_url, params={"tokenId": token_id}, headers={"app_id": api_key, "app_secret": api_secret})
        return BrokerToken(self._token_from(payload, "accessToken"), self._parse_expiry(payload.get("expiryTime")))

    async def renew(self, *, client_id: str, access_token: str) -> BrokerToken:
        for value, label in ((client_id, "client id"), (access_token, "access token")):
            self._require(value, label)
        payload = await self._request("POST", self.renew_url, headers={"access-token": access_token, "dhanClientId": client_id})
        return BrokerToken(self._token_from(payload, "accessToken"), self._parse_expiry(payload.get("expiryTime")))

    async def _request(self, method: str, url: str, *, params: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                response = await client.request(method, url, params=params, headers=headers or {})
        except httpx.HTTPError as exc:
            raise BrokerAuthError(f"broker authentication transport failure: {type(exc).__name__}") from exc
        if response.is_error:
            raise BrokerAuthError(f"broker authentication returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise BrokerAuthError("broker authentication returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise BrokerAuthError("broker authentication returned an invalid response")
        return payload

    @staticmethod
    def _token_from(payload: dict[str, Any], field: str) -> str:
        token = payload.get(field)
        if not isinstance(token, str) or not token.strip():
            raise BrokerAuthError("broker authentication response did not contain an access token")
        return token

    @staticmethod
    def _parse_expiry(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _require(value: str, label: str) -> None:
        if not value.strip():
            raise ValueError(f"{label} must be non-empty")
