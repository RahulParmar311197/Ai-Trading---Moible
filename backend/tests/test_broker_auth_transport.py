import pytest

from app.brokers.dhan import DhanBroker
from app.brokers.http import BrokerHTTPError, HTTPBrokerClient
from app.brokers.session import StaticTokenBrokerSession
from app.brokers.upstox import UpstoxBroker


class FakeResponse:
    is_error = False

    def json(self):
        return {"ok": True}


class FakeErrorResponse:
    is_error = True
    status_code = 403

    def json(self):
        return {
            "errorType": "Invalid_Authentication",
            "errorCode": "DH-901",
            "errorMessage": "Client ID or user generated access token is invalid or expired.",
        }


class FakeAsyncClient:
    captured = None
    response = FakeResponse()

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, method, path, **kwargs):
        FakeAsyncClient.captured = {"method": method, "path": path, **kwargs}
        return FakeAsyncClient.response


@pytest.mark.asyncio
async def test_http_client_supports_custom_auth_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.brokers.http.httpx.AsyncClient", FakeAsyncClient)
    FakeAsyncClient.response = FakeResponse()
    session = StaticTokenBrokerSession("dhan", "client", "secret-token")
    client = HTTPBrokerClient("https://example.invalid", session=session, auth_header="access-token", auth_scheme="")

    await client.request("GET", "/profile")

    assert FakeAsyncClient.captured["headers"]["access-token"] == "secret-token"
    assert "Authorization" not in FakeAsyncClient.captured["headers"]


@pytest.mark.asyncio
async def test_http_client_preserves_safe_provider_error_details(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.brokers.http.httpx.AsyncClient", FakeAsyncClient)
    FakeAsyncClient.response = FakeErrorResponse()
    client = HTTPBrokerClient("https://example.invalid", access_token="secret-token")

    with pytest.raises(BrokerHTTPError, match=r"HTTP 403 \(DH-901: Client ID or user generated access token is invalid or expired\.\)"):
        await client.request("GET", "/profile")


@pytest.mark.asyncio
async def test_upstox_keeps_bearer_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.brokers.http.httpx.AsyncClient", FakeAsyncClient)
    FakeAsyncClient.response = FakeResponse()
    broker = UpstoxBroker("upstox-token")

    await broker._client.request("GET", "/user/get-funds-and-margin")

    assert FakeAsyncClient.captured["headers"]["Authorization"] == "Bearer upstox-token"
    assert "access-token" not in FakeAsyncClient.captured["headers"]


@pytest.mark.asyncio
async def test_dhan_uses_access_token_header_without_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.brokers.http.httpx.AsyncClient", FakeAsyncClient)
    FakeAsyncClient.response = FakeResponse()
    broker = DhanBroker("client", "dhan-token")

    await broker._client.request("GET", "/profile")

    assert FakeAsyncClient.captured["headers"]["access-token"] == "dhan-token"
    assert "Authorization" not in FakeAsyncClient.captured["headers"]
