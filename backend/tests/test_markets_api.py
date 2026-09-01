from fastapi.testclient import TestClient

from app.main import app


def test_supported_timeframes() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/markets/timeframes")
    assert response.status_code == 200
    assert response.json()["timeframes"] == [
        "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1D", "1W"
    ]
