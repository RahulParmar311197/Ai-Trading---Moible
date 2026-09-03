from decimal import Decimal

import pytest

from app.execution.portfolio_risk import PortfolioPosition, PortfolioRiskError, PortfolioRiskLimits, assess_portfolio


def limits(**overrides):
    values = {"max_gross_exposure": Decimal("100000"), "max_net_exposure": Decimal("100000"), "max_single_position_notional": Decimal("100000"), "max_pair_correlation": Decimal("0.90")}
    values.update(overrides)
    return PortfolioRiskLimits(**values)


def position(symbol, quantity, price, returns=()):
    return PortfolioPosition(symbol=symbol, quantity=Decimal(str(quantity)), mark_price=Decimal(str(price)), returns=tuple(Decimal(str(value)) for value in returns))


def test_assessment_aggregates_gross_net_and_pnl():
    result = assess_portfolio([position("LONG", 10, 100), position("SHORT", -4, 50)], limits())
    assert result.gross_exposure == Decimal("1200")
    assert result.net_exposure == Decimal("800")
    assert result.approved


def test_single_position_limit_fails_closed():
    result = assess_portfolio([position("NIFTY", 10, 1000)], limits(max_single_position_notional=Decimal("9000")))
    assert not result.approved
    assert "single position exposure limit exceeded: NIFTY" in result.reasons


def test_gross_and_net_limits_are_independent():
    result = assess_portfolio([position("A", 100, 100), position("B", -100, 90)], limits(max_gross_exposure=Decimal("10000"), max_net_exposure=Decimal("2000")))
    assert result.gross_exposure == Decimal("19000")
    assert result.net_exposure == Decimal("1000")
    assert "gross exposure limit exceeded" in result.reasons
    assert "net exposure limit exceeded" not in result.reasons


def test_high_positive_correlation_is_reported_and_rejects():
    result = assess_portfolio([position("A", 1, 100, [1, 2, 3, 4]), position("B", 1, 100, [2, 4, 6, 8])], limits(max_pair_correlation=Decimal("0.90")))
    assert not result.approved
    assert len(result.correlated_pairs) == 1
    assert result.correlated_pairs[0][:2] == ("A", "B")


def test_duplicate_symbols_are_rejected():
    with pytest.raises(PortfolioRiskError, match="duplicate symbols"):
        assess_portfolio([position("A", 1, 10), position("A", 2, 10)], limits())


def test_undefined_correlation_history_is_rejected():
    with pytest.raises(PortfolioRiskError, match="correlation is undefined"):
        assess_portfolio([position("A", 1, 10, [1, 1, 1]), position("B", 1, 10, [1, 2, 3])], limits())


def test_non_finite_input_is_rejected():
    with pytest.raises(PortfolioRiskError, match="must be finite"):
        PortfolioPosition("A", Decimal("NaN"), Decimal("10"))
