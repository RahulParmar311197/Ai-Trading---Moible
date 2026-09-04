from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from ..base import Account, BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerPosition, BrokerReconciliation
from ..http import HTTPBrokerClient, LiveBrokerDisabled, decimal_value
from ..order_config import BrokerInstrument, InstrumentResolver, OrderValidity, ProductType
from ..session import StaticTokenBrokerSession


class UpstoxBroker:
    """Provider adapter for Upstox v2 account/portfolio/order APIs."""

    provider = "upstox"
    LIVE_BASE_URL = "https://api.upstox.com/v2"
    SANDBOX_BASE_URL = "https://api-sandbox.upstox.com/v2"

    def __init__(self, access_token: str, *, timeout: float = 10.0, allow_live_orders: bool = False, sandbox: bool = False, allow_sandbox_orders: bool = False, instrument_resolver: InstrumentResolver | None = None, session_expires_at: datetime | None = None) -> None:
        self._sandbox = sandbox
        self._allow_live_orders = allow_live_orders
        self._allow_sandbox_orders = allow_sandbox_orders
        self._session = StaticTokenBrokerSession(self.provider, "upstox", access_token, expires_at=session_expires_at)
        base_url = self.SANDBOX_BASE_URL if sandbox else self.LIVE_BASE_URL
        self._client = HTTPBrokerClient(base_url, session=self._session, timeout=timeout)
        self._instrument_resolver = instrument_resolver or InstrumentResolver()

    @property
    def session(self) -> StaticTokenBrokerSession:
        return self._session

    @property
    def sandbox(self) -> bool:
        return self._sandbox

    @property
    def orders_enabled(self) -> bool:
        return self._allow_sandbox_orders if self._sandbox else self._allow_live_orders

    async def authenticate(self) -> BrokerAuthentication:
        return self._session.authentication()

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
        return tuple(BrokerPosition(symbol=str(row.get("instrument_token", "")), quantity=int(row.get("quantity", row.get("net_quantity", 0)) or 0), average_price=decimal_value(row.get("average_price")), realized_pnl=decimal_value(row.get("realised", row.get("realized", 0))), unrealized_pnl=decimal_value(row.get("unrealised", row.get("unrealized", 0)))) for row in rows)

    async def get_orders(self) -> tuple[BrokerOrder, ...]:
        payload = await self._client.request("GET", "/order/retrieve-all")
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        return tuple(self._map_order(row) for row in rows)

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        if not self.orders_enabled:
            raise LiveBrokerDisabled("Upstox sandbox order submission is disabled" if self._sandbox else "Upstox live order submission is disabled")
        instrument = self._instrument_resolver.resolve(order.symbol)
        payload = await self._client.request("POST", "/order/place", json=self._order_payload(order, instrument))
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict) and data.get("order_id"):
            order_id = str(data["order_id"])
        elif isinstance(data, dict) and data.get("order_ids"):
            order_id = str(data["order_ids"][0])
        else:
            order_id = order.order_id
        return order.model_copy(update={"order_id": order_id, "status": BrokerOrderStatus.NEW})

    @staticmethod
    def _order_payload(order: BrokerOrder, instrument: BrokerInstrument) -> dict[str, Any]:
        product = {ProductType.INTRADAY: "I", ProductType.DELIVERY: "D", ProductType.MARGIN: "MTF"}[instrument.product_type]
        validity = instrument.validity.value if hasattr(instrument, "validity") else OrderValidity.DAY.value
        return {"quantity": order.quantity, "product": product, "validity": validity, "price": float(order.average_price or Decimal("0")), "tag": order.client_order_id, "instrument_token": instrument.provider_symbol, "order_type": order.order_type.value, "transaction_type": order.side.value, "disclosed_quantity": 0, "trigger_price": 0, "is_amo": False, "market_protection": -1}

    async def cancel_order(self, order_id: str) -> BrokerOrder:
        if not self.orders_enabled:
            raise LiveBrokerDisabled("Upstox sandbox order cancellation is disabled" if self._sandbox else "Upstox live order cancellation is disabled")
        payload = await self._client.request("DELETE", "/order/cancel", params={"order_id": order_id})
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        return BrokerOrder(order_id=order_id, client_order_id=str(data.get("tag", order_id)), symbol=str(data.get("instrument_token", "unknown")), side=str(data.get("transaction_type", "BUY")), order_type=str(data.get("order_type", "MARKET")), quantity=int(data.get("quantity", 1) or 1), status=BrokerOrderStatus.CANCELLED)

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation:
        orders = await self.get_orders()
        match = next((item for item in orders if item.client_order_id == client_order_id), None)
        return BrokerReconciliation(client_order_id=client_order_id, broker_status=match.status if match else None, matched=match is not None, reason=None if match else "order not found by client tag", broker_order=match)

    @staticmethod
    def _map_order(row: dict[str, Any]) -> BrokerOrder:
        status_map = {"complete": BrokerOrderStatus.FILLED, "open": BrokerOrderStatus.OPEN, "pending": BrokerOrderStatus.NEW, "cancelled": BrokerOrderStatus.CANCELLED, "rejected": BrokerOrderStatus.REJECTED, "partially_filled": BrokerOrderStatus.PARTIALLY_FILLED, "partial": BrokerOrderStatus.PARTIALLY_FILLED}
        raw_status = str(row.get("status", "pending")).lower()
        try:
            status = status_map[raw_status]
        except KeyError as exc:
            raise ValueError(f"unsupported Upstox order status: {raw_status}") from exc
        return BrokerOrder(order_id=str(row.get("order_id", "")), client_order_id=str(row.get("tag", row.get("order_ref_id", row.get("order_id", "")))), symbol=str(row.get("instrument_token", "")), side=str(row.get("transaction_type", "BUY")), order_type=str(row.get("order_type", "MARKET")), quantity=int(row.get("quantity", 1) or 1), filled_quantity=int(row.get("filled_quantity", row.get("filled_qty", 0)) or 0), average_price=decimal_value(row.get("average_price"), "0") or None, status=status)
