from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.dhan import DhanBroker
from app.brokers.order_config import BrokerInstrument, ExchangeSegment, InstrumentResolver, OrderValidity, ProductType


def order() -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id="client-1",
        symbol="NIFTY",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.LIMIT,
        quantity=1,
        average_price=Decimal("101.25"),
        status=BrokerOrderStatus.NEW,
    )


def resolver() -> InstrumentResolver:
    return InstrumentResolver(
        (
            BrokerInstrument(
                canonical_symbol="NIFTY",
                provider_symbol="NSE_FO|NIFTY_TEST",
                exchange_segment=ExchangeSegment.NSE_FNO,
                product_type=ProductType.DELIVERY,
                validity=OrderValidity.IOC,
            ),
        )
    )


@pytest.mark.parametrize(
    ("provider_status", "expected"),
    [
        ("PENDING", BrokerOrderStatus.NEW),
        ("TRANSIT", BrokerOrderStatus.OPEN),
        ("PART_TRADED", BrokerOrderStatus.PARTIALLY_FILLED),
        ("TRADED", BrokerOrderStatus.FILLED),
        ("CANCELLED", BrokerOrderStatus.CANCELLED),
        ("EXPIRED", BrokerOrderStatus.CANCELLED),
        ("REJECTED", BrokerOrderStatus.REJECTED),
    ],
)
def test_dhan_status_mapping_is_conservative_and_terminal(provider_status: str, expected: BrokerOrderStatus) -> None:
    assert DhanBroker._map_status(provider_status) is expected


@pytest.mark.asyncio
async def test_dhan_submission_preserves_broker_rejection(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker(
        "client",
        "token",
        allow_live_orders=True,
        instrument_resolver=resolver(),
    )

    async def fake_request(method: str, path: str, **kwargs: object) -> dict[str, object]:
        assert method == "POST"
        assert path == "/orders"
        return {"orderId": "d-rejected", "orderStatus": "REJECTED"}

    monkeypatch.setattr(broker._client, "request", fake_request)
    submitted = await broker.place_order(order())
    assert submitted.order_id == "d-rejected"
    assert submitted.status is BrokerOrderStatus.REJECTED


@pytest.mark.asyncio
async def test_dhan_submission_preserves_pending_status(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker(
        "client",
        "token",
        allow_live_orders=True,
        instrument_resolver=resolver(),
    )

    async def fake_request(method: str, path: str, **kwargs: object) -> dict[str, object]:
        return {"orderId": "d-pending", "orderStatus": "PENDING"}

    monkeypatch.setattr(broker._client, "request", fake_request)
    submitted = await broker.place_order(order())
    assert submitted.order_id == "d-pending"
    assert submitted.status is BrokerOrderStatus.NEW
