from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.paper import Order, OrderSide, OrderType, PaperBroker

router = APIRouter(prefix="/api/v1/paper", tags=["paper"])
broker = PaperBroker()


class PlacePaperOrderRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=128)
    symbol: str = Field(min_length=1, max_length=64)
    side: OrderSide
    order_type: OrderType
    quantity: int = Field(gt=0)
    market_price: Decimal = Field(gt=0)
    limit_price: Decimal | None = Field(default=None, gt=0)


@router.post("/orders", response_model=Order)
def place_paper_order(request: PlacePaperOrderRequest) -> Order:
    order = Order(order_id=request.order_id, symbol=request.symbol, side=request.side, order_type=request.order_type, quantity=request.quantity, limit_price=request.limit_price)
    try:
        broker.place_order(order, request.market_price)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return broker.orders[order.order_id]


@router.post("/orders/{order_id}/cancel", response_model=Order)
def cancel_paper_order(order_id: str) -> Order:
    try:
        return broker.cancel_order(order_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="paper order not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/orders", response_model=tuple[Order, ...])
def list_paper_orders() -> tuple[Order, ...]:
    return tuple(broker.orders.values())


@router.get("/positions")
def list_paper_positions():
    return tuple(broker.positions.values())


@router.get("/account")
def paper_account() -> dict[str, object]:
    return {"balance": broker.balance, "equity": broker.equity(), "positions": len(broker.positions), "trading_halted": broker.halted}


@router.post("/kill-switch")
def activate_kill_switch() -> dict[str, bool]:
    broker.kill_switch()
    return {"trading_halted": broker.halted}


@router.post("/kill-switch/clear")
def clear_kill_switch() -> dict[str, bool]:
    broker.clear_kill_switch()
    return {"trading_halted": broker.halted}
