from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder
from app.execution.autonomous import ExecutionIntent
from app.execution.autonomous_execution import AutonomousExecutionBridgeError, submit_autonomous_intent
from app.execution.gate import ExecutionDecision, RiskSnapshot
from app.execution.portfolio_risk import PortfolioRiskAssessment


def denied_execution_intent() -> ExecutionIntent:
    return ExecutionIntent(
        session_id="session-1",
        strategy_id="strategy-1",
        symbol="NIFTY",
        side="BUY",
        quantity=1,
        market_price=Decimal("100"),
        risk_decision=ExecutionDecision(approved=False, reason="execution risk limit"),
        portfolio_risk=PortfolioRiskAssessment(
            gross_exposure=Decimal("100"),
            net_exposure=Decimal("100"),
            total_realized_pnl=Decimal("0"),
            total_unrealized_pnl=Decimal("0"),
            single_position_notional=(("NIFTY", Decimal("100")),),
            correlated_pairs=(),
            approved=True,
            reasons=(),
        ),
        generated_by_ai=True,
    )


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[BrokerOrder] = []

    async def submit(self, order: BrokerOrder, *, market_price: object, snapshot: RiskSnapshot) -> BrokerOrder:
        self.calls.append(order)
        return order


@pytest.mark.asyncio
async def test_execution_risk_denied_intent_never_reaches_controlled_executor() -> None:
    executor = RecordingExecutor()
    snapshot = RiskSnapshot(balance=Decimal("100000"), realized_pnl=Decimal("0"), halted=False)

    with pytest.raises(AutonomousExecutionBridgeError, match="execution-risk-approved"):
        await submit_autonomous_intent(
            executor,
            denied_execution_intent(),
            client_order_id="auto-risk-gate-1",
            snapshot=snapshot,
        )

    assert executor.calls == []
