from decimal import Decimal

from app.paper import Order, OrderSide, OrderType, PaperBroker


class RecordingRepository:
    def __init__(self) -> None:
        self.orders = []
        self.fills = []
        self.positions = []
        self.deleted = []
        self.audit = []

    def save_order(self, order):
        self.orders.append(order)

    def save_fill(self, fill):
        self.fills.append(fill)

    def save_position(self, position):
        self.positions.append(position)

    def delete_position(self, symbol):
        self.deleted.append(symbol)

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
