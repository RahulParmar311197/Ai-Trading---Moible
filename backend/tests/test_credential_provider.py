from uuid import uuid4

import pytest

from app.brokers.credential_provider import BrokerCredentials, CredentialUnavailable, UnconfiguredCredentialProvider


def test_unconfigured_credential_provider_fails_closed_without_returning_credentials():
    provider = UnconfiguredCredentialProvider()

    with pytest.raises(CredentialUnavailable, match="not configured"):
        provider.resolve(user_id=uuid4(), account_id=uuid4(), credential_ref="opaque-ref")


def test_broker_credentials_are_immutable_and_do_not_expose_provider_state():
    credentials = BrokerCredentials("token-value", "client-id")

    assert credentials.access_token == "token-value"
    assert credentials.client_id == "client-id"
    with pytest.raises((AttributeError, TypeError)):
        credentials.access_token = "replacement"


def test_unconfigured_provider_does_not_echo_credential_reference_or_identity():
    provider = UnconfiguredCredentialProvider()
    user_id = uuid4()
    account_id = uuid4()
    secret_ref = "vault://private/credential/123"

    with pytest.raises(CredentialUnavailable) as exc_info:
        provider.resolve(user_id=user_id, account_id=account_id, credential_ref=secret_ref)

    message = str(exc_info.value)
    assert secret_ref not in message
    assert str(user_id) not in message
    assert str(account_id) not in message
