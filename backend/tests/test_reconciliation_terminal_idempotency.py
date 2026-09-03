from decimal import Decimal

import pytest

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerPosition, BrokerReconciliation, BrokerSide
from app.brokers.idempotency import BrokerIdempotencyStore
from app.execution import ControlledBrokerExecution, DeterministicExecutionGate, RiskLimits, RiskSnapshot


class FilledRecoveryBroker:
    def __init__(self, broker_order: BrokerOrder) -> None:
        self.broker_order = broker_order
        self.place_calls = 0

    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(provider="fake", account_id="account-1", authenticated=True)

    async def get_positions(self) -> tuple[BrokerPosition, ...]:
        return ()

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        return (self.broker_order,)

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        return BrokerReconciliation(
            client_order_id=client_order_id,
            broker_status=self.broker_order.status,
            matched=True,
            broker_order=self.broker_order,
        )

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        self.place_calls += 1
        return self.broker_order


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


@pytest.mark.asyncio
async def test_filled_reconciliation_completes_idempotency_and_replays_without_resubmission() -> None:
    submitted = make_order()
    filled = submitted.model_copy(update={"order_id": "broker-1", "filled_quantity": 5, "average_price": Decimal("100"), "status": BrokerOrderStatus.FILLED})
    store = BrokerIdempotencyStore()
    assert store.begin(submitted) is None
    broker = FilledRecoveryBroker(filled)
    execution = ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)),
        confirmation_phrase="CONFIRM-LIVE",
        idempotency_store=store,
    )

    result = await execution.recover(("client-1",))
    assert result[0].broker_order == filled
    assert not execution.active
    execution.activate("CONFIRM-LIVE")
    replay = await execution.submit(submitted, market_price=Decimal("100"), snapshot=RiskSnapshot(Decimal("100000"), Decimal("0"), False, 0))

    assert replay == filled
    assert broker.place_calls == 0
