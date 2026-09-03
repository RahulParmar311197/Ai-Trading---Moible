from __future__ import annotations

import os
import uuid

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.upstox import UpstoxBroker
from app.brokers.order_config import BrokerInstrument, ExchangeSegment, InstrumentResolver, OrderValidity, ProductType


SANDBOX_TOKEN = os.getenv("UPSTOX_SANDBOX_ACCESS_TOKEN", "").strip()


def sandbox_resolver() -> InstrumentResolver:
    return InstrumentResolver(
        (
            BrokerInstrument(
                canonical_symbol="SANDBOX_EQ",
                provider_symbol="NSE_EQ|INE062A01020",
                exchange_segment=ExchangeSegment.NSE_EQ,
                product_type=ProductType.DELIVERY,
                validity=OrderValidity.DAY,
            ),
        )
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upstox_sandbox_place_and_cancel() -> None:
    if not SANDBOX_TOKEN:
        pytest.skip("UPSTOX_SANDBOX_ACCESS_TOKEN is not configured")

    broker = UpstoxBroker(
        SANDBOX_TOKEN,
        sandbox=True,
        allow_sandbox_orders=True,
        instrument_resolver=sandbox_resolver(),
        timeout=20.0,
    )
    client_order_id = f"sandbox-{uuid.uuid4().hex[:20]}"
    request = BrokerOrder(
        order_id=f"local-{client_order_id}",
        client_order_id=client_order_id,
        symbol="SANDBOX_EQ",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.LIMIT,
        quantity=1,
        average_price=1,
        status=BrokerOrderStatus.NEW,
    )

    placed = await broker.place_order(request)
    assert placed.order_id
    assert placed.order_id != request.order_id
    assert broker.sandbox is True

    cancelled = await broker.cancel_order(placed.order_id)
    assert cancelled.order_id == placed.order_id
    assert cancelled.status is BrokerOrderStatus.CANCELLED
