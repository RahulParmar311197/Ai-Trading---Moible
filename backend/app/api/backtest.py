"""Deterministic backtest API."""

from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_backtest_repository
from app.backtest.engine import BacktestEngine, BacktestReport, MarketOrder, Side
from app.backtest.repository import PostgresBacktestRepository
from app.market.models import Candle

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


class BacktestOrderPlan(BaseModel):
    """Transport-only deterministic order instruction for one visible candle."""

    candle_index: int = Field(ge=0)
    side: Side
    quantity: Decimal | None = Field(default=None, gt=0)
    entry_price: Decimal = Field(gt=0)
    stop_price: Decimal | None = Field(default=None, gt=0)
    target_price: Decimal | None = Field(default=None, gt=0)


class BacktestRequest(BaseModel):
    candles: list[Candle] = Field(min_length=1)
    orders: list[BacktestOrderPlan] = Field(default_factory=list)
    starting_balance: Decimal = Field(default=Decimal("100000"), ge=0)
    fee_rate: Decimal = Field(default=Decimal("0"), ge=0)
    slippage_bps: Decimal = Field(default=Decimal("0"), ge=0)
    risk_per_trade: Decimal | None = Field(default=None, gt=0, le=100)


def _report_payload(report: BacktestReport) -> dict[str, object]:
    return {
        "starting_balance": str(report.starting_balance),
        "ending_balance": str(report.ending_balance),
        "net_pnl": str(report.net_pnl),
        "trade_count": report.trade_count,
        "win_rate": str(report.win_rate),
        "expectancy": str(report.expectancy),
        "max_drawdown": str(report.max_drawdown),
        "trades": [
            {
                "side": trade.side.value,
                "quantity": str(trade.quantity),
                "entry_price": str(trade.entry_price),
                "exit_price": str(trade.exit_price),
                "gross_pnl": str(trade.gross_pnl),
                "fees": str(trade.fees),
                "slippage": str(trade.slippage),
                "net_pnl": str(trade.net_pnl),
            }
            for trade in report.trades
        ],
        "order_events": [
            {
                "sequence": event.sequence,
                "event": event.event,
                "side": event.side.value,
                "quantity": str(event.quantity),
                "price": str(event.price),
                "timestamp": event.timestamp,
            }
            for event in report.order_events
        ],
    }


class PlannedOrderStrategy:
    """Adapt an API order plan to the existing BacktestStrategy protocol."""

    def __init__(self, plans: list[BacktestOrderPlan]) -> None:
        self._plans = {plan.candle_index: plan for plan in plans}

    def on_candle(self, candles: tuple[Candle, ...]) -> MarketOrder | None:
        index = len(candles) - 1
        plan = self._plans.get(index)
        if plan is None:
            return None
        return MarketOrder(plan.side, plan.quantity, plan.entry_price, plan.stop_price, plan.target_price)


@router.post("")
def run_backtest(
    request: BacktestRequest,
    repository: PostgresBacktestRepository = Depends(get_backtest_repository),
) -> dict[str, object]:
    if len({plan.candle_index for plan in request.orders}) != len(request.orders):
        raise HTTPException(status_code=422, detail="only one order plan is allowed per candle index")
    if any(plan.candle_index >= len(request.candles) for plan in request.orders):
        raise HTTPException(status_code=422, detail="order candle_index is outside the supplied candle range")

    for candle in request.candles:
        try:
            candle.validate_ohlc()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    engine = BacktestEngine(
        request.candles,
        starting_balance=request.starting_balance,
        fee_rate=request.fee_rate,
        slippage_bps=request.slippage_bps,
        risk_per_trade=request.risk_per_trade,
    )
    report = BacktestReport.from_result(engine.run(PlannedOrderStrategy(request.orders)))
    backtest_id = uuid4()
    repository.save(backtest_id, request.model_dump(mode="json"), report)
    return {"id": str(backtest_id), "report": _report_payload(report)}


@router.get("/{backtest_id}")
def get_backtest(
    backtest_id: UUID,
    repository: PostgresBacktestRepository = Depends(get_backtest_repository),
) -> dict[str, object]:
    row = repository.get(backtest_id)
    if row is None:
        raise HTTPException(status_code=404, detail="backtest not found")
    return {
        "id": str(row["id"]),
        "created_at": row["created_at"],
        "request": row["request"],
        "report": row["report"],
    }
