from uuid import uuid4

import pytest

from app.brokers.credential_provider import CredentialUnavailable, UnconfiguredCredentialProvider


def test_unconfigured_credential_provider_fails_closed_without_returning_credentials():
    provider = UnconfiguredCredentialProvider()

    with pytest.raises(CredentialUnavailable, match="not configured"):
        provider.resolve(user_id=uuid4(), account_id=uuid4(), credential_ref="opaque-ref")
