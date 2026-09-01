from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


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


class BrokerPosition(BaseModel):
    symbol: str = Field(min_length=1)
    quantity: int
    average_price: Decimal
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")


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
