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


class UpstoxBroker:
    """Provider adapter for Upstox v2 account/portfolio/order APIs.

    The adapter is read-capable when a token is supplied. Live mutation is
    intentionally disabled unless the caller explicitly opts in; this class
    does not itself provide a route that enables live trading.

    ``BrokerOrder.symbol`` is mapped to the Upstox ``instrument_token``.
    """

    provider = "upstox"

    def __init__(self, access_token: str, *, timeout: float = 10.0, allow_live_orders: bool = False) -> None:
        self._client = HTTPBrokerClient("https://api.upstox.com/v2", access_token, timeout=timeout)
        self._allow_live_orders = allow_live_orders

    async def authenticate(self) -> BrokerAuthentication:
        return BrokerAuthentication(
            provider=self.provider,
            account_id="upstox",
            authenticated=self._client.authenticated,
        )

    async def get_account(self) -> Account:
        payload = await self._client.request("GET", "/user/get-funds-and-margin")
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        equity = data.get("equity", {}) if isinstance(data, dict) else {}
        available = decimal_value(equity.get("available_margin"))
        balance = decimal_value(equity.get("payin_amount"), "0") + available
        return Account(account_id="upstox", currency="INR", balance=balance, available_margin=available)

    async def get_positions(self) -> tuple[BrokerPosition, ...]:
        payload = await self._client.request("GET", "/portfolio/short-term-positions")
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        return tuple(
            BrokerPosition(
                symbol=str(row.get("instrument_token", "")),
                quantity=int(row.get("quantity", row.get("net_quantity", 0)) or 0),
                average_price=decimal_value(row.get("average_price")),
                realized_pnl=decimal_value(row.get("realised", row.get("realized", 0))),
                unrealized_pnl=decimal_value(row.get("unrealised", row.get("unrealized", 0))),
            )
            for row in rows
        )

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        payload = await self._client.request("GET", "/order/retrieve-all")
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        return tuple(self._map_order(row) for row in rows)

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        if not self._allow_live_orders:
            raise LiveBrokerDisabled("Upstox live order submission is disabled")
        body = {
            "quantity": order.quantity,
            "product": "D",
            "validity": "DAY",
            "price": float(order.average_price or Decimal("0")),
            "tag": order.client_order_id,
            "instrument_token": order.symbol,
            "order_type": order.order_type.value,
            "transaction_type": order.side.value,
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False,
            "market_protection": 0,
        }
        payload = await self._client.request("POST", "/order/place", json=body)
        order_id = str((payload.get("data") or {}).get("order_id", order.order_id)) if isinstance(payload, dict) else order.order_id
        return order.model_copy(update={"order_id": order_id, "status": BrokerOrderStatus.NEW})

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        if not self._allow_live_orders:
            raise LiveBrokerDisabled("Upstox live order cancellation is disabled")
        payload = await self._client.request("DELETE", "/order/cancel", params={"order_id": order_id})
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        return BrokerOrder(
            order_id=order_id,
            client_order_id=str(data.get("tag", order_id)),
            symbol=str(data.get("instrument_token", "unknown")),
            side=str(data.get("transaction_type", "BUY")),
            order_type=str(data.get("order_type", "MARKET")),
            quantity=int(data.get("quantity", 1) or 1),
            status=BrokerOrderStatus.CANCELLED,
        )

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        orders = await self.get_orders()
        match = next((item for item in orders if item.client_order_id == client_order_id), None)
        return BrokerReconciliation(
            client_order_id=client_order_id,
            broker_status=match.status if match else None,
            matched=match is not None,
            reason=None if match else "order not found by client tag",
        )

    @staticmethod
    def _map_order(row: dict[str, Any]) -> BrokerOrder:
        status_map = {
            "complete": BrokerOrderStatus.FILLED,
            "open": BrokerOrderStatus.OPEN,
            "pending": BrokerOrderStatus.NEW,
            "cancelled": BrokerOrderStatus.CANCELLED,
            "rejected": BrokerOrderStatus.REJECTED,
        }
        raw_status = str(row.get("status", "pending")).lower()
        return BrokerOrder(
            order_id=str(row.get("order_id", "")),
            client_order_id=str(row.get("tag", row.get("order_ref_id", row.get("order_id", "")))),
            symbol=str(row.get("instrument_token", "")),
            side=str(row.get("transaction_type", "BUY")),
            order_type=str(row.get("order_type", "MARKET")),
            quantity=int(row.get("quantity", 1) or 1),
            filled_quantity=int(row.get("filled_quantity", 0) or 0),
            average_price=decimal_value(row.get("average_price"), "0") or None,
            status=status_map.get(raw_status, BrokerOrderStatus.NEW),
        )
