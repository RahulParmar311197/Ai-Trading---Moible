from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import Fill, Order, OrderSide, OrderStatus, OrderType, Position
from .repository import PaperRepository


class PaperBroker:
    """In-memory paper broker with deterministic fills and no live-broker access."""

    def __init__(self, starting_balance: Decimal = Decimal("100000"), fee_rate: Decimal = Decimal("0"), slippage: Decimal = Decimal("0"), max_order_notional: Decimal | None = None, max_position_quantity: int | None = None, max_daily_loss: Decimal | None = None, repository: PaperRepository | None = None) -> None:
        if starting_balance < 0 or fee_rate < 0 or slippage < 0:
            raise ValueError("balance, fee rate and slippage must be non-negative")
        for name, value in (("max_order_notional", max_order_notional), ("max_daily_loss", max_daily_loss)):
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")
        if max_position_quantity is not None and max_position_quantity <= 0:
            raise ValueError("max_position_quantity must be positive")
        self.balance = starting_balance
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.max_order_notional = max_order_notional
        self.max_position_quantity = max_position_quantity
        self.max_daily_loss = max_daily_loss
        self.repository = repository
        self.realized_pnl_total = Decimal("0")
        self.halted = False
        self.orders: dict[str, Order] = {}
        self.fills: list[Fill] = []
        self.positions: dict[str, Position] = {}

    def place_order(self, order: Order, market_price: Decimal, fill_quantity: int | None = None) -> Fill | None:
        """Accept an order and optionally execute a deterministic first fill.

        ``fill_quantity`` is paper-only simulation control. Omitting it preserves the
        existing behavior for marketable orders by filling the entire remaining quantity.
        Resting limit orders remain NEW until ``process_market`` is called.
        """
        if self.halted:
            raise ValueError("paper trading is halted by kill switch")
        if order.order_id in self.orders:
            raise ValueError(f"duplicate order id: {order.order_id}")
        if market_price <= 0:
            raise ValueError("market price must be positive")
        if order.order_type is OrderType.LIMIT and order.limit_price is None:
            raise ValueError("limit order requires limit_price")
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
        if market_price <= 0:
            raise ValueError("market price must be positive")
        fills: list[Fill] = []
        for order_id in sorted(self.orders):
            order = self.orders[order_id]
            if order.symbol != symbol or order.status is not OrderStatus.NEW:
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
        if market_price <= 0:
            raise ValueError("market price must be positive")
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
        self._audit("ORDER_FILLED", order.order_id, {"quantity": fill.quantity, "price": str(fill.price), "fee": str(fill.fee), "filled_quantity": stored.filled_quantity, "remaining_quantity": order.quantity - stored.filled_quantity, "status": stored.status.value})
        if self.max_daily_loss is not None and self.realized_pnl_total <= -self.max_daily_loss:
            self.halted = True
            self._audit("KILL_SWITCH_ACTIVATED", order.order_id, {"reason": "max_daily_loss"})
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
        self._audit("ORDER_CANCELLED", order_id, {"filled_quantity": cancelled.filled_quantity, "remaining_quantity": cancelled.quantity - cancelled.filled_quantity})
        return cancelled

    def kill_switch(self) -> None:
        self.halted = True
        self._audit("KILL_SWITCH_ACTIVATED", None, {"reason": "manual"})

    def clear_kill_switch(self) -> None:
        self.halted = False
        self._audit("KILL_SWITCH_CLEARED", None, {})

    def mark_to_market(self, symbol: str, price: Decimal) -> Position | None:
        if price <= 0:
            raise ValueError("mark price must be positive")
        position = self.positions.get(symbol)
        if position is None:
            return None
        marked = position.mark(price)
        self._persist_position(marked)
        return marked

    def equity(self, marks: dict[str, Decimal] | None = None) -> Decimal:
        total = self.balance
        for symbol, position in self.positions.items():
            if marks and symbol in marks:
                total += position.quantity * marks[symbol]
        return total

    def _projected_position_quantity(self, order: Order) -> int:
        current = self.positions.get(order.symbol)
        existing = current.quantity if current else 0
        signed = order.quantity if order.side is OrderSide.BUY else -order.quantity
        return existing + signed

    def _apply_fill(self, order: Order, fill: Fill) -> None:
        signed = fill.quantity if order.side is OrderSide.BUY else -fill.quantity
        current = self.positions.get(order.symbol)
        if current is None:
            self.positions[order.symbol] = Position(symbol=order.symbol, quantity=signed, average_price=fill.price)
            self.balance -= fill.price * signed + fill.fee
            return

        old_qty = current.quantity
        new_qty = old_qty + signed
        if old_qty == 0 or (old_qty > 0 and signed > 0) or (old_qty < 0 and signed < 0):
            total_cost = current.average_price * abs(old_qty) + fill.price * abs(signed)
            current.average_price = total_cost / abs(new_qty)
            current.quantity = new_qty
        else:
            closing_qty = min(abs(old_qty), abs(signed))
            direction = Decimal("1") if old_qty > 0 else Decimal("-1")
            pnl = (fill.price - current.average_price) * closing_qty * direction
            current.realized_pnl += pnl - fill.fee
            self.realized_pnl_total += pnl - fill.fee
            current.quantity = new_qty
            if new_qty != 0 and (old_qty > 0) != (new_qty > 0):
                current.average_price = fill.price
        self.balance -= fill.price * signed + fill.fee
        if current.quantity == 0:
            self.positions.pop(order.symbol, None)

    def _persist_order(self, order: Order) -> None:
        if self.repository is not None:
            self.repository.save_order(order)

    def _persist_fill(self, fill: Fill) -> None:
        if self.repository is not None:
            self.repository.save_fill(fill)

    def _persist_position(self, position: Position) -> None:
        if self.repository is not None:
            self.repository.save_position(position)

    def _delete_position(self, symbol: str) -> None:
        if self.repository is not None:
            self.repository.delete_position(symbol)

    def _audit(self, event_type: str, entity_id: str | None, payload: dict[str, Any]) -> None:
        if self.repository is not None:
            self.repository.append_audit(event_type, entity_id, payload)
