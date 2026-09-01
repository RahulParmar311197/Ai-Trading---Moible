from datetime import date, datetime, timezone
from decimal import Decimal

from app.options.liquidity import liquid, select_by_delta, spread_percent
from app.options.models import OptionChain, OptionContract, OptionLiquidityLimits, OptionType


def option(symbol: str, delta: str, bid: str = "100", ask: str = "102", volume: int = 1000, oi: int = 5000) -> OptionContract:
    return OptionContract(
        symbol=symbol,
        underlying="NIFTY",
        expiry=date(2026, 9, 24),
        strike=Decimal("25000"),
        option_type=OptionType.CALL,
        bid=Decimal(bid),
        ask=Decimal(ask),
        ltp=Decimal("101"),
        volume=volume,
        open_interest=oi,
        iv=Decimal("0.2"),
        delta=Decimal(delta),
    )


def test_liquidity_rejects_wide_spread_and_stale_price():
    limits = OptionLiquidityLimits(min_volume=100, min_open_interest=100, max_spread_percent=Decimal("0.05"))
    assert liquid(option("GOOD", "0.5"), limits)
    assert not liquid(option("WIDE", "0.5", bid="50", ask="100"), limits)
    assert not liquid(option("STALE", "0.5", bid="0", ask="0"), limits)


def test_delta_selection_is_deterministic():
    limits = OptionLiquidityLimits(min_volume=100, min_open_interest=100, max_spread_percent=Decimal("0.05"))
    chain = OptionChain(
        underlying="NIFTY",
        as_of=datetime(2026, 9, 1, tzinfo=timezone.utc),
        contracts=(option("A", "0.45"), option("B", "0.55"), option("C", "0.80")),
    )
    selected = select_by_delta(chain, Decimal("0.52"), limits)
    assert selected is not None
    assert selected.contract.symbol == "B"
    assert spread_percent(selected.contract) == Decimal("2") / Decimal("101")
