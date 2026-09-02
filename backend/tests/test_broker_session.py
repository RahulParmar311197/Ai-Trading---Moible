from datetime import datetime, timedelta, timezone

import pytest

from app.brokers.session import BrokerSessionState, StaticTokenBrokerSession


def test_authenticated_session_exposes_only_non_secret_projection() -> None:
    session = StaticTokenBrokerSession("upstox", "account-1", "secret-token")

    auth = session.authentication()

    assert session.state is BrokerSessionState.AUTHENTICATED
    assert auth.provider == "upstox"
    assert auth.account_id == "account-1"
    assert auth.authenticated is True
    assert "secret-token" not in auth.model_dump_json()


def test_empty_token_is_unauthenticated_and_cannot_be_read() -> None:
    session = StaticTokenBrokerSession("dhan", "account-1", "")

    assert session.state is BrokerSessionState.UNAUTHENTICATED
    assert session.authentication().authenticated is False
    with pytest.raises(RuntimeError, match="unauthenticated"):
        session.access_token()


def test_expired_session_is_not_usable() -> None:
    session = StaticTokenBrokerSession(
        "upstox",
        "account-1",
        "secret-token",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )

    assert session.state is BrokerSessionState.EXPIRED
    assert session.authentication().authenticated is False
    with pytest.raises(RuntimeError, match="expired"):
        session.access_token()


def test_invalidation_erases_secret_and_blocks_access() -> None:
    session = StaticTokenBrokerSession("dhan", "account-1", "secret-token")
    session.invalidate()

    assert session.state is BrokerSessionState.INVALIDATED
    assert session.authentication().authenticated is False
    with pytest.raises(RuntimeError, match="invalidated"):
        session.access_token()


def test_external_refresh_can_replace_invalidated_token() -> None:
    session = StaticTokenBrokerSession("upstox", "account-1", "old-token")
    session.invalidate()
    session.replace_token("new-token", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5))

    assert session.state is BrokerSessionState.AUTHENTICATED
    assert session.access_token() == "new-token"
