from decimal import Decimal

import pytest

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerPosition, BrokerReconciliation, BrokerSide
from app.brokers.idempotency import BrokerIdempotencyStore, IdempotencyPending
from app.execution import ControlledBrokerExecution, DeterministicExecutionGate, RiskLimits


class PartialRecoveryBroker:
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
            broker_status=BrokerOrderStatus.PARTIALLY_FILLED,
            matched=True,
            broker_order=self.broker_order,
        )

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        self.place_calls += 1
        raise AssertionError("unresolved partial fill must block duplicate submission")


@pytest.mark.asyncio
async def test_recovered_partial_fill_remains_pending_and_blocks_resubmission() -> None:
    submitted = BrokerOrder(
        order_id="local-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=5,
        status=BrokerOrderStatus.NEW,
    )
    partial = submitted.model_copy(
        update={
            "order_id": "broker-1",
            "filled_quantity": 2,
            "average_price": Decimal("100"),
            "status": BrokerOrderStatus.PARTIALLY_FILLED,
        }
    )
    store = BrokerIdempotencyStore()
    assert store.begin(submitted) is None
    broker = PartialRecoveryBroker(partial)
    execution = ControlledBrokerExecution(
        broker,
        DeterministicExecutionGate(RiskLimits(max_order_notional=Decimal("1000"), max_position_quantity=10)),
        confirmation_phrase="CONFIRM-LIVE",
        idempotency_store=store,
    )

    result = await execution.recover(("client-1",))

    assert result[0].broker_order == partial
    assert execution.started
    assert execution.kill_switch_active
    execution.activate("CONFIRM-LIVE")

    with pytest.raises(IdempotencyPending, match="unresolved broker submission"):
        await execution.submit(submitted, market_price=Decimal("100"), snapshot=__import__("app.execution", fromlist=["RiskSnapshot"]).RiskSnapshot(Decimal("100000"), Decimal("0"), False, 0))

    assert broker.place_calls == 0
