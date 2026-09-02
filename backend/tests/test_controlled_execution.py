from decimal import Decimal

import pytest

from app.brokers.base import (
    BrokerAuthentication,
    BrokerOrder,
    BrokerOrderStatus,
    BrokerOrderType,
    BrokerReconciliation,
    BrokerSide,
)
from app.brokers.idempotency import BrokerIdempotencyStore
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


class FailingBroker(FakeBroker):
    async def authenticate(self) -> BrokerAuthentication:
        raise ConnectionError("broker unavailable")


class SubmissionFailBroker(FakeBroker):
    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        self.calls += 1
        raise TimeoutError("sensitive provider timeout detail")


class ReauthenticationFailBroker(FakeBroker):
    def __init__(self) -> None:
        super().__init__()
        self.auth_calls = 0

    async def authenticate(self) -> BrokerAuthentication:
        self.auth_calls += 1
        if self.auth_calls == 1:
            return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=True)
        raise ConnectionError("re-authentication unavailable")


class RecoveryBroker(FakeBroker):
    def __init__(self, *, matched: bool = True, recovery_auth: bool = True) -> None:
        super().__init__()
        self.matched = matched
        self.recovery_auth = recovery_auth
        self.positions_calls = 0
        self.orders_calls = 0
        self.reconcile_calls: list[str] = []

    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=self.recovery_auth)

    async def get_positions(self) -> tuple[object, ...]:
        self.positions_calls += 1
        return ()

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        self.orders_calls += 1
        return ()

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        self.reconcile_calls.append(client_order_id)
        return BrokerReconciliation(
            client_order_id=client_order_id,
            local_status=BrokerOrderStatus.NEW,
            broker_status=BrokerOrderStatus.OPEN if self.matched else BrokerOrderStatus.REJECTED,
            matched=self.matched,
            reason=None if self.matched else "broker/local status mismatch",
        )


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
        idempotency_store=BrokerIdempotencyStore(),
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


@pytest.mark.asyncio
async def test_startup_failure_is_audited_without_exposing_provider_error() -> None:
    events = []
    guarded = execution(FailingBroker(), audit_sink=events.append)
    with pytest.raises(ConnectionError, match="broker unavailable"):
        await guarded.startup()
    assert events[-1].event_type == "STARTUP_REJECTED"
    assert events[-1].reason == "broker authentication failed: ConnectionError"
    assert "broker unavailable" not in events[-1].reason
    assert not guarded.started
    assert guarded.kill_switch_active


@pytest.mark.asyncio
async def test_broker_submission_failure_fails_closed_and_is_audited_without_leaking_exception_details() -> None:
    events = []
    broker = SubmissionFailBroker()
    guarded = execution(broker, audit_sink=events.append)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")
    with pytest.raises(TimeoutError, match="sensitive provider timeout detail"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())
    assert broker.calls == 1
    assert [event.event_type for event in events[-2:]] == ["BROKER_SUBMISSION_ATTEMPTED", "BROKER_SUBMISSION_FAILED"]
    assert events[-1].reason == "broker submission failed: TimeoutError; execution fail-closed pending reconciliation"
    assert "sensitive provider timeout detail" not in events[-1].reason
    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    with pytest.raises(ControlledExecutionError, match="startup"):
        await guarded.submit(make_order(6), market_price=Decimal("100"), snapshot=snapshot())
    assert broker.calls == 1


@pytest.mark.asyncio
async def test_failed_reauthentication_disables_previously_active_execution() -> None:
    events = []
    broker = ReauthenticationFailBroker()
    guarded = execution(broker, audit_sink=events.append)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")
    assert guarded.active

    with pytest.raises(ConnectionError, match="re-authentication unavailable"):
        await guarded.startup()

    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    assert events[-1].event_type == "STARTUP_REJECTED"
    with pytest.raises(ControlledExecutionError, match="startup"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())


@pytest.mark.asyncio
async def test_recovery_refreshes_state_and_requires_explicit_reactivation() -> None:
    broker = RecoveryBroker()
    events = []
    guarded = execution(broker, audit_sink=events.append)
    await guarded.startup()
    guarded.activate("CONFIRM-LIVE")
    assert guarded.active

    reconciliations = await guarded.recover(("client-1",))

    assert len(reconciliations) == 1
    assert reconciliations[0].matched
    assert broker.positions_calls == 1
    assert broker.orders_calls == 1
    assert broker.reconcile_calls == ["client-1"]
    assert guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    assert events[-1].event_type == "RECOVERY_HEALTHY"
    with pytest.raises(ControlledExecutionError, match="not activated"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())

    guarded.activate("CONFIRM-LIVE")
    assert guarded.active


@pytest.mark.asyncio
async def test_recovery_mismatch_stays_fail_closed_and_does_not_resume() -> None:
    broker = RecoveryBroker(matched=False)
    events = []
    guarded = execution(broker, audit_sink=events.append)

    with pytest.raises(ControlledExecutionError, match="reconciliation mismatch"):
        await guarded.recover(("client-1",))

    assert broker.positions_calls == 1
    assert broker.orders_calls == 1
    assert broker.reconcile_calls == ["client-1"]
    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    assert events[-1].event_type == "RECONCILIATION_REQUIRED"

    with pytest.raises(ControlledExecutionError, match="startup"):
        await guarded.submit(make_order(), market_price=Decimal("100"), snapshot=snapshot())


@pytest.mark.asyncio
async def test_recovery_requires_provider_reconciliation_boundary() -> None:
    events = []
    guarded = execution(FakeBroker(), audit_sink=events.append)

    with pytest.raises(ControlledExecutionError, match="reconciliation boundary"):
        await guarded.recover()

    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    assert events[-1].event_type == "RECOVERY_REJECTED"
