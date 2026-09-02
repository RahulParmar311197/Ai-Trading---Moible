from __future__ import annotations

from datetime import datetime
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
from ..order_config import BrokerInstrument, InstrumentResolver, ProductType
from ..session import StaticTokenBrokerSession


class DhanBroker:
    """Provider adapter for DhanHQ v2 account/portfolio/order APIs.

    Read operations are available with an access token. Live order mutation is
    explicitly disabled by default. Authentication state is owned by a
    secret-safe session boundary and never returned in domain DTOs.
    """

    provider = "dhan"
    _MAX_CORRELATION_ID_LENGTH = 30

    def __init__(
        self,
        client_id: str,
        access_token: str,
        *,
        timeout: float = 10.0,
        allow_live_orders: bool = False,
        instrument_resolver: InstrumentResolver | None = None,
        session_expires_at: datetime | None = None,
    ) -> None:
        self.client_id = client_id
        self._session = StaticTokenBrokerSession(
            self.provider, client_id, access_token, expires_at=session_expires_at
        )
        self._client = HTTPBrokerClient(
            "https://api.dhan.co/v2", session=self._session, timeout=timeout
        )
        self._allow_live_orders = allow_live_orders
        self._instrument_resolver = instrument_resolver or InstrumentResolver()

    @property
    def session(self) -> StaticTokenBrokerSession:
        return self._session

    async def authenticate(self) -> BrokerAuthentication:
        return self._session.authentication()

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
        instrument = self._instrument_resolver.resolve(order.symbol)
        body = self._order_payload(order, instrument)
        payload = await self._client.request("POST", "/orders", json=body)
        data = payload if isinstance(payload, dict) else {}
        order_id = str(data.get("orderId", data.get("order_id", "")))
        raw_status = str(data.get("orderStatus", data.get("status", "PENDING"))).upper()
        status = self._map_status(raw_status)
        if not order_id:
            raise RuntimeError("Dhan order response did not contain an order id")
        return order.model_copy(update={"order_id": order_id, "status": status})

    @classmethod
    def _validate_correlation_id(cls, client_order_id: str) -> str:
        if not client_order_id:
            raise ValueError("Dhan correlation id must be non-empty")
        if len(client_order_id) > cls._MAX_CORRELATION_ID_LENGTH:
            raise ValueError("Dhan correlation id must be at most 30 characters")
        if any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-" for character in client_order_id):
            raise ValueError("Dhan correlation id contains unsupported characters")
        return client_order_id

    def _order_payload(self, order: BrokerOrder, instrument: BrokerInstrument) -> dict[str, Any]:
        product = {ProductType.INTRADAY: "INTRADAY", ProductType.DELIVERY: "CNC", ProductType.MARGIN: "MARGIN"}[instrument.product_type]
        return {
            "dhanClientId": self.client_id,
            "correlationId": self._validate_correlation_id(order.client_order_id),
            "transactionType": order.side.value,
            "exchangeSegment": instrument.exchange_segment.value,
            "productType": product,
            "orderType": order.order_type.value,
            "validity": instrument.validity.value,
            "securityId": instrument.provider_symbol,
            "quantity": order.quantity,
            "disclosedQuantity": "",
            "price": str(order.average_price or Decimal("0")),
            "triggerPrice": "",
            "afterMarketOrder": False,
            "amoTime": "",
            "boProfitValue": "",
            "boStopLossValue": "",
        }

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
        correlation_id = self._validate_correlation_id(client_order_id)
        payload = await self._client.request("GET", f"/orders/external/{correlation_id}")
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

    @classmethod
    def _map_status(cls, raw_status: str) -> BrokerOrderStatus:
        status_map = {
            "TRADED": BrokerOrderStatus.FILLED,
            "PART_TRADED": BrokerOrderStatus.PARTIALLY_FILLED,
            "PENDING": BrokerOrderStatus.NEW,
            "TRANSIT": BrokerOrderStatus.OPEN,
            "CANCELLED": BrokerOrderStatus.CANCELLED,
            "EXPIRED": BrokerOrderStatus.CANCELLED,
            "REJECTED": BrokerOrderStatus.REJECTED,
        }
        return status_map.get(raw_status.upper(), BrokerOrderStatus.NEW)

    @classmethod
    def _map_order(cls, row: dict[str, Any]) -> BrokerOrder:
        raw_status = str(row.get("orderStatus", row.get("status", "PENDING"))).upper()
        return BrokerOrder(
            order_id=str(row.get("orderId", row.get("order_id", ""))),
            client_order_id=str(row.get("correlationId", row.get("correlation_id", row.get("orderId", "")))),
            symbol=str(row.get("securityId", row.get("tradingSymbol", ""))),
            side=str(row.get("transactionType", "BUY")),
            order_type=str(row.get("orderType", "MARKET")),
            quantity=int(row.get("quantity", 1) or 1),
            filled_quantity=int(row.get("tradedQty", row.get("filledQuantity", row.get("filledQty", 0))) or 0),
            average_price=decimal_value(row.get("averageTradedPrice", row.get("averagePrice", 0))) or None,
            status=cls._map_status(raw_status),
        )
