from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(StrEnum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Order(BaseModel):
    order_id: str = Field(min_length=1, max_length=128)
    symbol: str = Field(min_length=1, max_length=64)
    side: OrderSide
    order_type: OrderType
    quantity: int = Field(gt=0)
    limit_price: Decimal | None = Field(default=None, gt=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: OrderStatus = OrderStatus.NEW
    filled_quantity: int = Field(default=0, ge=0)
    average_fill_price: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_fill_state(self) -> "Order":
        if self.filled_quantity > self.quantity:
            raise ValueError("filled quantity cannot exceed order quantity")
        if self.average_fill_price is not None and not self.average_fill_price.is_finite():
            raise ValueError("average fill price must be finite")
        if self.status is OrderStatus.FILLED and self.filled_quantity != self.quantity:
            raise ValueError("filled order must have complete fill quantity")
        if self.status is OrderStatus.PARTIALLY_FILLED and not 0 < self.filled_quantity < self.quantity:
            raise ValueError("partially filled order must have a partial fill quantity")
        return self


class Fill(BaseModel):
    order_id: str = Field(min_length=1, max_length=128)
    quantity: int = Field(gt=0)
    price: Decimal = Field(gt=0)
    fee: Decimal = Field(default=Decimal("0"), ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_financial_values(self) -> "Fill":
        if not self.price.is_finite() or not self.fee.is_finite():
            raise ValueError("fill financial values must be finite")
        return self


class Position(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    quantity: int
    average_price: Decimal = Field(gt=0)
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")

    @model_validator(mode="after")
    def validate_financial_values(self) -> "Position":
        if not self.average_price.is_finite():
            raise ValueError("position average price must be finite")
        if not self.realized_pnl.is_finite() or not self.unrealized_pnl.is_finite():
            raise ValueError("position pnl values must be finite")
        return self

    def mark(self, price: Decimal) -> "Position":
        if not price.is_finite() or price <= 0:
            raise ValueError("mark price must be finite and positive")
        self.unrealized_pnl = (price - self.average_price) * self.quantity
        return self
