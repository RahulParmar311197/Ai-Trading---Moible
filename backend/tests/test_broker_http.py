import pytest

from app.brokers.http import BrokerHTTPError, HTTPBrokerClient
from app.brokers.session import BrokerSessionState


class LeakySession:
    state = BrokerSessionState.AUTHENTICATED

    def authentication(self):
        raise AssertionError("authentication should not be called")

    def access_token(self) -> str:
        raise RuntimeError("provider secret should never escape")

    def invalidate(self) -> None:
        pass


@pytest.mark.asyncio
async def test_session_runtime_errors_are_sanitized() -> None:
    client = HTTPBrokerClient("https://example.invalid", session=LeakySession())

    with pytest.raises(BrokerHTTPError, match="broker session/transport failure: RuntimeError") as exc_info:
        await client.request("GET", "/account")

    assert "provider secret" not in str(exc_info.value)
