from datetime import timezone

import httpx
import pytest

from app.brokers.auth import BrokerAuthError, DhanOAuth, UpstoxOAuth
from app.brokers.session import BrokerSessionState


def transport_for(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_upstox_authorization_code_exchange_uses_documented_form_fields_without_leaking_secret() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"access_token": "secret-access-token"})

    token = await UpstoxOAuth(transport=transport_for(handler)).exchange_code(
        code="one-time-code",
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="https://example.test/callback",
    )

    assert token.access_token == "secret-access-token"
    assert "grant_type=authorization_code" in captured["body"]
    assert "client_id=client-id" in captured["body"]
    assert "client_secret=client-secret" in captured["body"]
    assert token.expires_at is not None
    assert token.expires_at.tzinfo is timezone.utc
    session = token.session("upstox", "account")
    assert session.state is BrokerSessionState.AUTHENTICATED
    assert session.authentication().authenticated is True


@pytest.mark.asyncio
async def test_dhan_consent_and_consume_return_expiring_token() -> None:
    responses = [
        httpx.Response(200, json={"redirect_URL": "https://example.test/callback?tokenId=consent-123"}),
        httpx.Response(200, json={"accessToken": "secret-token", "expiryTime": "2027-09-02T18:00:00"}),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    oauth = DhanOAuth(transport=transport_for(handler))
    token_id = await oauth.generate_consent(client_id="client", api_key="api-key", api_secret="api-secret")
    token = await oauth.consume_consent(token_id=token_id, api_key="api-key", api_secret="api-secret")

    assert token_id == "consent-123"
    assert token.access_token == "secret-token"
    assert token.expires_at is not None
    assert token.expires_at.hour == 12
    assert token.session("dhan", "client").state is BrokerSessionState.AUTHENTICATED


@pytest.mark.asyncio
async def test_dhan_renew_uses_existing_access_token_only_at_transport_boundary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["access-token"] == "old-token"
        assert request.headers["dhanClientId"] == "client"
        return httpx.Response(200, json={"accessToken": "new-token", "expiryTime": "2027-09-02T18:00:00+00:00"})

    token = await DhanOAuth(transport=transport_for(handler)).renew(client_id="client", access_token="old-token")

    assert token.access_token == "new-token"
    assert token.expires_at is not None


@pytest.mark.asyncio
async def test_auth_failures_do_not_include_credential_values() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    with pytest.raises(BrokerAuthError) as exc:
        await UpstoxOAuth(transport=transport_for(handler)).exchange_code(
            code="one-time-code",
            client_id="client-id",
            client_secret="super-secret",
            redirect_uri="https://example.test/callback",
        )

    assert "super-secret" not in str(exc.value)
    assert "one-time-code" not in str(exc.value)
