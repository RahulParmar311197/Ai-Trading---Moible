from decimal import Decimal

from app.paper import Order, OrderSide, OrderType, PaperBroker


class RecordingRepository:
    def __init__(self) -> None:
        self.orders = []
        self.fills = []
        self.positions = []
        self.deleted = []
        self.audit = []
        self.state = None

    def save_order(self, order):
        self.orders.append(order)

    def save_fill(self, fill):
        self.fills.append(fill)

    def save_position(self, position):
        self.positions.append(position)

    def delete_position(self, symbol):
        self.deleted.append(symbol)

    def save_state(self, balance, realized_pnl_total, halted):
        self.state = {
            "balance": balance,
            "realized_pnl_total": realized_pnl_total,
            "halted": halted,
        }

    def load_orders(self):
        latest = {}
        for order in self.orders:
            latest[order.order_id] = order
        return list(latest.values())

    def load_fills(self):
        return list(self.fills)

    def load_positions(self):
        latest = {}
        for position in self.positions:
            latest[position.symbol] = position
        for symbol in self.deleted:
            latest.pop(symbol, None)
        return list(latest.values())

    def load_state(self):
        return self.state

    def append_audit(self, event_type, entity_id, payload):
        self.audit.append((event_type, entity_id, payload))


def test_paper_execution_persists_order_fill_position_and_audit() -> None:
    repository = RecordingRepository()
    broker = PaperBroker(repository=repository)
    order = Order(
        order_id="1",
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=2,
    )

    fill = broker.place_order(order, Decimal("100"))

    assert fill is not None
    assert repository.orders[-1].status.value == "FILLED"
    assert repository.fills[-1].quantity == 2
    assert repository.positions[-1].quantity == 2
    assert repository.audit[-1][0] == "ORDER_FILLED"


def test_closing_paper_position_persists_delete_and_audit() -> None:
    repository = RecordingRepository()
    broker = PaperBroker(repository=repository)
    broker.place_order(
        Order(order_id="1", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=1),
        Decimal("100"),
    )
    broker.place_order(
        Order(order_id="2", symbol="NIFTY", side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=1),
        Decimal("110"),
    )

    assert repository.deleted == ["NIFTY"]
    assert repository.audit[-1][0] == "ORDER_FILLED"


def test_paper_broker_restores_open_state_after_restart() -> None:
    repository = RecordingRepository()
    broker = PaperBroker(repository=repository, starting_balance=Decimal("1000"))
    broker.place_order(
        Order(order_id="1", symbol="NIFTY", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=4),
        Decimal("100"),
        fill_quantity=2,
    )
    broker.kill_switch()

    restored = PaperBroker.from_repository(repository, starting_balance=Decimal("1000"))

    assert restored.balance == Decimal("800")
    assert restored.realized_pnl_total == Decimal("0")
    assert restored.halted is True
    assert restored.orders["1"].status.value == "PARTIALLY_FILLED"
    assert restored.orders["1"].filled_quantity == 2
    assert restored.fills[0].quantity == 2
    assert restored.positions["NIFTY"].quantity == 2
