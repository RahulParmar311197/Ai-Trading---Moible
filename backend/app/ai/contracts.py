"""Provider-neutral structured contracts for AI analysis and trade explanation."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.market.models import Timeframe


class AIAnalysisRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    timeframe: Timeframe
    market_context: dict[str, Any] = Field(default_factory=dict)
    smc_context: dict[str, Any] = Field(default_factory=dict)
    ict_context: dict[str, Any] = Field(default_factory=dict)
    technical_context: dict[str, Any] = Field(default_factory=dict)
    options_context: dict[str, Any] = Field(default_factory=dict)
    risk_context: dict[str, Any] = Field(default_factory=dict)
    strategy_context: dict[str, Any] = Field(default_factory=dict)


class AITradeProposal(BaseModel):
    """AI suggestion only; it is never an executable broker order."""

    direction: str = Field(pattern="^(LONG|SHORT)$")
    entry: Decimal = Field(gt=0)
    stop: Decimal = Field(gt=0)
    target: Decimal = Field(gt=0)
    risk_reward: Decimal = Field(gt=0)
    setup_score: int = Field(ge=0, le=100)
    conditions_satisfied: tuple[str, ...] = ()
    conditions_missing: tuple[str, ...] = ()
    market_context: str = ""
    risk: str = ""
    invalidation: str = ""
    potential_exit: str = ""


class AIAnalysisResponse(BaseModel):
    summary: str = Field(min_length=1)
    proposal: AITradeProposal | None = None
