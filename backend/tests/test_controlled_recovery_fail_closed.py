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
from app.execution import (
    ControlledBrokerExecution,
    ControlledExecutionError,
    DeterministicExecutionGate,
    RiskLimits,
    RiskSnapshot,
)


class RecoveryDisconnectBroker:
    def __init__(self, failure_point: str) -> None:
        self.failure_point = failure_point

    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=True)

    async def get_positions(self) -> tuple[object, ...]:
        if self.failure_point == "positions":
            raise ConnectionError("provider session leaked secret endpoint details")
        return ()

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        if self.failure_point == "orders":
            raise TimeoutError("provider timeout with sensitive response details")
        return ()

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        if self.failure_point == "reconcile":
            raise ConnectionError("provider reconciliation payload contained sensitive data")
        return BrokerReconciliation(
            client_order_id=client_order_id,
            local_status=BrokerOrderStatus.NEW,
            broker_status=BrokerOrderStatus.OPEN,
            matched=True,
            reason=None,
        )


def make_execution(broker: RecoveryDisconnectBroker, events: list) -> ControlledBrokerExecution:
    return ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(
            RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)
        ),
        confirmation_phrase="CONFIRM-LIVE",
        idempotency_store=BrokerIdempotencyStore(),
        audit_sink=events.append,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_point", ["positions", "orders", "reconcile"])
async def test_recovery_provider_failure_fails_closed_and_sanitizes_audit(failure_point: str) -> None:
    events = []
    guarded = make_execution(RecoveryDisconnectBroker(failure_point), events)

    with pytest.raises((ConnectionError, TimeoutError)):
        await guarded.recover(("client-1",))

    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    assert events[-1].event_type == "RECOVERY_REJECTED"
    assert events[-1].reason == f"broker recovery failed: {'TimeoutError' if failure_point == 'orders' else 'ConnectionError'}"
    assert "sensitive" not in events[-1].reason
    assert "secret" not in events[-1].reason
    assert "payload" not in events[-1].reason


@pytest.mark.asyncio
async def test_recovery_failure_never_auto_reactivates_after_broker_disconnect() -> None:
    events = []
    guarded = make_execution(RecoveryDisconnectBroker("reconcile"), events)

    with pytest.raises(ConnectionError):
        await guarded.recover(("client-1",))

    with pytest.raises(ControlledExecutionError, match="startup"):
        await guarded.submit(
            BrokerOrder(
                order_id="local-1",
                client_order_id="client-1",
                symbol="NIFTY",
                side=BrokerSide.BUY,
                order_type=BrokerOrderType.MARKET,
                quantity=1,
                status=BrokerOrderStatus.NEW,
            ),
            market_price=Decimal("100"),
            snapshot=RiskSnapshot(Decimal("100000"), Decimal("0"), False, 0),
        )
