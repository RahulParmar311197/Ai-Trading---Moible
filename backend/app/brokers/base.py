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


class Account(BaseModel):
    account_id: str
    currency: str = "INR"
    balance: Decimal
    available_margin: Decimal


class BrokerOrder(BaseModel):
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: int = Field(gt=0)
    filled_quantity: int = Field(default=0, ge=0)
    average_price: Decimal | None = None
    status: BrokerOrderStatus


class BrokerPosition(BaseModel):
    symbol: str
    quantity: int
    average_price: Decimal
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")


class Broker(Protocol):
    """Provider-neutral execution boundary. Implementations must enforce auth and broker safety externally."""

    async def get_account(self) -> Account: ...

    async def get_positions(self) -> tuple[BrokerPosition, ...]: ...

    async def get_orders(self) -> tuple[BrokerOrder, ...]: ...

    async def place_order(self, order: BrokerOrder) -> BrokerOrder: ...

    async def cancel_order(self, order_id: str) -> BrokerOrder: ...
