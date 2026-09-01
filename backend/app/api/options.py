from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.options.models import OptionChain, OptionLeg, OptionLiquidityLimits, OptionPayoffReport, OptionSelection
from app.options.payoff import payoff_at, payoff_report
from app.options.strategies import MarketBias, RiskProfile, permitted_strategies, select_liquid_contracts

router = APIRouter(prefix="/api/v1/options", tags=["options"])


class PayoffRequest(BaseModel):
    legs: tuple[OptionLeg, ...] = Field(min_length=1)


class PayoffPoint(BaseModel):
    underlying: Decimal = Field(ge=0)
    pnl: Decimal


class PayoffResponse(BaseModel):
    report: OptionPayoffReport
    points: tuple[PayoffPoint, ...]


class StrategySelectionRequest(BaseModel):
    bias: MarketBias
    risk_profile: RiskProfile = RiskProfile.MODERATE


class StrategySelectionResponse(BaseModel):
    strategies: tuple[str, ...]


@router.post("/payoff", response_model=PayoffResponse)
def calculate_payoff(request: PayoffRequest) -> PayoffResponse:
    report = payoff_report(request.legs)
    strikes = sorted({leg.contract.strike for leg in request.legs})
    if not strikes:
        raise HTTPException(status_code=422, detail="at least one strike is required")
    span = max(Decimal("1"), strikes[-1] - strikes[0])
    points = sorted({
        Decimal("0"),
        *strikes,
        max(Decimal("0"), strikes[0] - span),
        strikes[-1] + span,
    })
    return PayoffResponse(
        report=report,
        points=tuple(PayoffPoint(underlying=p, pnl=payoff_at(request.legs, p)) for p in points),
    )


@router.post("/strategies", response_model=StrategySelectionResponse)
def select_strategies(request: StrategySelectionRequest) -> StrategySelectionResponse:
    return StrategySelectionResponse(strategies=permitted_strategies(request.bias, request.risk_profile))


@router.post("/liquidity", response_model=tuple[OptionSelection, ...])
def filter_liquidity(chain: OptionChain, limits: OptionLiquidityLimits = OptionLiquidityLimits()) -> tuple[OptionSelection, ...]:
    return select_liquid_contracts(chain, limits)
