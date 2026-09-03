from decimal import Decimal

import pytest

from app.execution.autonomous import AutonomousDecision, ExecutionIntent
from app.execution.autonomous_handoff import AutonomousIntentHandoffError, build_broker_order
from app.execution.gate import ExecutionDecision
from app.execution.portfolio_risk import PortfolioRiskAssessment


def approved_intent() -> ExecutionIntent:
    gate = ExecutionDecision(approved=True, reason="approved")
    portfolio = PortfolioRiskAssessment(
        gross_exposure=Decimal("100"),
        net_exposure=Decimal("100"),
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        per_symbol_notional={"NIFTY": Decimal("100")},
        correlated_pairs=(),
        approved=True,
        reasons=(),
    )
    return ExecutionIntent(
        session_id="session-1",
        strategy_id="strategy-1",
        symbol="NIFTY",
        side="BUY",
        quantity=1,
        market_price=Decimal("100"),
        risk_decision=gate,
        portfolio_risk=portfolio,
        generated_by_ai=True,
    )


def test_approved_intent_materializes_market_order_without_submission() -> None:
    order = build_broker_order(approved_intent(), client_order_id="auto-123")

    assert order.client_order_id == "auto-123"
    assert order.order_id == "auto-123"
    assert order.symbol == "NIFTY"
    assert order.side.value == "BUY"
    assert order.order_type.value == "MARKET"
    assert order.quantity == 1
    assert order.average_price is None
    assert order.status.value == "NEW"


def test_unapproved_intent_is_rejected() -> None:
    intent = approved_intent()
    rejected = ExecutionIntent(
        session_id=intent.session_id,
        strategy_id=intent.strategy_id,
        symbol=intent.symbol,
        side=intent.side,
        quantity=intent.quantity,
        market_price=intent.market_price,
        risk_decision=ExecutionDecision(approved=False, reason="risk halt"),
        portfolio_risk=intent.portfolio_risk,
        generated_by_ai=intent.generated_by_ai,
    )

    with pytest.raises(AutonomousIntentHandoffError, match="approved deterministic intent"):
        build_broker_order(rejected, client_order_id="auto-123")


def test_client_order_id_is_explicitly_required() -> None:
    with pytest.raises(AutonomousIntentHandoffError, match="client order id"):
        build_broker_order(approved_intent(), client_order_id="")


def test_market_order_handoff_does_not_turn_reference_price_into_fill_price() -> None:
    intent = approved_intent()
    order = build_broker_order(intent, client_order_id="auto-124")

    assert order.average_price is None
    assert intent.market_price == Decimal("100")
