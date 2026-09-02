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
from app.brokers.idempotency import BrokerIdempotencyStore, IdempotencyPending
from app.execution import ControlledBrokerExecution, DeterministicExecutionGate, RiskLimits, RiskSnapshot


class TerminalRecoveryBroker:
    def __init__(self, status: BrokerOrderStatus) -> None:
        self.status = status
        self.calls = 0

    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=True)

    async def get_positions(self) -> tuple[object, ...]:
        return ()

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        return ()

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        return BrokerReconciliation(
            client_order_id=client_order_id,
            broker_status=self.status,
            matched=True,
        )

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        self.calls += 1
        return order.model_copy(update={"order_id": f"broker-{self.calls}", "status": BrokerOrderStatus.OPEN})


def make_order() -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=5,
        status=BrokerOrderStatus.NEW,
    )


def snapshot() -> RiskSnapshot:
    return RiskSnapshot(Decimal("100000"), Decimal("0"), False, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal_status", [BrokerOrderStatus.REJECTED, BrokerOrderStatus.CANCELLED])
async def test_recovery_clears_only_terminal_non_live_reservation(terminal_status: BrokerOrderStatus) -> None:
    broker = TerminalRecoveryBroker(terminal_status)
    store = BrokerIdempotencyStore()
    guarded = ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)),
        confirmation_phrase="CONFIRM-LIVE",
        idempotency_store=store,
    )
    order = make_order()
    assert store.begin(order) is None

    reconciliations = await guarded.recover((order.client_order_id,))

    assert reconciliations[0].matched
    guarded.activate("CONFIRM-LIVE")
    result = await guarded.submit(order, market_price=Decimal("100"), snapshot=snapshot())
    assert result.order_id == "broker-1"
    assert broker.calls == 1


@pytest.mark.asyncio
async def test_recovery_preserves_reservation_for_live_or_filled_order() -> None:
    broker = TerminalRecoveryBroker(BrokerOrderStatus.OPEN)
    store = BrokerIdempotencyStore()
    guarded = ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)),
        confirmation_phrase="CONFIRM-LIVE",
        idempotency_store=store,
    )
    order = make_order()
    assert store.begin(order) is None

    await guarded.recover((order.client_order_id,))
    with pytest.raises(IdempotencyPending):
        store.begin(order)
    assert broker.calls == 0
