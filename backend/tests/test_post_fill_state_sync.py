from decimal import Decimal

import pytest

from app.brokers.base import Account, BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerPosition, BrokerSide
from app.execution.post_fill_sync import PostFillBrokerStateSynchronizer
from app.execution.risk_session import RiskSessionBaseline
from app.execution.state_sync import BrokerStateSynchronizer, StateSynchronizationError


class Store:
    def __init__(self, baseline: Decimal = Decimal("100")) -> None:
        self.baseline = baseline

    def get(self, session_id: str) -> RiskSessionBaseline:
        assert session_id == "session-1"
        return RiskSessionBaseline(session_id, self.baseline)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "filled_quantity"),
    [
        (BrokerOrderStatus.PARTIALLY_FILLED, 2),
        (BrokerOrderStatus.FILLED, 5),
    ],
)
async def test_post_fill_refreshes_broker_state_and_persists_derived_risk_snapshot(
    status: BrokerOrderStatus,
    filled_quantity: int,
) -> None:
    account = Account(account_id="broker", balance=Decimal("100000"), available_margin=Decimal("80000"))
    positions = (
        BrokerPosition(
            symbol="NIFTY",
            quantity=5,
            average_price=Decimal("100"),
            realized_pnl=Decimal("125"),
            unrealized_pnl=Decimal("10"),
        ),
    )
    refreshed = 0
    persisted: list[tuple[object, object]] = []

    async def get_account() -> Account:
        return account

    async def get_positions() -> tuple[BrokerPosition, ...]:
        nonlocal refreshed
        refreshed += 1
        return positions

    async def sink(snapshot: object, state: object) -> None:
        persisted.append((snapshot, state))

    synchronizer = PostFillBrokerStateSynchronizer(
        broker_state=BrokerStateSynchronizer(get_account, get_positions),
        baseline_store=Store(),
        session_id="session-1",
        sink=sink,
    )
    order = BrokerOrder(
        order_id="broker-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=5,
        filled_quantity=filled_quantity,
        average_price=Decimal("101"),
        status=status,
    )

    snapshot = await synchronizer.synchronize(order)

    assert refreshed == 1
    assert snapshot.balance == Decimal("100000")
    assert snapshot.position_quantity == 5
    assert snapshot.realized_pnl == Decimal("25")
    assert len(persisted) == 1
    assert persisted[0][0] == snapshot


@pytest.mark.asyncio
async def test_post_fill_propagation_fails_closed_when_sink_fails() -> None:
    account = Account(account_id="broker", balance=Decimal("100000"), available_margin=Decimal("80000"))

    async def get_account() -> Account:
        return account

    async def get_positions() -> tuple[BrokerPosition, ...]:
        return ()

    async def sink(snapshot: object, state: object) -> None:
        raise TimeoutError("sink unavailable")

    synchronizer = PostFillBrokerStateSynchronizer(
        broker_state=BrokerStateSynchronizer(get_account, get_positions),
        baseline_store=Store(),
        session_id="session-1",
        sink=sink,
    )

    order = BrokerOrder(
        order_id="broker-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=1,
        filled_quantity=1,
        average_price=Decimal("101"),
        status=BrokerOrderStatus.FILLED,
    )

    with pytest.raises(StateSynchronizationError, match="TimeoutError"):
        await synchronizer.synchronize(order)


def test_post_fill_requires_explicit_session_id() -> None:
    async def sink(snapshot: object, state: object) -> None:
        return None

    async def get_account() -> Account:
        return Account(account_id="broker", balance=Decimal("100000"), available_margin=Decimal("80000"))

    async def get_positions() -> tuple[BrokerPosition, ...]:
        return ()

    with pytest.raises(ValueError, match="session_id"):
        PostFillBrokerStateSynchronizer(
            broker_state=BrokerStateSynchronizer(get_account, get_positions),
            baseline_store=Store(),
            session_id="   ",
            sink=sink,
        )
