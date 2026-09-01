from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class OptionType(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


class OptionContract(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    underlying: str = Field(min_length=1, max_length=64)
    expiry: date
    strike: Decimal = Field(gt=0)
    option_type: OptionType
    lot_size: int = Field(default=1, gt=0)
    bid: Decimal = Field(default=Decimal("0"), ge=0)
    ask: Decimal = Field(default=Decimal("0"), ge=0)
    ltp: Decimal = Field(default=Decimal("0"), ge=0)
    volume: int = Field(default=0, ge=0)
    open_interest: int = Field(default=0, ge=0)
    iv: Decimal | None = Field(default=None, ge=0, le=5)
    delta: Decimal | None = None
    gamma: Decimal | None = Field(default=None, ge=0)
    theta: Decimal | None = None
    vega: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_quote(self) -> "OptionContract":
        if self.ask and self.bid > self.ask:
            raise ValueError("option bid cannot exceed ask")
        return self


class OptionChain(BaseModel):
    underlying: str = Field(min_length=1, max_length=64)
    as_of: datetime
    contracts: tuple[OptionContract, ...]

    def for_expiry(self, expiry: date) -> tuple[OptionContract, ...]:
        return tuple(c for c in self.contracts if c.expiry == expiry)


class OptionLeg(BaseModel):
    contract: OptionContract
    quantity: int
    premium: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def validate_quantity(self) -> "OptionLeg":
        if self.quantity == 0:
            raise ValueError("option leg quantity cannot be zero")
        return self


class OptionPayoffReport(BaseModel):
    maximum_profit: Decimal | None
    maximum_loss: Decimal | None
    breakeven: tuple[Decimal, ...]
    capital_requirement: Decimal
    risk_reward: Decimal | None


class OptionLiquidityLimits(BaseModel):
    min_volume: int = Field(default=0, ge=0)
    min_open_interest: int = Field(default=0, ge=0)
    max_spread_percent: Decimal = Field(default=Decimal("0.1"), gt=0)


class OptionSelection(BaseModel):
    contract: OptionContract
    score: Decimal
