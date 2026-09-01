from __future__ import annotations

from decimal import Decimal
from typing import Any

from ..base import (
    Account,
    BrokerAuthentication,
    BrokerOrder,
    BrokerOrderStatus,
    BrokerPosition,
    BrokerReconciliation,
)
from ..http import HTTPBrokerClient, LiveBrokerDisabled, decimal_value


class DhanBroker:
    """Provider adapter for DhanHQ v2 account/portfolio/order APIs.

    Read operations are available with an access token. Live order mutation is
    explicitly disabled by default and is not enabled by the application.

    ``BrokerOrder.symbol`` is mapped to Dhan's ``securityId``. The exchange
    segment defaults to NSE_EQ for this first provider-neutral boundary.
    """

    provider = "dhan"

    def __init__(self, client_id: str, access_token: str, *, timeout: float = 10.0, allow_live_orders: bool = False) -> None:
        self.client_id = client_id
        self._client = HTTPBrokerClient("https://api.dhan.co/v2", access_token, timeout=timeout)
        self._allow_live_orders = allow_live_orders

    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(
            provider=self.provider,
            account_id=self.client_id,
            authenticated=bool(self.client_id.strip()) and self._client.authenticated,
        )

    async def get_account(self) -> Account:
        payload = await self._client.request("GET", "/fundlimit")
        data = payload if isinstance(payload, dict) else {}
        available = decimal_value(data.get("availabelBalance", data.get("availableBalance", 0)))
        balance = available + decimal_value(data.get("utilizedAmount"))
        return Account(account_id=self.client_id, currency="INR", balance=balance, available_margin=available)

    async def get_positions(self) -> tuple[BrokerPosition, ...]:
        payload = await self._client.request("GET", "/positions")
        rows = payload if isinstance(payload, list) else payload.get("data", []) if isinstance(payload, dict) else []
        return tuple(
            BrokerPosition(
                symbol=str(row.get("securityId", row.get("tradingSymbol", ""))),
                quantity=int(row.get("netQty", row.get("netQuantity", 0)) or 0),
                average_price=decimal_value(row.get("costPrice", row.get("buyAvg", row.get("avgCostPrice", 0)))),
                realized_pnl=decimal_value(row.get("realizedProfit", row.get("realizedPnl", 0))),
                unrealized_pnl=decimal_value(row.get("unrealizedProfit", row.get("unrealizedPnl", 0))),
            )
            for row in rows
        )

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        payload = await self._client.request("GET", "/orders")
        rows = payload if isinstance(payload, list) else payload.get("data", []) if isinstance(payload, dict) else []
        return tuple(self._map_order(row) for row in rows)

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        if not self._allow_live_orders:
            raise LiveBrokerDisabled("Dhan live order submission is disabled")
        body = {
            "dhanClientId": self.client_id,
            "correlationId": order.client_order_id,
            "transactionType": order.side.value,
            "exchangeSegment": "NSE_EQ",
            "productType": "INTRADAY",
            "orderType": order.order_type.value,
            "validity": "DAY",
            "securityId": order.symbol,
            "quantity": order.quantity,
            "disclosedQuantity": "",
            "price": str(order.average_price or Decimal("0")),
            "triggerPrice": "",
            "afterMarketOrder": False,
            "amoTime": "",
            "boProfitValue": "",
            "boStopLossValue": "",
        }
        payload = await self._client.request("POST", "/orders", json=body)
        data = payload if isinstance(payload, dict) else {}
        order_id = str(data.get("orderId", data.get("order_id", order.order_id)))
        return order.model_copy(update={"order_id": order_id, "status": BrokerOrderStatus.NEW})

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        if not self._allow_live_orders:
            raise LiveBrokerDisabled("Dhan live order cancellation is disabled")
        payload = await self._client.request("DELETE", f"/orders/{order_id}")
        data = payload if isinstance(payload, dict) else {}
        return BrokerOrder(
            order_id=order_id,
            client_order_id=str(data.get("correlationId", order_id)),
            symbol=str(data.get("securityId", "unknown")),
            side=str(data.get("transactionType", "BUY")),
            order_type=str(data.get("orderType", "MARKET")),
            quantity=int(data.get("quantity", 1) or 1),
            status=BrokerOrderStatus.CANCELLED,
        )

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        payload = await self._client.request("GET", f"/orders/external/{client_order_id}")
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        if not isinstance(data, dict) or not data:
            return BrokerReconciliation(
                client_order_id=client_order_id,
                matched=False,
                reason="order not found by correlation id",
            )
        order = self._map_order(data)
        return BrokerReconciliation(
            client_order_id=client_order_id,
            broker_status=order.status,
            matched=True,
        )

    @staticmethod
    def _map_order(row: dict[str, Any]) -> BrokerOrder:
        status_map = {
            "TRADED": BrokerOrderStatus.FILLED,
            "PART_TRADED": BrokerOrderStatus.PARTIALLY_FILLED,
            "PENDING": BrokerOrderStatus.OPEN,
            "TRANSIT": BrokerOrderStatus.OPEN,
            "CANCELLED": BrokerOrderStatus.CANCELLED,
            "REJECTED": BrokerOrderStatus.REJECTED,
        }
        raw_status = str(row.get("orderStatus", row.get("status", "PENDING"))).upper()
        return BrokerOrder(
            order_id=str(row.get("orderId", row.get("order_id", ""))),
            client_order_id=str(row.get("correlationId", row.get("correlation_id", row.get("orderId", "")))),
            symbol=str(row.get("securityId", row.get("tradingSymbol", ""))),
            side=str(row.get("transactionType", "BUY")),
            order_type=str(row.get("orderType", "MARKET")),
            quantity=int(row.get("quantity", 1) or 1),
            filled_quantity=int(row.get("tradedQty", row.get("filledQuantity", 0)) or 0),
            average_price=decimal_value(row.get("averageTradedPrice", row.get("averagePrice", 0))) or None,
            status=status_map.get(raw_status, BrokerOrderStatus.NEW),
        )
