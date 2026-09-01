from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.idempotency import BrokerIdempotencyStore, IdempotencyConflict, IdempotentBroker


class FakeBroker:
    def __init__(self) -> None:
        self.calls = 0

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        self.calls += 1
        return order.model_copy(update={"status": BrokerOrderStatus.OPEN, "order_id": f"broker-{self.calls}"})


def make_order(quantity: int = 10) -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=quantity,
        status=BrokerOrderStatus.NEW,
    )


@pytest.mark.asyncio
async def test_duplicate_client_order_id_returns_original_result() -> None:
    broker = FakeBroker()
    guarded = IdempotentBroker(broker)
    order = make_order()

    first = await guarded.place_order(order)
    second = await guarded.place_order(order)

    assert first == second
    assert first.order_id == "broker-1"
    assert broker.calls == 1


@pytest.mark.asyncio
async def test_conflicting_reuse_is_rejected() -> None:
    broker = FakeBroker()
    guarded = IdempotentBroker(broker)
    await guarded.place_order(make_order(10))

    with pytest.raises(IdempotencyConflict):
        await guarded.place_order(make_order(11))

    assert broker.calls == 1


@pytest.mark.asyncio
async def test_failed_submission_can_be_retried() -> None:
    class FailingOnceBroker(FakeBroker):
        async def place_order(self, order: BrokerOrder) -> BrokerOrder:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("provider unavailable")
            return order.model_copy(update={"status": BrokerOrderStatus.OPEN, "order_id": "broker-2"})

    broker = FailingOnceBroker()
    guarded = IdempotentBroker(broker)
    order = make_order()

    with pytest.raises(RuntimeError):
        await guarded.place_order(order)

    result = await guarded.place_order(order)
    assert result.order_id == "broker-2"
    assert broker.calls == 2


def test_fingerprint_is_deterministic_and_order_sensitive() -> None:
    first = BrokerIdempotencyStore.fingerprint(make_order(10))
    second = BrokerIdempotencyStore.fingerprint(make_order(10))
    different = BrokerIdempotencyStore.fingerprint(make_order(11))

    assert first == second
    assert first != different
