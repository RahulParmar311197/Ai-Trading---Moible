from decimal import Decimal

import pytest

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.execution import ControlledBrokerExecution, ControlledExecutionError, DeterministicExecutionGate, RiskLimits, RiskSnapshot


class FakeBroker:
    def __init__(self, authenticated: bool = True) -> None:
        self.calls = 0
        self.authenticated = authenticated

    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=self.authenticated)

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        self.calls += 1
        return order.model_copy(update={"order_id": f"broker-{self.calls}", "status": BrokerOrderStatus.OPEN})


def make_order(quantity: int = 5) -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=quantity,
        status=BrokerOrderStatus.NEW,
    )


def snapshot(**changes) -> RiskSnapshot:
    value = RiskSnapshot(Decimal("100000"), Decimal("0"), False, 0)
    return value.__class__(**{**value.__dict__, **changes})


def execution(broker: FakeBroker, **kwargs) -> ControlledBrokerExecution:
    return ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)),
        confirmation_phrase="CONFIRM-LIVE",
        **kwargs,
    )


@pytest.mark.asyncio
async def test_construction_is_inert_and_startup_is_required() -> None:
    broker = FakeBroker()
    guarded = execution(broker)
    with pytest.raises(ControlledExecutionError, match="startup"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())
    assert broker.calls == 0
    assert not guarded.started


@pytest.mark.asyncio
async def test_startup_rejects_unauthenticated_broker_and_stays_fail_closed() -> None:
    guarded = execution(FakeBroker(authenticated=False))
    with pytest.raises(ControlledExecutionError, match="not authenticated"):
        await guarded.startup()
    assert not guarded.started
    assert guarded.kill_switch_active


@pytest.mark.asyncio
async def test_startup_never_activates_order_mutation() -> None:
    guarded = execution(FakeBroker())
    authentication = await guarded.startup()
    assert authentication.authenticated
    assert guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active


def test_activation_requires_exact_confirmation_and_kill_switch() -> None:
    guarded = execution(FakeBroker())
    with pytest.raises(ControlledExecutionError, match="startup"):
        guarded.activate("CONFIRM-LIVE")


@pytest.mark.asyncio
async def test_activation_requires_exact_confirmation_after_startup() -> None:
    guarded = execution(FakeBroker())
    await guarded.startup()
    with pytest.raises(ControlledExecutionError, match="confirmation"):
        guarded.activate("wrong")
    assert not guarded.active
    guarded.activate("CONFIRM-LIVE")
    assert guarded.active
    guarded.trip_kill_switch("operator stop")
    assert not guarded.active


@pytest.mark.asyncio
async def test_risk_rejection_happens_before_broker_call() -> None:
    broker = FakeBroker()
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")
    with pytest.raises(ControlledExecutionError, match="maximum notional"):
        await guarded.submit(make_order(11), market_price=Decimal("100"), snapshot=snapshot())
    assert broker.calls == 0


@pytest.mark.asyncio
async def test_approved_order_reaches_broker_once_and_duplicate_is_idempotent() -> None:
    broker = FakeBroker()
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")
    first = await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())
    second = await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())
    assert first.order_id == "broker-1"
    assert second == first
    assert broker.calls == 1


@pytest.mark.asyncio
async def test_kill_switch_blocks_after_activation() -> None:
    broker = FakeBroker()
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")
    guarded.trip_kill_switch("emergency stop")
    with pytest.raises(ControlledExecutionError, match="kill switch"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())
    assert broker.calls == 0


@pytest.mark.asyncio
async def test_shutdown_fails_closed_and_blocks_future_submission() -> None:
    broker = FakeBroker()
    guarded = execution(broker)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")
    await guarded.shutdown("application shutdown")
    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    with pytest.raises(ControlledExecutionError, match="startup"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())
    assert broker.calls == 0
