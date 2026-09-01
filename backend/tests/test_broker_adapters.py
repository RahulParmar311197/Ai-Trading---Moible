from app.brokers.base import BrokerOrder, BrokerOrderStatus, BrokerOrderType, BrokerSide
from app.brokers.dhan import DhanBroker
from app.brokers.http import LiveBrokerDisabled
from app.brokers.upstox import UpstoxBroker
import pytest


def order() -> BrokerOrder:
    return BrokerOrder(
        order_id="local-1",
        client_order_id="client-1",
        symbol="1333",
        side=BrokerSide.BUY,
        order_type=BrokerOrderType.MARKET,
        quantity=1,
        status=BrokerOrderStatus.NEW,
    )


@pytest.mark.asyncio
async def test_upstox_live_submission_is_gated_by_default() -> None:
    broker = UpstoxBroker("token")
    with pytest.raises(LiveBrokerDisabled):
        await broker.place_order(order())


@pytest.mark.asyncio
async def test_dhan_live_submission_is_gated_by_default() -> None:
    broker = DhanBroker("client", "token")
    with pytest.raises(LiveBrokerDisabled):
        await broker.place_order(order())


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
