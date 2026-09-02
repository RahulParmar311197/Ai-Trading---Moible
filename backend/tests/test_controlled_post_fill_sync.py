from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrderStatus
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
async def test_filled_confirmation_requires_post_fill_state_sync() -> None:
    broker = FilledBroker()
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    with pytest.raises(ControlledExecutionError, match="post-fill broker state synchronization is required"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())

    assert broker.calls == 1
    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active


@pytest.mark.asyncio
async def test_filled_confirmation_invokes_post_fill_state_sync() -> None:
    broker = FilledBroker()
    synchronized = []

    async def sync(result) -> None:
        synchronized.append(result)

    guarded = execution(broker, post_fill_state_sync=sync)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    result = await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())

    assert result.status is BrokerOrderStatus.FILLED
    assert synchronized == [result]
    assert guarded.active


@pytest.mark.asyncio
async def test_post_fill_state_sync_failure_fails_closed() -> None:
    broker = FilledBroker()

    async def sync(result) -> None:
        raise TimeoutError("provider refresh failed")

    guarded = execution(broker, post_fill_state_sync=sync)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")

    with pytest.raises(ControlledExecutionError, match="post-fill broker state synchronization failed"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())

    assert broker.calls == 1
    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
