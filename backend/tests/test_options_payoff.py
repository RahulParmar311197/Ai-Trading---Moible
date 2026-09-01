from datetime import date
from decimal import Decimal

import pytest

from app.options.models import OptionContract, OptionLeg, OptionType
from app.options.payoff import payoff_at, payoff_report
from app.options.strategies import MarketBias, RiskProfile, permitted_strategies


def contract(strike: str, option_type: OptionType, lot_size: int = 1) -> OptionContract:
    return OptionContract(
        symbol=f"TEST-{strike}-{option_type}",
        underlying="TEST",
        expiry=date(2026, 12, 31),
        strike=Decimal(strike),
        option_type=option_type,
        lot_size=lot_size,
        bid=Decimal("9"),
        ask=Decimal("11"),
        ltp=Decimal("10"),
        volume=1000,
        open_interest=2000,
    )


def test_long_call_payoff_and_unbounded_profit() -> None:
    leg = OptionLeg(contract=contract("100", OptionType.CALL), quantity=1, premium=Decimal("10"))
    assert payoff_at([leg], Decimal("90")) == Decimal("-10")
    assert payoff_at([leg], Decimal("130")) == Decimal("20")
    report = payoff_report([leg])
    assert report.maximum_profit is None
    assert report.maximum_loss == Decimal("-10")
    assert report.capital_requirement == Decimal("10")
    assert report.breakeven == (Decimal("110"),)


def test_bull_call_spread_has_bounded_profit_and_loss() -> None:
    long_call = OptionLeg(contract=contract("100", OptionType.CALL, 50), quantity=1, premium=Decimal("12"))
    short_call = OptionLeg(contract=contract("120", OptionType.CALL, 50), quantity=-1, premium=Decimal("4"))
    report = payoff_report([long_call, short_call])
    assert report.maximum_profit == Decimal("600")
    assert report.maximum_loss == Decimal("-400")
    assert report.capital_requirement == Decimal("400")
    assert report.breakeven == (Decimal("108"),)
    assert report.risk_reward == Decimal("1.5")


def test_lot_size_and_quantity_scale_payoff() -> None:
    leg = OptionLeg(contract=contract("100", OptionType.PUT, 25), quantity=2, premium=Decimal("5"))
    assert payoff_at([leg], Decimal("80")) == Decimal("-250")
    assert payoff_at([leg], Decimal("120")) == Decimal("-250")


def test_risk_profile_restricts_neutral_short_strategies() -> None:
    conservative = permitted_strategies(MarketBias.NEUTRAL, RiskProfile.CONSERVATIVE)
    assert conservative == ()
    aggressive = permitted_strategies(MarketBias.NEUTRAL, RiskProfile.AGGRESSIVE)
    assert "IRON_CONDOR" in aggressive
    assert "SHORT_STRADDLE" in aggressive


def test_zero_quantity_is_rejected() -> None:
    with pytest.raises(ValueError):
        OptionLeg(contract=contract("100", OptionType.CALL), quantity=0, premium=Decimal("1"))
