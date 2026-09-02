from decimal import Decimal

import pytest

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerPosition, BrokerSide
from app.brokers.idempotency import BrokerIdempotencyStore
from app.execution import ControlledBrokerExecution, ControlledExecutionError, DeterministicExecutionGate, RiskLimits, RiskSnapshot


class ConfirmationBroker:
    def __init__(self, result_factory):
        self.calls = 0
        self.result_factory = result_factory

    async def authenticate(self):
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=True)

    async def get_positions(self):
        return (BrokerPosition(symbol="NIFTY", quantity=0, average_price=Decimal("100")),)

    async def place_order(self, order):
        self.calls += 1
        return self.result_factory(order)


def order() -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=5,
        status=BrokerOrderStatus.NEW,
    )


def execution(broker):
    return ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)),
        confirmation_phrase="CONFIRM-LIVE",
        idempotency_store=BrokerIdempotencyStore(),
    )


def snapshot() -> RiskSnapshot:
    return RiskSnapshot(Decimal("100000"), Decimal("0"), False, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field, value, reason",
    [
        ("client_order_id", "other-client", "client order id mismatch"),
        ("symbol", "BANKNIFTY", "symbol mismatch"),
        ("side", BrokerSide.SELL, "side mismatch"),
        ("order_type", BrokerOrderType.LIMIT, "order type mismatch"),
        ("quantity", 4, "quantity mismatch"),
    ],
)
async def test_confirmation_identity_must_match_submission(field, value, reason):
    broker = ConfirmationBroker(lambda submitted: submitted.model_copy(update={"order_id": "broker-1", field: value}))
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    with pytest.raises(ControlledExecutionError, match=reason):
        await guarded.submit(order(), market_price=Decimal("100"), snapshot=snapshot())

    assert broker.calls == 1
    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, filled_quantity, reason",
    [
        (BrokerOrderStatus.FILLED, 0, "incomplete fill quantity"),
        (BrokerOrderStatus.PARTIALLY_FILLED, 0, "invalid fill quantity"),
        (BrokerOrderStatus.PARTIALLY_FILLED, 5, "invalid fill quantity"),
    ],
)
async def test_confirmation_fill_quantity_must_match_status(status, filled_quantity, reason):
    broker = ConfirmationBroker(
        lambda submitted: submitted.model_copy(
            update={"order_id": "broker-1", "status": status, "filled_quantity": filled_quantity}
        )
    )
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    with pytest.raises(ControlledExecutionError, match=reason):
        await guarded.submit(order(), market_price=Decimal("100"), snapshot=snapshot())

    assert not guarded.started
    assert guarded.kill_switch_active


@pytest.mark.asyncio
async def test_confirmation_rejects_filled_quantity_above_order_quantity():
    broker = ConfirmationBroker(lambda submitted: submitted.model_copy(update={"order_id": "broker-1", "filled_quantity": 6}))
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    with pytest.raises(ControlledExecutionError, match="exceeds order quantity"):
        await guarded.submit(order(), market_price=Decimal("100"), snapshot=snapshot())

    assert not guarded.started
    assert guarded.kill_switch_active


@pytest.mark.asyncio
@pytest.mark.parametrize("average_price", [Decimal("NaN"), Decimal("Infinity"), Decimal("0"), Decimal("-1")])
async def test_confirmation_rejects_invalid_average_price(average_price):
    broker = ConfirmationBroker(lambda submitted: submitted.model_copy(update={"order_id": "broker-1", "average_price": average_price}))
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    with pytest.raises(ControlledExecutionError, match="average price"):
        await guarded.submit(order(), market_price=Decimal("100"), snapshot=snapshot())

    assert not guarded.started
    assert guarded.kill_switch_active
