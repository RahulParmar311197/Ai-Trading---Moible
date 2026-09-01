from decimal import Decimal
from uuid import uuid4

from app.backtest.engine import BacktestEngine, BacktestReport, MarketOrder, Side
from app.backtest.repository import PostgresBacktestRepository
from app.market.models import Candle, Timeframe
from datetime import datetime, timezone


class FakeExecutor:
    def __init__(self):
        self.params = None

    def execute(self, query, params):
        self.params = params

    def fetch_one(self, query, params):
        return None


def test_repository_serializes_nested_report_as_json():
    candle = Candle(
        instrument_id="TEST",
        timestamp=datetime.fromtimestamp(0, timezone.utc),
        timeframe=Timeframe.M1,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume=Decimal("1"),
    )
    result = BacktestEngine([candle]).run(
        type("OneShot", (), {"on_candle": lambda self, _: MarketOrder(Side.LONG, Decimal("1"), Decimal("100"))})()
    )
    report = BacktestReport.from_result(result)
    executor = FakeExecutor()
    PostgresBacktestRepository(executor).save(uuid4(), {"candles": [candle.model_dump(mode="json")]}, report)

    assert executor.params is not None
    assert '"trades"' in executor.params["report"]
    assert '"order_events"' in executor.params["report"]
    assert "BacktestTrade" not in executor.params["report"]
