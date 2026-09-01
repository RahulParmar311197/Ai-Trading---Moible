import pytest

from app.market.upstox_live import UpstoxLiveConfigurationError, UpstoxLiveFeed


def test_upstox_live_requires_token():
    with pytest.raises(UpstoxLiveConfigurationError):
        UpstoxLiveFeed("", lambda payload: payload)


@pytest.mark.asyncio
async def test_authorize_extracts_v3_socket(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": {"authorized_redirect_uri": "wss://example.test/feed"}}

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr("app.market.upstox_live.httpx.AsyncClient", lambda **kwargs: Client())
    feed = UpstoxLiveFeed("token", lambda payload: payload)
    assert await feed.authorize() == "wss://example.test/feed"
