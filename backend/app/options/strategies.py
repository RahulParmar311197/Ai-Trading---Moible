from __future__ import annotations

from enum import StrEnum

from .models import OptionChain, OptionContract, OptionLiquidityLimits, OptionSelection, OptionType
from .liquidity import liquid


class MarketBias(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class RiskProfile(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


STRATEGIES: dict[MarketBias, tuple[str, ...]] = {
    MarketBias.BULLISH: ("LONG_CALL", "BULL_CALL_SPREAD", "BULL_PUT_SPREAD"),
    MarketBias.BEARISH: ("LONG_PUT", "BEAR_PUT_SPREAD", "BEAR_CALL_SPREAD"),
    MarketBias.NEUTRAL: ("IRON_CONDOR", "IRON_BUTTERFLY", "SHORT_STRADDLE", "SHORT_STRANGLE"),
}


def permitted_strategies(bias: MarketBias, risk_profile: RiskProfile) -> tuple[str, ...]:
    candidates = STRATEGIES[bias]
    if risk_profile is RiskProfile.CONSERVATIVE:
        return tuple(s for s in candidates if s in {"LONG_CALL", "LONG_PUT", "BULL_CALL_SPREAD", "BEAR_PUT_SPREAD"})
    if risk_profile is RiskProfile.MODERATE:
        return tuple(s for s in candidates if s not in {"SHORT_STRADDLE", "SHORT_STRANGLE"})
    return candidates


def select_liquid_contracts(
    chain: OptionChain, limits: OptionLiquidityLimits
) -> tuple[OptionSelection, ...]:
    selected: list[OptionSelection] = []
    for contract in chain.contracts:
        if not liquid(contract, limits):
            continue
        spread = (contract.ask - contract.bid) / contract.ltp if contract.ltp else 1
        score = (
            contract.open_interest
            + contract.volume
        ) / (1 + spread * 100)
        selected.append(OptionSelection(contract=contract, score=score))
    return tuple(sorted(selected, key=lambda item: item.score, reverse=True))


def pair_for_spread(
    contracts: tuple[OptionContract, ...], option_type: OptionType, bullish: bool
) -> tuple[OptionContract, OptionContract] | None:
    legs = sorted((c for c in contracts if c.option_type is option_type), key=lambda c: c.strike)
    if len(legs) < 2:
        return None
    if bullish:
        return legs[0], legs[-1]
    return legs[-1], legs[0]
