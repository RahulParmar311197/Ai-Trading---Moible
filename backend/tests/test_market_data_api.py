from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.api.market_data import get_candle_repository
from app.market.models import Candle, Timeframe


class FakeCandleRepository:
    def list_range(self, instrument_id, timeframe, start_time, end_time):
        return [Candle(
            instrument_id=instrument_id,
            timestamp=datetime(2026, 9, 1, 9, 15, tzinfo=timezone.utc),
            timeframe=Timeframe(timeframe),
            open=Decimal("25000"), high=Decimal("25050"),
            low=Decimal("24980"), close=Decimal("25030"), volume=Decimal("100"),
        )]


def test_candles_endpoint_returns_persisted_candles() -> None:
    app.dependency_overrides[get_candle_repository] = lambda: FakeCandleRepository()
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/market-data/candles",
            params={
                "instrument_id": "nifty-front",
                "timeframe": "15m",
                "start_time": "2026-09-01T09:00:00Z",
                "end_time": "2026-09-01T09:30:00Z",
            },
        )
        assert response.status_code == 200
        assert response.json()["candles"][0]["close"] == "25030"
    finally:
        app.dependency_overrides.clear()


def test_candles_endpoint_rejects_invalid_range() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/market-data/candles",
        params={
            "instrument_id": "nifty-front",
            "timeframe": "15m",
            "start_time": "2026-09-01T09:30:00Z",
            "end_time": "2026-09-01T09:00:00Z",
        },
    )
    assert response.status_code == 400
