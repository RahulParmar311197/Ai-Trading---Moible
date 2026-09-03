from decimal import Decimal

import pytest

from app.brokers.base import Account
from app.execution.gate import RiskSnapshot
from app.execution.risk_state import PostgresExecutionRiskStateSink
from app.execution.state_sync import BrokerRiskState


class ExecutorStub:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, statement, params):
        self.calls.append((statement, params))


@pytest.mark.asyncio
async def test_risk_state_sink_persists_explicit_session() -> None:
    executor = ExecutorStub()
    sink = PostgresExecutionRiskStateSink(executor, session_id="2026-09-03")
    state = BrokerRiskState(
        account=Account(account_id="demo", balance=Decimal("100000"), available_margin=Decimal("90000")),
        positions=(),
        realized_pnl=Decimal("125"),
        unrealized_pnl=Decimal("25"),
    )
    snapshot = RiskSnapshot(
        balance=Decimal("100000"),
        realized_pnl=Decimal("125"),
        halted=False,
        position_quantity=0,
    )

    await sink(snapshot, state)

    assert len(executor.calls) == 1
    statement, params = executor.calls[0]
    assert "execution_risk_state" in statement
    assert "ON CONFLICT (session_id)" in statement
    assert params["session_id"] == "2026-09-03"
    assert params["realized_pnl"] == Decimal("125")
    assert params["position_quantity"] == 0
