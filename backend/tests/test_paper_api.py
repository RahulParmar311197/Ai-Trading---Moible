from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api import paper as paper_api
from app.api.auth import current_user
from app.auth import AuthUser
from app.main import app
from app.paper import OrderSide, OrderType, PaperBroker


def test_paper_api_uses_authenticated_user_broker(monkeypatch) -> None:
    user = AuthUser(uuid4(), "trader@example.com", "Trader", "ACTIVE")
    broker = PaperBroker(starting_balance=Decimal("1000"))
    monkeypatch.setattr(paper_api, "get_paper_broker", lambda user_id: broker if user_id == user.id else None)
    app.dependency_overrides[current_user] = lambda: user
    try:
        with TestClient(app) as client:
            placed = client.post(
                "/api/v1/paper/orders",
                json={
                    "order_id": "api-1",
                    "symbol": "NIFTY",
                    "side": OrderSide.BUY.value,
                    "order_type": OrderType.MARKET.value,
                    "quantity": 1,
                    "market_price": "100",
                },
            )
            assert placed.status_code == 200
            assert placed.json()["status"] == "FILLED"

            account = client.get("/api/v1/paper/account")
            assert account.status_code == 200
            assert account.json()["positions"] == 1
            assert account.json()["balance"] == "900"
    finally:
        app.dependency_overrides.pop(current_user, None)


def test_paper_broker_factory_receives_authenticated_user_id(monkeypatch) -> None:
    user = AuthUser(UUID("11111111-1111-1111-1111-111111111111"), "a@example.com", "A", "ACTIVE")
    captured = []
    broker = PaperBroker(starting_balance=Decimal("1000"))
    monkeypatch.setattr(paper_api, "get_paper_broker", lambda user_id: captured.append(user_id) or broker)
    app.dependency_overrides[current_user] = lambda: user
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/paper/account")
            assert response.status_code == 200
        assert captured == [user.id]
    finally:
        app.dependency_overrides.pop(current_user, None)
