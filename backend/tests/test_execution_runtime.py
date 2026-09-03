from decimal import Decimal

from app.brokers.base import Account, BrokerPosition
from app.execution.gate import RiskLimits
from app.execution.runtime import StaticTradingSessionIdentityProvider, build_execution_runtime


class BrokerStub:
    async def authenticate(self):
        raise AssertionError("runtime composition must not authenticate the broker")

    async def get_account(self):
        return Account(account_id="test", balance=Decimal("100000"), available_margin=Decimal("100000"))

    async def get_positions(self):
        return (
            BrokerPosition(
                symbol="NSE_EQ|TEST",
                quantity=0,
                average_price=Decimal("0"),
            ),
        )

    async def get_orders(self):
        return ()

    async def reconcile_order(self, client_order_id):
        raise AssertionError("runtime composition must not reconcile the broker")

    async def place_order(self, order):
        raise AssertionError("runtime composition must not submit an order")


def test_runtime_composition_is_fail_closed_and_does_not_start_broker() -> None:
    runtime = build_execution_runtime(
        BrokerStub(),
        session_identity_provider=StaticTradingSessionIdentityProvider("session-1"),
        risk_limits=RiskLimits(
            max_order_notional=Decimal("100000"),
            max_position_quantity=100,
            max_daily_loss=Decimal("5000"),
        ),
        confirmation_phrase="CONFIRM LIVE TRADING",
        risk_state_sink=lambda snapshot, state: None,
        database_url="sqlite:///:memory:",
    )

    assert runtime.executor.started is False
    assert runtime.executor.active is False
    assert runtime.executor.kill_switch_active is True
    assert runtime.sessions is not None
