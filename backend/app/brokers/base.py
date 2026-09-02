from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field, model_validator


class BrokerOrderStatus(StrEnum):
    NEW = "NEW"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class BrokerSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class BrokerOrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class Account(BaseModel):
    account_id: str
    currency: str = "INR"
    balance: Decimal
    available_margin: Decimal

    @model_validator(mode="after")
    def validate_financial_values(self) -> "Account":
        if not self.balance.is_finite() or not self.available_margin.is_finite():
            raise ValueError("account financial values must be finite")
        return self


class BrokerOrder(BaseModel):
    order_id: str
    client_order_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: BrokerSide
    order_type: BrokerOrderType
    quantity: int = Field(gt=0)
    filled_quantity: int = Field(default=0, ge=0)
    average_price: Decimal | None = None
    status: BrokerOrderStatus

    @model_validator(mode="after")
    def validate_fill_state(self) -> "BrokerOrder":
        if self.filled_quantity > self.quantity:
            raise ValueError("filled quantity cannot exceed order quantity")
        if self.average_price is not None and (not self.average_price.is_finite() or self.average_price <= 0):
            raise ValueError("average price must be finite and positive")
        if self.status is BrokerOrderStatus.FILLED and self.filled_quantity != self.quantity:
            raise ValueError("filled order must have complete fill quantity")
        if self.status is BrokerOrderStatus.PARTIALLY_FILLED and not 0 < self.filled_quantity < self.quantity:
            raise ValueError("partially filled order must have a partial fill quantity")
        return self


class BrokerPosition(BaseModel):
    symbol: str = Field(min_length=1)
    quantity: int
    average_price: Decimal
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")

    @model_validator(mode="after")
    def validate_financial_values(self) -> "BrokerPosition":
        if not self.average_price.is_finite() or self.average_price < 0:
            raise ValueError("position average price must be finite and non-negative")
        if not self.realized_pnl.is_finite() or not self.unrealized_pnl.is_finite():
            raise ValueError("position pnl values must be finite")
        return self


class BrokerAuthentication(BaseModel):
    """Non-secret authentication context supplied by the application boundary."""

    provider: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    authenticated: bool = False


class BrokerReconciliation(BaseModel):
    """Deterministic broker-state reconciliation result."""

    client_order_id: str = Field(min_length=1)
    local_status: BrokerOrderStatus | None = None
    broker_status: BrokerOrderStatus | None = None
    matched: bool
    reason: str | None = None


class Broker(Protocol):
    """Provider-neutral execution boundary.

    Implementations must keep credentials outside domain models and enforce
    provider authentication, idempotency, reconciliation, and broker safety.
    """

    async def authenticate(self) -> BrokerAuthentication: ...

    async def get_account(self) -> Account: ...

    async def get_positions(self) -> tuple[BrokerPosition, ...]: ...

    async def get_orders(self) -> tuple[BrokerOrder, ...]: ...

    async def place_order(self, order: BrokerOrder) -> BrokerOrder: ...

    async def cancel_order(self, order_id: str) -> BrokerOrder: ...

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation: ...
