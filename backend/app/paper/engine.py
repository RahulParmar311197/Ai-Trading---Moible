from __future__ import annotations

from decimal import Decimal

from .models import Fill, Order, OrderSide, OrderStatus, OrderType, Position


class PaperBroker:
    """In-memory paper broker with deterministic fills and no live-broker access."""

    def __init__(self, starting_balance: Decimal = Decimal("100000"), fee_rate: Decimal = Decimal("0"), slippage: Decimal = Decimal("0")) -> None:
        if starting_balance < 0 or fee_rate < 0 or slippage < 0:
            raise ValueError("balance, fee rate and slippage must be non-negative")
        self.balance = starting_balance
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.orders: dict[str, Order] = {}
        self.fills: list[Fill] = []
        self.positions: dict[str, Position] = {}

    def place_order(self, order: Order, market_price: Decimal) -> Fill | None:
        if order.order_id in self.orders:
            raise ValueError(f"duplicate order id: {order.order_id}")
        if market_price <= 0:
            raise ValueError("market price must be positive")
        if order.order_type is OrderType.LIMIT:
            if order.limit_price is None:
                raise ValueError("limit order requires limit_price")
            if order.side is OrderSide.BUY and market_price > order.limit_price:
                self.orders[order.order_id] = order.model_copy(update={"status": OrderStatus.NEW})
                return None
            if order.side is OrderSide.SELL and market_price < order.limit_price:
                self.orders[order.order_id] = order.model_copy(update={"status": OrderStatus.NEW})
                return None

        execution_price = market_price * (
            Decimal("1") + self.slippage if order.side is OrderSide.BUY else Decimal("1") - self.slippage
        )
        fee = execution_price * order.quantity * self.fee_rate
        fill = Fill(order_id=order.order_id, quantity=order.quantity, price=execution_price, fee=fee)
        self.orders[order.order_id] = order.model_copy(
            update={
                "status": OrderStatus.FILLED,
                "filled_quantity": order.quantity,
                "average_fill_price": execution_price,
            }
        )
        self.fills.append(fill)
        self._apply_fill(order, fill)
        return fill

    def cancel_order(self, order_id: str) -> Order:
        order = self.orders.get(order_id)
        if order is None:
            raise KeyError(order_id)
        if order.status is not OrderStatus.NEW:
            raise ValueError("only open orders can be cancelled")
        cancelled = order.model_copy(update={"status": OrderStatus.CANCELLED})
        self.orders[order_id] = cancelled
        return cancelled

    def mark_to_market(self, symbol: str, price: Decimal) -> Position | None:
        if price <= 0:
            raise ValueError("mark price must be positive")
        position = self.positions.get(symbol)
        return None if position is None else position.mark(price)

    def equity(self, marks: dict[str, Decimal] | None = None) -> Decimal:
        total = self.balance
        for symbol, position in self.positions.items():
            if marks and symbol in marks:
                total += position.quantity * marks[symbol]
        return total

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
            current.realized_pnl += (fill.price - current.average_price) * closing_qty * direction - fill.fee
            current.quantity = new_qty
            if new_qty != 0 and (old_qty > 0) != (new_qty > 0):
                current.average_price = fill.price
        self.balance -= fill.price * signed + fill.fee
        if current.quantity == 0:
            self.positions.pop(order.symbol, None)
