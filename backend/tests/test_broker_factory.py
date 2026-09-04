from uuid import uuid4

import pytest

from app.brokers.account_repository import BrokerAccount
from app.brokers.credential_provider import BrokerCredentials, CredentialUnavailable
from app.brokers.dhan.adapter import DhanBroker
from app.brokers.factory import BrokerAccountFactory, BrokerUnavailable
from app.brokers.upstox.adapter import UpstoxBroker


class FakeRepository:
    def __init__(self, account):
        self.account = account

    def get_for_user(self, user_id, account_id):
        if self.account and self.account.user_id == user_id and self.account.id == account_id:
            return self.account
        return None


class FakeCredentials:
    def __init__(self, credentials=None, error=None):
        self.credentials = credentials
        self.error = error
        self.calls = []

    def resolve(self, *, user_id, account_id, credential_ref):
        self.calls.append((user_id, account_id, credential_ref))
        if self.error:
            raise self.error
        return self.credentials


def account(provider="UPSTOX", environment="SANDBOX", *, enabled=True, credential_ref="vault/ref"):
    return BrokerAccount(
        id=uuid4(),
        user_id=uuid4(),
        provider=provider,
        environment=environment,
        external_account_id="ACC-1",
        enabled=enabled,
        has_credential_ref=credential_ref is not None,
        credential_ref=credential_ref,
    )


def test_disabled_account_fails_before_credential_resolution():
    item = account(enabled=False)
    credentials = FakeCredentials(BrokerCredentials("token"))

    with pytest.raises(BrokerUnavailable, match="disabled"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)
    assert credentials.calls == []


def test_missing_credential_reference_fails_closed():
    item = account(credential_ref=None)
    credentials = FakeCredentials(BrokerCredentials("token"))

    with pytest.raises(CredentialUnavailable, match="no credential reference"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)
    assert credentials.calls == []


def test_whitespace_credential_reference_fails_before_resolution():
    item = account(credential_ref="   \t\n")
    credentials = FakeCredentials(BrokerCredentials("token"))

    with pytest.raises(CredentialUnavailable, match="no credential reference"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)
    assert credentials.calls == []


def test_credential_provider_failure_propagates_without_fallback():
    item = account()
    credentials = FakeCredentials(error=CredentialUnavailable("secret store unavailable"))

    with pytest.raises(CredentialUnavailable, match="secret store unavailable"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id).build(user_id=item.user_id, account_id=item.id)
    assert credentials.calls == [(item.user_id, item.id, "vault/ref")]


def test_cross_user_or_account_lookup_fails_before_credential_resolution():
    item = account()
    credentials = FakeCredentials(BrokerCredentials("token-value"))
    factory = BrokerAccountFactory(FakeRepository(item), credentials)

    with pytest.raises(BrokerUnavailable, match="not found"):
        factory.build(user_id=uuid4(), account_id=item.id)
    with pytest.raises(BrokerUnavailable, match="not found"):
        factory.build(user_id=item.user_id, account_id=uuid4())
    assert credentials.calls == []


def test_invalid_provider_result_fails_closed():
    item = account()
    credentials = FakeCredentials(object())

    with pytest.raises(CredentialUnavailable, match="invalid credentials"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)


def test_non_string_access_token_fails_closed():
    item = account()
    credentials = FakeCredentials(BrokerCredentials(123))

    with pytest.raises(CredentialUnavailable, match="no access token"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)


def test_non_string_dhan_client_id_fails_closed():
    item = account(provider="DHAN")
    credentials = FakeCredentials(BrokerCredentials("token-value", 123))

    with pytest.raises(CredentialUnavailable, match="no client id"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)


def test_upstox_credentials_are_resolved_by_exact_user_account_and_ref():
    item = account()
    credentials = FakeCredentials(BrokerCredentials("token-value"))

    broker = BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)

    assert isinstance(broker, UpstoxBroker)
    assert credentials.calls == [(item.user_id, item.id, "vault/ref")]
    assert broker.sandbox is True
    assert broker.orders_enabled is False
    assert broker.session.access_token() == "token-value"


def test_live_account_never_enables_live_mutations():
    item = account(environment="LIVE")
    credentials = FakeCredentials(BrokerCredentials("token-value"))

    broker = BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)

    assert isinstance(broker, UpstoxBroker)
    assert broker.sandbox is False
    assert broker.orders_enabled is False


def test_dhan_requires_client_id_and_keeps_mutations_disabled():
    item = account(provider="DHAN")
    credentials = FakeCredentials(BrokerCredentials("token-value", "CLIENT-1"))

    broker = BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)

    assert isinstance(broker, DhanBroker)
    assert broker.client_id == "CLIENT-1"
    assert broker.sandbox is True
    assert broker.orders_enabled is False


def test_dhan_missing_client_id_fails_closed():
    item = account(provider="DHAN")
    credentials = FakeCredentials(BrokerCredentials("token-value"))

    with pytest.raises(CredentialUnavailable, match="no client id"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)


def test_blank_access_token_from_provider_fails_closed():
    item = account()
    credentials = FakeCredentials(BrokerCredentials("  "))

    with pytest.raises(CredentialUnavailable, match="no access token"):
        BrokerAccountFactory(FakeRepository(item), credentials).build(user_id=item.user_id, account_id=item.id)


def test_unknown_account_is_not_constructed():
    user_id, account_id = uuid4(), uuid4()
    credentials = FakeCredentials(BrokerCredentials("token"))

    with pytest.raises(BrokerUnavailable, match="not found"):
        BrokerAccountFactory(FakeRepository(None), credentials).build(user_id=user_id, account_id=account_id)
