from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.dhan import DhanBroker
from app.brokers.http import LiveBrokerDisabled
from app.brokers.order_config import BrokerInstrument, ExchangeSegment, InstrumentResolver, OrderValidity, ProductType
from app.brokers.upstox import UpstoxBroker


def order(symbol: str = "NIFTY", client_order_id: str = "client-1") -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id=client_order_id,
        symbol=symbol,
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


@pytest.mark.asyncio
async def test_upstox_live_submission_is_gated_by_default() -> None:
    broker = UpstoxBroker("token")
    with pytest.raises(LiveBrokerDisabled):
        await broker.place_order(order("1333"))


@pytest.mark.asyncio
async def test_upstox_sandbox_submission_is_separately_gated() -> None:
    broker = UpstoxBroker("sandbox-token", sandbox=True, instrument_resolver=resolver())
    assert broker.sandbox is True
    assert broker.orders_enabled is False
    assert broker._client.base_url == UpstoxBroker.SANDBOX_BASE_URL
    with pytest.raises(LiveBrokerDisabled, match="sandbox order submission is disabled"):
        await broker.place_order(order())


@pytest.mark.asyncio
async def test_upstox_sandbox_order_gate_does_not_enable_live_mode() -> None:
    broker = UpstoxBroker(
        "sandbox-token",
        sandbox=True,
        allow_sandbox_orders=True,
        instrument_resolver=resolver(),
    )
    assert broker.orders_enabled is True
    assert broker._client.base_url == UpstoxBroker.SANDBOX_BASE_URL


@pytest.mark.asyncio
async def test_upstox_live_order_gate_is_not_reused_for_sandbox() -> None:
    broker = UpstoxBroker(
        "token",
        allow_live_orders=True,
        sandbox=True,
        instrument_resolver=resolver(),
    )
    assert broker.orders_enabled is False
    assert broker._client.base_url == UpstoxBroker.SANDBOX_BASE_URL


@pytest.mark.asyncio
async def test_dhan_live_submission_is_gated_by_default() -> None:
    broker = DhanBroker("client", "token")
    with pytest.raises(LiveBrokerDisabled):
        await broker.place_order(order("1333"))


def test_upstox_order_mapping_is_provider_neutral() -> None:
    mapped = UpstoxBroker._map_order({
        "order_id": "u-1",
        "tag": "client-1",
        "instrument_token": "NSE_EQ|TEST",
        "transaction_type": "BUY",
        "order_type": "MARKET",
        "quantity": 5,
        "filled_quantity": 5,
        "average_price": 101.25,
        "status": "complete",
    })
    assert mapped.order_id == "u-1"
    assert mapped.client_order_id == "client-1"
    assert mapped.status is BrokerOrderStatus.FILLED
    assert mapped.filled_quantity == 5


def test_dhan_order_mapping_is_provider_neutral() -> None:
    mapped = DhanBroker._map_order({
        "orderId": "d-1",
        "correlationId": "client-1",
        "securityId": "1333",
        "transactionType": "SELL",
        "orderType": "MARKET",
        "quantity": 5,
        "tradedQty": 2,
        "averageTradedPrice": 100.5,
        "orderStatus": "PART_TRADED",
    })
    assert mapped.order_id == "d-1"
    assert mapped.client_order_id == "client-1"
    assert mapped.status is BrokerOrderStatus.PARTIALLY_FILLED
    assert mapped.filled_quantity == 2


def test_unknown_upstox_status_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported Upstox order status"):
        UpstoxBroker._map_order({"order_id": "u-unknown", "tag": "client-1", "status": "new-provider-state"})


def test_unknown_dhan_status_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported Dhan order status"):
        DhanBroker._map_order({"orderId": "d-unknown", "correlationId": "client-1", "orderStatus": "new-provider-state"})


def test_upstox_payload_uses_resolved_provider_configuration() -> None:
    payload = UpstoxBroker._order_payload(order(), resolver().resolve("NIFTY"))
    assert payload["instrument_token"] == "NSE_FO|NIFTY_TEST"
    assert payload["product"] == "D"
    assert payload["validity"] == "IOC"
    assert payload["price"] == 101.25
    assert payload["market_protection"] == -1


def test_dhan_payload_uses_resolved_provider_configuration() -> None:
    broker = DhanBroker("client-42", "token", instrument_resolver=resolver())
    payload = broker._order_payload(order(), resolver().resolve("NIFTY"))
    assert payload["dhanClientId"] == "client-42"
    assert payload["correlationId"] == "client-1"
    assert payload["securityId"] == "NSE_FO|NIFTY_TEST"
    assert payload["exchangeSegment"] == "NSE_FNO"
    assert payload["productType"] == "CNC"
    assert payload["validity"] == "IOC"


def test_dhan_rejects_invalid_correlation_id_before_network_call() -> None:
    broker = DhanBroker("client-42", "token", instrument_resolver=resolver())
    long_id = "x" * 31
    with pytest.raises(ValueError, match="at most 30"):
        broker._order_payload(order(client_order_id=long_id), resolver().resolve("NIFTY"))
    with pytest.raises(ValueError, match="unsupported characters"):
        broker._order_payload(order(client_order_id="client/1"), resolver().resolve("NIFTY"))


def test_enabled_broker_rejects_unknown_instrument_before_network_call() -> None:
    broker = DhanBroker("client", "token", allow_live_orders=True)
    with pytest.raises(KeyError, match="instrument mapping not configured"):
        # Resolver lookup occurs before the HTTP request.
        import asyncio
        asyncio.run(broker.place_order(order("UNKNOWN")))
