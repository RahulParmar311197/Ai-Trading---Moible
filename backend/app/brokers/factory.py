"""Construct authenticated broker adapters from user-owned account metadata."""

from __future__ import annotations

from uuid import UUID

from app.brokers.account_repository import BrokerAccount, BrokerAccountRepository
from app.brokers.base import Broker
from app.brokers.credential_provider import BrokerCredentials, CredentialProvider, CredentialUnavailable
from app.brokers.dhan.adapter import DhanBroker
from app.brokers.upstox.adapter import UpstoxBroker


class BrokerUnavailable(RuntimeError):
    """Raised when an account cannot be safely converted into a broker session."""


class BrokerAccountFactory:
    """Resolve one enabled account into a read-only-by-default broker adapter.

    The factory deliberately never enables broker mutations. In particular, a LIVE
    account is metadata, not authorization to submit real-money orders. Controlled
    execution must supply its own separately verified mutation gate.
    """

    def __init__(self, repository: BrokerAccountRepository, credentials: CredentialProvider) -> None:
        self.repository = repository
        self.credentials = credentials

    def build(self, *, user_id: UUID, account_id: UUID) -> Broker:
        account = self.repository.get_for_user(user_id, account_id)
        if account is None:
            raise BrokerUnavailable("broker account not found")
        if not account.enabled:
            raise BrokerUnavailable("broker account is disabled")
        credential_ref = (account.credential_ref or "").strip()
        if not credential_ref:
            raise CredentialUnavailable("broker account has no credential reference")

        resolved = self.credentials.resolve(
            user_id=user_id,
            account_id=account.id,
            credential_ref=credential_ref,
        )
        self._validate_credentials(account, resolved)
        return self._construct(account, resolved)

    @staticmethod
    def _validate_credentials(account: BrokerAccount, credentials: BrokerCredentials) -> None:
        if not isinstance(credentials, BrokerCredentials):
            raise CredentialUnavailable("broker credential provider returned invalid credentials")
        if not credentials.access_token or not credentials.access_token.strip():
            raise CredentialUnavailable("broker credential provider returned no access token")
        if account.provider == "DHAN" and (not credentials.client_id or not credentials.client_id.strip()):
            raise CredentialUnavailable("Dhan credential provider returned no client id")

    @staticmethod
    def _construct(account: BrokerAccount, credentials: BrokerCredentials) -> Broker:
        sandbox = account.environment == "SANDBOX"
        if account.provider == "UPSTOX":
            return UpstoxBroker(
                credentials.access_token,
                sandbox=sandbox,
                allow_live_orders=False,
                allow_sandbox_orders=False,
            )
        if account.provider == "DHAN":
            return DhanBroker(
                credentials.client_id or "",
                credentials.access_token,
                sandbox=sandbox,
                allow_live_orders=False,
                allow_sandbox_orders=False,
            )
        raise BrokerUnavailable("unsupported broker provider")
