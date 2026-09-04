"""Credential-resolution boundary for user-owned broker accounts.

This module deliberately does not read broker tokens from database rows. Deployments
must provide secrets through an external secret-management boundary keyed by the
opaque credential reference stored with the account metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class CredentialUnavailable(RuntimeError):
    """Raised when credentials cannot be safely resolved."""


@dataclass(frozen=True, slots=True)
class BrokerCredentials:
    access_token: str
    client_id: str | None = None


class CredentialProvider(Protocol):
    def resolve(self, *, user_id: UUID, account_id: UUID, credential_ref: str) -> BrokerCredentials: ...


class UnconfiguredCredentialProvider:
    """Fail-closed provider used until a deployment wires a real secret store."""

    def resolve(self, *, user_id: UUID, account_id: UUID, credential_ref: str) -> BrokerCredentials:
        raise CredentialUnavailable("broker credential provider is not configured")
