import pytest

from app.brokers.dhan import DhanBroker
from app.brokers.http import HTTPBrokerClient
from app.brokers.session import StaticTokenBrokerSession
from app.brokers.upstox import UpstoxBroker


class FakeResponse:
    is_error = False

    def json(self):
        return {"ok": True}


class FakeAsyncClient:
    captured = None

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, method, path, **kwargs):
        FakeAsyncClient.captured = {"method": method, "path": path, **kwargs}
        return FakeResponse()


@pytest.mark.asyncio
async def test_http_client_supports_custom_auth_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.brokers.http.httpx.AsyncClient", FakeAsyncClient)
    session = StaticTokenBrokerSession("dhan", "client", "secret-token")
    client = HTTPBrokerClient("https://example.invalid", session=session, auth_header="access-token", auth_scheme="")

    await client.request("GET", "/profile")

    assert FakeAsyncClient.captured["headers"]["access-token"] == "secret-token"
    assert "Authorization" not in FakeAsyncClient.captured["headers"]


@pytest.mark.asyncio
async def test_upstox_keeps_bearer_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.brokers.http.httpx.AsyncClient", FakeAsyncClient)
    broker = UpstoxBroker("upstox-token")

    await broker._client.request("GET", "/user/get-funds-and-margin")

    assert FakeAsyncClient.captured["headers"]["Authorization"] == "Bearer upstox-token"
    assert "access-token" not in FakeAsyncClient.captured["headers"]


@pytest.mark.asyncio
async def test_dhan_uses_access_token_header_without_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.brokers.http.httpx.AsyncClient", FakeAsyncClient)
    broker = DhanBroker("client", "dhan-token")

    await broker._client.request("GET", "/profile")

    assert FakeAsyncClient.captured["headers"]["access-token"] == "dhan-token"
    assert "Authorization" not in FakeAsyncClient.captured["headers"]
