from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.execution.gate import DeterministicExecutionGate, RiskSnapshot

from .models import Fill, Order, OrderSide, OrderStatus, OrderType, Position
from .repository import PaperRepository


class PaperBroker:
    """In-memory paper broker with deterministic fills and no live-broker access."""

    def __init__(self, starting_balance: Decimal = Decimal("100000"), fee_rate: Decimal = Decimal("0"), slippage: Decimal = Decimal("0"), max_order_notional: Decimal | None = None, max_position_quantity: int | None = None, max_daily_loss: Decimal | None = None, repository: PaperRepository | None = None, risk_gate: DeterministicExecutionGate | None = None) -> None:
        if not starting_balance.is_finite() or starting_balance < 0:
            raise ValueError("starting balance must be finite and non-negative")
        if not fee_rate.is_finite() or fee_rate < 0:
            raise ValueError("fee rate must be finite and non-negative")
        if not slippage.is_finite() or not 0 <= slippage < 1:
            raise ValueError("slippage must be finite, non-negative and less than 1")
        for name, value in (("max_order_notional", max_order_notional), ("max_daily_loss", max_daily_loss)):
            if value is not None and (not value.is_finite() or value <= 0):
                raise ValueError(f"{name} must be finite and positive")
        if max_position_quantity is not None and max_position_quantity <= 0:
            raise ValueError("max_position_quantity must be positive")
        self.balance = starting_balance
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.max_order_notional = max_order_notional
        self.max_position_quantity = max_position_quantity
        self.max_daily_loss = max_daily_loss
        self.repository = repository
        self.risk_gate = risk_gate
        self.realized_pnl_total = Decimal("0")
        self.halted = False
        self.orders: dict[str, Order] = {}
        self.fills: list[Fill] = []
        self.positions: dict[str, Position] = {}

    @classmethod
    def from_repository(cls, repository: PaperRepository, **kwargs: Any) -> "PaperBroker":
        """Restore paper state without replaying orders or touching a live broker."""
        broker = cls(repository=repository, **kwargs)
        state = repository.load_state()
        if state is not None:
            broker.balance = Decimal(str(state["balance"]))
            broker.realized_pnl_total = Decimal(str(state["realized_pnl_total"]))
            if not broker.balance.is_finite() or not broker.realized_pnl_total.is_finite():
                raise ValueError("persisted paper financial state must be finite")
            broker.halted = bool(state["halted"])
        broker.orders = {order.order_id: order for order in repository.load_orders()}
        broker.fills = repository.load_fills()
        broker.positions = {position.symbol: position for position in repository.load_positions()}
        return broker

    def place_order(self, order: Order, market_price: Decimal, fill_quantity: int | None = None) -> Fill | None:
        """Accept an order and optionally execute a deterministic first fill."""
        if self.halted:
            raise ValueError("paper trading is halted by kill switch")
        if order.order_id in self.orders:
            raise ValueError(f"duplicate order id: {order.order_id}")
        if not market_price.is_finite() or market_price <= 0:
            raise ValueError("market price must be finite and positive")
        if order.order_type is OrderType.LIMIT and order.limit_price is None:
            raise ValueError("limit order requires limit_price")
        if self.risk_gate is not None:
            decision = self.risk_gate.evaluate(
                order,
                market_price,
                RiskSnapshot(
                    balance=self.balance,
                    realized_pnl=self.realized_pnl_total,
                    halted=self.halted,
                    position_quantity=self.positions.get(order.symbol).quantity if order.symbol in self.positions else 0,
                ),
            )
            if not decision.approved:
                raise ValueError(decision.reason)
        projected_quantity = self._projected_position_quantity(order)
        if self.max_position_quantity is not None and abs(projected_quantity) > self.max_position_quantity:
            raise ValueError("order exceeds paper position limit")
        if self.max_order_notional is not None and market_price * order.quantity > self.max_order_notional:
            raise ValueError("order exceeds paper risk notional limit")

        stored = order.model_copy(update={"status": OrderStatus.NEW})
        self.orders[order.order_id] = stored
        self._persist_order(stored)
        self._audit("ORDER_ACCEPTED", order.order_id, {"status": stored.status.value})

        if order.order_type is OrderType.LIMIT:
            if order.side is OrderSide.BUY and market_price > order.limit_price:
                return None
            if order.side is OrderSide.SELL and market_price < order.limit_price:
                return None

        requested = order.quantity if fill_quantity is None else fill_quantity
        return self.fill_order(order.order_id, requested, market_price)

    def process_market(self, symbol: str, market_price: Decimal, max_fill_quantity: int | None = None) -> list[Fill]:
        """Process all marketable open orders for a symbol in stable order-id order."""
        if not market_price.is_finite() or market_price <= 0:
            raise ValueError("market price must be finite and positive")
        fills: list[Fill] = []
        for order_id in sorted(self.orders):
            order = self.orders[order_id]
            if order.symbol != symbol or order.status not in (OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED):
                continue
            if order.order_type is OrderType.LIMIT:
                if order.limit_price is None:
                    continue
                if order.side is OrderSide.BUY and market_price > order.limit_price:
                    continue
                if order.side is OrderSide.SELL and market_price < order.limit_price:
                    continue
            remaining = order.quantity - order.filled_quantity
            if remaining <= 0:
                continue
            quantity = remaining if max_fill_quantity is None else min(remaining, max_fill_quantity)
            if quantity <= 0:
                continue
            fills.append(self.fill_order(order_id, quantity, market_price))
        return fills

    def fill_order(self, order_id: str, quantity: int, market_price: Decimal) -> Fill:
        """Execute a deterministic fill against an accepted paper order."""
        if self.halted:
            raise ValueError("paper trading is halted by kill switch")
        if not market_price.is_finite() or market_price <= 0:
            raise ValueError("market price must be finite and positive")
        if quantity <= 0:
            raise ValueError("fill quantity must be positive")
        order = self.orders.get(order_id)
        if order is None:
            raise KeyError(order_id)
        if order.status not in (OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED):
            raise ValueError("only open orders can be filled")
        remaining = order.quantity - order.filled_quantity
        if quantity > remaining:
            raise ValueError("fill quantity exceeds remaining order quantity")

        execution_price = market_price * (Decimal("1") + self.slippage if order.side is OrderSide.BUY else Decimal("1") - self.slippage)
        fee = execution_price * quantity * self.fee_rate
        fill = Fill(order_id=order.order_id, quantity=quantity, price=execution_price, fee=fee)
        filled_quantity = order.filled_quantity + quantity
        prior_value = (order.average_fill_price or Decimal("0")) * order.filled_quantity
        average_fill_price = (prior_value + execution_price * quantity) / filled_quantity
        status = OrderStatus.FILLED if filled_quantity == order.quantity else OrderStatus.PARTIALLY_FILLED
        stored = order.model_copy(update={"status": status, "filled_quantity": filled_quantity, "average_fill_price": average_fill_price})
        self.orders[order.order_id] = stored
        self.fills.append(fill)
        self._apply_fill(order, fill)
        self._persist_order(stored)
        self._persist_fill(fill)
        position = self.positions.get(order.symbol)
        if position is None:
            self._delete_position(order.symbol)
        else:
            self._persist_position(position)
        if self.max_daily_loss is not None and self.realized_pnl_total <= -self.max_daily_loss:
            self.halted = True
            self._audit("KILL_SWITCH_ACTIVATED", order.order_id, {"reason": "max_daily_loss"})
        self._persist_state()
        self._audit("ORDER_FILLED", order.order_id, {"quantity": fill.quantity, "price": str(fill.price), "fee": str(fill.fee), "filled_quantity": stored.filled_quantity, "remaining_quantity": order.quantity - stored.filled_quantity, "status": stored.status.value})
        return fill

    def cancel_order(self, order_id: str) -> Order:
        order = self.orders.get(order_id)
        if order is None:
            raise KeyError(order_id)
        if order.status not in (OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED):
            raise ValueError("only open orders can be cancelled")
        cancelled = order.model_copy(update={"status": OrderStatus.CANCELLED})
        self.orders[order_id] = cancelled
        self._persist_order(cancelled)
        self._persist_state()
        self._audit("ORDER_CANCELLED", order_id, {"filled_quantity": cancelled.filled_quantity, "remaining_quantity": cancelled.quantity - cancelled.filled_quantity})
        return cancelled

    def kill_switch(self) -> None:
        self.halted = True
        self._persist_state()
        self._audit("KILL_SWITCH_ACTIVATED", None, {"reason": "manual"})

    def clear_kill_switch(self) -> None:
        self.halted = False
