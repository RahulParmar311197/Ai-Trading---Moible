from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.auth import current_user
from app.api import broker_state as broker_state_api
from app.auth import AuthUser
from app.brokers.base import (
    Account,
    BrokerAuthentication,
    BrokerOrder,
    BrokerOrderType,
    BrokerPosition,
    BrokerSide,
    BrokerOrderStatus,
)
from app.brokers.credential_provider import CredentialUnavailable
from app.main import app


class FakeBroker:
    async def authenticate(self):
        return BrokerAuthentication(provider="upstox", account_id="ACC-1", authenticated=True)

    async def get_account(self):
        return Account(account_id="ACC-1", balance=Decimal("100000"), available_margin=Decimal("90000"))

    async def get_positions(self):
        return (BrokerPosition(symbol="NIFTY", quantity=1, average_price=Decimal("100")),)

    async def get_orders(self):
        return (
            BrokerOrder(
                order_id="OID-1",
                client_order_id="CID-1",
                symbol="NIFTY",
                side=BrokerSide.BUY,
                order_type=BrokerOrderType.LIMIT,
                quantity=1,
                status=BrokerOrderStatus.NEW,
            ),
        )


class FakeFactory:
    def __init__(self):
        self.calls = []

    def build(self, *, user_id, account_id):
        self.calls.append((user_id, account_id))
        return FakeBroker()


class UnauthenticatedBroker:
    async def authenticate(self):
        return BrokerAuthentication(provider="upstox", account_id="ACC-1", authenticated=False)


class AuthenticationFactory:
    def build(self, *, user_id, account_id):
        return UnauthenticatedBroker()


def test_broker_state_requires_authentication():
    account_id = uuid4()
    with TestClient(app) as client:
        assert client.get(f"/api/v1/brokers/accounts/{account_id}/state").status_code == 401


def test_broker_state_is_read_only_and_user_scoped(monkeypatch):
    user = AuthUser(uuid4(), "trader@example.com", "Trader", "ACTIVE")
    factory = FakeFactory()
    monkeypatch.setattr(broker_state_api, "get_broker_factory", lambda: factory)
    account_id = uuid4()
    app.dependency_overrides[current_user] = lambda: user
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/brokers/accounts/{account_id}/state")
            assert response.status_code == 200
            body = response.json()
            assert body["account"]["account_id"] == "ACC-1"
            assert body["positions"][0]["symbol"] == "NIFTY"
            assert body["orders"][0]["status"] == "NEW"
            assert factory.calls == [(user.id, account_id)]
    finally:
        app.dependency_overrides.clear()


def test_broker_state_fails_closed_when_broker_authentication_is_unavailable(monkeypatch):
    user = AuthUser(uuid4(), "trader@example.com", "Trader", "ACTIVE")
    monkeypatch.setattr(broker_state_api, "get_broker_factory", lambda: AuthenticationFactory())
    app.dependency_overrides[current_user] = lambda: user
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/brokers/accounts/{uuid4()}/state")
            assert response.status_code == 503
            assert response.json()["detail"] == "broker authentication unavailable"
    finally:
        app.dependency_overrides.clear()


def test_broker_state_fails_closed_when_credentials_unavailable(monkeypatch):
    user = AuthUser(uuid4(), "trader@example.com", "Trader", "ACTIVE")
    monkeypatch.setattr(
        broker_state_api,
        "get_broker_factory",
        lambda: (_ for _ in ()).throw(CredentialUnavailable("secret store unavailable")),
    )
    app.dependency_overrides[current_user] = lambda: user
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/brokers/accounts/{uuid4()}/state")
            assert response.status_code == 503
            assert response.json()["detail"] == "broker credentials or account are unavailable"
            assert "secret store" not in response.text
    finally:
        app.dependency_overrides.clear()
