from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Protocol

from .base import BrokerAuthentication


class BrokerSessionState(StrEnum):
    UNAUTHENTICATED = "UNAUTHENTICATED"
    AUTHENTICATED = "AUTHENTICATED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class BrokerSession(Protocol):
    """Secret-free lifecycle boundary for provider authentication sessions."""

    @property
    def state(self) -> BrokerSessionState: ...

    def authentication(self) -> BrokerAuthentication: ...

    def access_token(self) -> str: ...

    def invalidate(self) -> None: ...


class StaticTokenBrokerSession:
    """Own a broker access token without exposing it through domain models/logs.

    The application supplies the token from configuration/secret storage. The
    session exposes only a non-secret authentication projection; transport
    code can retrieve the token through the private lifecycle boundary.
    """

    def __init__(
        self,
        provider: str,
        account_id: str,
        access_token: str,
        *,
        expires_at: datetime | None = None,
    ) -> None:
        if not provider.strip() or not account_id.strip():
            raise ValueError("provider and account_id must be non-empty")
        self._provider = provider.strip()
        self._account_id = account_id.strip()
        self._access_token = access_token
        self._expires_at = expires_at
        self._invalidated = False

    @property
    def state(self) -> BrokerSessionState:
        if self._invalidated:
            return BrokerSessionState.INVALIDATED
        if not self._access_token.strip():
            return BrokerSessionState.UNAUTHENTICATED
        if self._expires_at is not None and self._expires_at <= datetime.now(timezone.utc):
            return BrokerSessionState.EXPIRED
        return BrokerSessionState.AUTHENTICATED

    def authentication(self) -> BrokerAuthentication:
        return BrokerAuthentication(
            provider=self._provider,
            account_id=self._account_id,
            authenticated=self.state is BrokerSessionState.AUTHENTICATED,
        )

    def access_token(self) -> str:
        if self.state is not BrokerSessionState.AUTHENTICATED:
            raise RuntimeError(f"broker session is {self.state.value.lower()}")
        return self._access_token

    def invalidate(self) -> None:
        self._invalidated = True
        self._access_token = ""

    def replace_token(self, access_token: str, *, expires_at: datetime | None = None) -> None:
        """Install a new secret after an external OAuth/token refresh flow."""
        self._access_token = access_token
        self._expires_at = expires_at
        self._invalidated = False
