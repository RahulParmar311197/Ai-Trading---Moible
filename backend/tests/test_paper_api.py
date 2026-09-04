from decimal import Decimal

from fastapi.testclient import TestClient

from app.api import paper as paper_api
from app.main import app
from app.paper import OrderSide, OrderType, PaperBroker


def test_paper_api_uses_single_hydrated_broker(monkeypatch) -> None:
    broker = PaperBroker(starting_balance=Decimal("1000"))
    monkeypatch.setattr(paper_api, "get_paper_broker", lambda: broker)

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
