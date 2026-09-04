from decimal import Decimal

import pytest

from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.dhan import DhanBroker
from app.brokers.http import BrokerHTTPError, LiveBrokerDisabled
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
async def test_upstox_missing_broker_order_id_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = UpstoxBroker(
        "sandbox-token",
        sandbox=True,
        allow_sandbox_orders=True,
        instrument_resolver=resolver(),
    )

    async def fake_request(*args, **kwargs):
        return {"data": {}}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(BrokerHTTPError, match="no broker order ID; reconciliation required"):
        await broker.place_order(order())


@pytest.mark.asyncio
async def test_upstox_empty_order_ids_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = UpstoxBroker(
        "sandbox-token",
        sandbox=True,
        allow_sandbox_orders=True,
        instrument_resolver=resolver(),
    )

    async def fake_request(*args, **kwargs):
        return {"data": {"order_ids": []}}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(BrokerHTTPError, match="no broker order ID; reconciliation required"):
        await broker.place_order(order())


@pytest.mark.asyncio
async def test_upstox_cancel_requires_broker_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = UpstoxBroker("sandbox-token", sandbox=True, allow_sandbox_orders=True)

    async def fake_request(*args, **kwargs):
        return {"data": {}}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(BrokerHTTPError, match="ambiguous broker order ID; reconciliation required"):
        await broker.cancel_order("broker-1")


@pytest.mark.asyncio
async def test_upstox_cancel_rejects_mismatched_broker_order_id(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = UpstoxBroker("sandbox-token", sandbox=True, allow_sandbox_orders=True)

    async def fake_request(*args, **kwargs):
        return {"data": {"order_id": "different-order"}}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(BrokerHTTPError, match="ambiguous broker order ID; reconciliation required"):
        await broker.cancel_order("broker-1")


@pytest.mark.asyncio
async def test_upstox_cancel_accepts_matching_broker_order_id(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = UpstoxBroker("sandbox-token", sandbox=True, allow_sandbox_orders=True)

    async def fake_request(*args, **kwargs):
        return {"data": {"order_id": "broker-1"}}

    monkeypatch.setattr(broker._client, "request", fake_request)
    cancelled = await broker.cancel_order("broker-1")
    assert cancelled.order_id == "broker-1"
    assert cancelled.status is BrokerOrderStatus.CANCELLED


@pytest.mark.asyncio
async def test_dhan_live_submission_is_gated_by_default() -> None:
    broker = DhanBroker("client", "token")
    with pytest.raises(LiveBrokerDisabled):
        await broker.place_order(order("1333"))


@pytest.mark.asyncio
async def test_dhan_place_order_requires_broker_status(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker("client", "token", allow_live_orders=True, instrument_resolver=resolver())

    async def fake_request(*args, **kwargs):
        return {"orderId": "d-1"}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(RuntimeError, match="did not contain an order status; reconciliation required"):
        await broker.place_order(order())


@pytest.mark.asyncio
async def test_dhan_place_order_rejects_blank_broker_status(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker("client", "token", allow_live_orders=True, instrument_resolver=resolver())

    async def fake_request(*args, **kwargs):
        return {"orderId": "d-1", "orderStatus": "   "}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(RuntimeError, match="did not contain an order status; reconciliation required"):
        await broker.place_order(order())


@pytest.mark.asyncio
async def test_dhan_cancel_requires_authoritative_response(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker("client", "token", allow_live_orders=True)

    async def fake_request(*args, **kwargs):
        return {}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(RuntimeError, match="cancellation response was ambiguous"):
        await broker.cancel_order("d-1")


@pytest.mark.asyncio
async def test_dhan_cancel_rejects_mismatched_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker("client", "token", allow_live_orders=True)

    async def fake_request(*args, **kwargs):
        return {"orderId": "different", "orderStatus": "CANCELLED"}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(RuntimeError, match="cancellation response was ambiguous"):
        await broker.cancel_order("d-1")


@pytest.mark.asyncio
async def test_dhan_cancel_requires_refreshed_cancelled_state(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker("client", "token", allow_live_orders=True)
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append((method, path))
        if method == "DELETE":
            return {"orderId": "d-1", "orderStatus": "CANCELLED"}
        return {"orderId": "d-1", "correlationId": "client-1", "securityId": "1333", "transactionType": "BUY", "orderType": "LIMIT", "quantity": 1, "orderStatus": "PENDING"}

    monkeypatch.setattr(broker._client, "request", fake_request)
    with pytest.raises(RuntimeError, match="state refresh was not confirmed"):
        await broker.cancel_order("d-1")
    assert calls == [("DELETE", "/orders/d-1"), ("GET", "/orders/d-1")]


@pytest.mark.asyncio
async def test_dhan_cancel_returns_refreshed_broker_order(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = DhanBroker("client", "token", allow_live_orders=True)

    async def fake_request(method, path, **kwargs):
        if method == "DELETE":
            return {"orderId": "d-1", "orderStatus": "CANCELLED"}
        return {"orderId": "d-1", "correlationId": "client-1", "securityId": "1333", "transactionType": "BUY", "orderType": "LIMIT", "quantity": 1, "filledQty": 0, "orderStatus": "CANCELLED"}

    monkeypatch.setattr(broker._client, "request", fake_request)
    cancelled = await broker.cancel_order("d-1")
    assert cancelled.order_id == "d-1"
    assert cancelled.client_order_id == "client-1"
    assert cancelled.symbol == "1333"
    assert cancelled.status is BrokerOrderStatus.CANCELLED


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


def test_missing_upstox_order_status_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="did not contain an order status; reconciliation required"):
        UpstoxBroker._map_order({"order_id": "u-missing", "tag": "client-1"})


def test_blank_upstox_order_status_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="did not contain an order status; reconciliation required"):
        UpstoxBroker._map_order({"order_id": "u-blank", "tag": "client-1", "status": "   "})


def test_unknown_dhan_status_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported Dhan order status"):
        DhanBroker._map_order({"orderId": "d-unknown", "correlationId": "client-1", "orderStatus": "new-provider-state"})


def test_missing_dhan_order_status_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="did not contain an order status; reconciliation required"):
        DhanBroker._map_order({"orderId": "d-missing", "correlationId": "client-1"})


def test_blank_dhan_order_status_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="did not contain an order status; reconciliation required"):
        DhanBroker._map_order({"orderId": "d-blank", "correlationId": "client-1", "orderStatus": "   "})


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
        import asyncio
        asyncio.run(broker.place_order(order("UNKNOWN")))