from datetime import date
from decimal import Decimal

from app.options.greeks import black_scholes
from app.options.models import OptionContract, OptionType


def contract() -> OptionContract:
    return OptionContract(
        symbol="NIFTY26SEP25000CE",
        underlying="NIFTY",
        expiry=date(2026, 9, 24),
        strike=Decimal("25000"),
        option_type=OptionType.CALL,
        bid=Decimal("100"),
        ask=Decimal("102"),
        ltp=Decimal("101"),
        volume=1000,
        open_interest=5000,
        iv=Decimal("0.2"),
    )


def test_option_contract_validates_bid_ask():
    assert contract().ask == Decimal("102")


def test_black_scholes_call_has_positive_delta_gamma_vega():
    greeks = black_scholes(
        Decimal("25000"), Decimal("25000"), Decimal("30") / Decimal("365"), Decimal("0.2"), option_type=OptionType.CALL
    )
    assert Decimal("0") < greeks.delta < Decimal("1")
    assert greeks.gamma > 0
    assert greeks.vega > 0


def test_put_delta_is_negative_and_gamma_matches_call():
    args = (Decimal("25000"), Decimal("25000"), Decimal("30") / Decimal("365"), Decimal("0.2"))
    call = black_scholes(*args, option_type=OptionType.CALL)
    put = black_scholes(*args, option_type=OptionType.PUT)
    assert put.delta < 0
    assert abs(call.gamma - put.gamma) < Decimal("1e-20")
    assert abs(call.vega - put.vega) < Decimal("1e-18")


def test_black_scholes_rejects_invalid_inputs():
    import pytest

    with pytest.raises(ValueError):
        black_scholes(Decimal("0"), Decimal("25000"), Decimal("0.1"), Decimal("0.2"))
