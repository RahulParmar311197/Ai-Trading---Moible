from decimal import Decimal

import pytest

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerReconciliation, BrokerSide
from app.brokers.idempotency import BrokerIdempotencyStore
from app.execution import ControlledBrokerExecution, ControlledExecutionError, DeterministicExecutionGate, RiskLimits


class UnexpectedLiveOrderBroker:
    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=True)

    async def get_positions(self) -> tuple[object, ...]:
        return ()

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        return (
            BrokerOrder(
                order_id="broker-manual-1",
                client_order_id="manual-1",
                symbol="NIFTY",
                side=BrokerSide.BUY,
                order_type=BrokerOrderType.MARKET,
                quantity=1,
                status=BrokerOrderStatus.OPEN,
            ),
        )

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        raise AssertionError("unexpected order must block before per-order reconciliation")

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        raise AssertionError("unexpected order must block before submission")


class TerminalOrderBroker(UnexpectedLiveOrderBroker):
    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        return (
            BrokerOrder(
                order_id="broker-history-1",
                client_order_id="history-1",
                symbol="NIFTY",
                side=BrokerSide.BUY,
                order_type=BrokerOrderType.MARKET,
                quantity=1,
                status=BrokerOrderStatus.FILLED,
            ),
        )

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        return BrokerReconciliation(
            client_order_id=client_order_id,
            local_status=BrokerOrderStatus.FILLED,
            broker_status=BrokerOrderStatus.FILLED,
            matched=True,
        )


def make_execution(broker, events):
    return ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(
            RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)
        ),
        confirmation_phrase="CONFIRM-LIVE",
        audit_sink=events.append,
        idempotency_store=BrokerIdempotencyStore(),
    )


@pytest.mark.asyncio
async def test_recovery_blocks_unexpected_broker_live_order() -> None:
    events = []
    guarded = make_execution(UnexpectedLiveOrderBroker(), events)

    with pytest.raises(ControlledExecutionError, match="unexpected broker live order"):
        await guarded.recover(("client-1",))

    assert not guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    assert events[-1].event_type == "RECONCILIATION_REQUIRED"
    assert events[-1].client_order_id == "manual-1"


@pytest.mark.asyncio
async def test_recovery_does_not_treat_terminal_broker_history_as_unexpected_live_order() -> None:
    events = []
    guarded = make_execution(TerminalOrderBroker(), events)

    reconciliations = await guarded.recover(("history-1",))

    assert reconciliations[0].matched
    assert guarded.started
    assert not guarded.active
    assert guarded.kill_switch_active
    assert events[-1].event_type == "RECOVERY_HEALTHY"
