from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.backtest import run_backtest
from app.api.dependencies import get_backtest_repository
from app.main import app


class FakeBacktestRepository:
    def __init__(self):
        self.saved = {}

    def save(self, backtest_id, request, report):
        self.saved[str(backtest_id)] = (request, report)

    def get(self, backtest_id):
        saved = self.saved.get(str(backtest_id))
        if saved is None:
            return None
        request, report = saved
        return {
            "id": str(backtest_id),
            "created_at": datetime.now(timezone.utc),
            "request": request,
            "report": {
                "trade_count": report.trade_count,
                "net_pnl": str(report.net_pnl),
            },
        }


def test_post_backtest_runs_engine_and_persists_report():
    repository = FakeBacktestRepository()
    app.dependency_overrides[get_backtest_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/backtest",
                json={
                    "candles": [
                        {
                            "instrument_id": "TEST",
                            "timestamp": "2026-01-01T09:15:00Z",
                            "timeframe": "1m",
                            "open": "100",
                            "high": "102",
                            "low": "99",
                            "close": "101",
                            "volume": "10",
                        }
                    ],
                    "orders": [
                        {
                            "candle_index": 0,
                            "side": "LONG",
                            "quantity": "1",
                            "entry_price": "100",
                        }
                    ],
                },
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["report"]["trade_count"] == 1
        assert payload["report"]["net_pnl"] == "1"
        assert payload["id"] in repository.saved
    finally:
        app.dependency_overrides.clear()


def test_post_backtest_rejects_duplicate_order_indices():
    repository = FakeBacktestRepository()
    app.dependency_overrides[get_backtest_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/backtest",
                json={
                    "candles": [
                        {
                            "instrument_id": "TEST",
                            "timestamp": "2026-01-01T09:15:00Z",
                            "timeframe": "1m",
                            "open": "100",
                            "high": "102",
                            "low": "99",
                            "close": "101",
                            "volume": "10",
                        }
                    ],
                    "orders": [
                        {"candle_index": 0, "side": "LONG", "quantity": "1", "entry_price": "100"},
                        {"candle_index": 0, "side": "SHORT", "quantity": "1", "entry_price": "100"},
                    ],
                },
            )
        assert response.status_code == 422
        assert "one order plan" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
