from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrderStatus
from app.brokers.idempotency import IdempotencyPending
from app.execution import ControlledExecutionError

from test_controlled_execution import FakeBroker, execution, make_order, snapshot


class FilledBroker(FakeBroker):
    async def place_order(self, order):
        self.calls += 1
        return order.model_copy(
            update={
                "order_id": f"broker-{self.calls}",
                "filled_quantity": order.quantity,
                "average_price": Decimal("100"),
                "status": BrokerOrderStatus.FILLED,
            }
        )


@pytest.mark.asyncio
async def test_successful_fill_completes_idempotency_after_post_fill_sync() -> None:
    broker = FilledBroker()

    async def sync(result) -> None:
        return None

    guarded = execution(broker, post_fill_state_sync=sync)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    result = await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())

    assert guarded._idempotency_store.begin(make_order()) == result
    assert broker.calls == 1


@pytest.mark.asyncio
async def test_failed_post_fill_sync_leaves_idempotency_pending() -> None:
    broker = FilledBroker()

    async def sync(result) -> None:
        raise TimeoutError("provider refresh failed")

    guarded = execution(broker, post_fill_state_sync=sync)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    with pytest.raises(ControlledExecutionError, match="post-fill broker state synchronization failed"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())

    with pytest.raises(IdempotencyPending):
        guarded._idempotency_store.begin(make_order())
    assert broker.calls == 1
