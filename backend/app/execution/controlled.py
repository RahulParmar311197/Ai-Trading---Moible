from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Protocol, Sequence

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerReconciliation
from app.brokers.idempotency import BrokerIdempotencyStore, IdempotentBroker

from .gate import DeterministicExecutionGate, RiskSnapshot


class ExecutionBroker(Protocol):
    async def place_order(self, order: BrokerOrder) -> BrokerOrder: ...


class ExecutionLifecycleBroker(ExecutionBroker, Protocol):
    async def authenticate(self) -> BrokerAuthentication: ...


class ExecutionRecoveryBroker(ExecutionLifecycleBroker, Protocol):
    async def get_positions(self) -> object: ...

    async def get_orders(self) -> tuple[BrokerOrder, ...]: ...

    async def reconcile_order(self, client_order_id: str) -> BrokerReconciliation: ...


@dataclass(frozen=True)
class ExecutionAuditEvent:
    event_type: str
    client_order_id: str
    reason: str
    timestamp: datetime


class ControlledExecutionError(RuntimeError):
    """Raised when a controlled live-execution prerequisite is not satisfied."""


class ControlledBrokerExecution:
    """Explicitly activated broker execution with deterministic safety gates.

    Construction and startup are inert. Live submission requires an explicit
    activation phrase, a successful authenticated broker session, a clear kill
    switch, and an explicitly supplied idempotency store. Requiring the store
    at construction prevents a live executor from silently falling back to
    process-local idempotency state that would disappear after a restart.
    """

    def __init__(
        self,
        broker: ExecutionBroker,
        risk_gate: DeterministicExecutionGate,
        *,
        confirmation_phrase: str,
        audit_sink: Callable[[ExecutionAuditEvent], None] | None = None,
        idempotency_store: BrokerIdempotencyStore,
    ) -> None:
        if not confirmation_phrase.strip():
            raise ValueError("confirmation phrase must be non-empty")
        self._broker = IdempotentBroker(broker, idempotency_store)
        self._risk_gate = risk_gate
        self._confirmation_phrase = confirmation_phrase
        self._audit_sink = audit_sink
        self._activated = False
        self._kill_switch = True
        self._started = False

    @property
    def active(self) -> bool:
        return self._started and self._activated and not self._kill_switch

    @property
    def started(self) -> bool:
        return self._started

    @property
    def kill_switch_active(self) -> bool:
        return self._kill_switch

    async def startup(self) -> BrokerAuthentication:
        """Verify broker authentication without enabling order mutation."""
        self._started = False
        self._activated = False
        self._kill_switch = True
        authenticate = getattr(self._broker, "authenticate", None)
        if not callable(authenticate):
            self._audit("STARTUP_REJECTED", "", "broker authentication boundary unavailable")
            raise ControlledExecutionError("broker authentication boundary unavailable")
        try:
            authentication = await authenticate()
        except Exception as exc:
            self._audit("STARTUP_REJECTED", "", f"broker authentication failed: {type(exc).__name__}")
            raise
        if not authentication.authenticated:
            self._audit("STARTUP_REJECTED", "", "broker session is not authenticated")
            raise ControlledExecutionError("broker session is not authenticated")
        self._started = True
        self._kill_switch = True
        self._audit("EXECUTION_READY", "", "authenticated broker session verified; kill switch remains active")
        return authentication

    async def recover(self, client_order_ids: Sequence[str] = ()) -> tuple[BrokerReconciliation, ...]:
        """Reconnect and reconcile broker state without automatically resuming trading.

        Recovery is deliberately fail-closed: authentication is refreshed first,
        broker orders/positions are refreshed, every supplied local order is
        reconciled, and every broker-reported live order must belong to that
        expected local set. An unexpected broker order is treated as an
        unresolved external/manual order and blocks activation rather than being
        silently adopted by the trading system.
        """
        self._started = False
        self._activated = False
        self._kill_switch = True
        self._audit("RECOVERY_STARTED", "", "broker recovery started; new entries disabled")
        try:
            authentication = await self.startup()
            if not authentication.authenticated:
                raise ControlledExecutionError("broker session is not authenticated")
            get_orders = getattr(self._broker, "get_orders", None)
            get_positions = getattr(self._broker, "get_positions", None)
            reconcile_order = getattr(self._broker, "reconcile_order", None)
            if not all(callable(operation) for operation in (get_orders, get_positions, reconcile_order)):
                self._audit("RECOVERY_REJECTED", "", "broker reconciliation boundary unavailable")
                raise ControlledExecutionError("broker reconciliation boundary unavailable")
            await get_positions()
            broker_orders = await get_orders()
            expected_ids = {client_order_id for client_order_id in client_order_ids if client_order_id.strip()}
            live_statuses = {
                BrokerOrderStatus.NEW,
                BrokerOrderStatus.OPEN,
                BrokerOrderStatus.PARTIALLY_FILLED,
            }
            unexpected_live_orders = tuple(
                order for order in broker_orders
                if order.status in live_statuses and order.client_order_id not in expected_ids
            )
            if unexpected_live_orders:
                client_order_id = unexpected_live_orders[0].client_order_id
                self._audit(
                    "RECONCILIATION_REQUIRED",
                    client_order_id,
                    "broker reported live order outside expected local order set",
                )
                self._started = False
                self._activated = False
                self._kill_switch = True
                raise ControlledExecutionError("unexpected broker live order requires reconciliation")
            reconciliations: list[BrokerReconciliation] = []
            for client_order_id in client_order_ids:
                if not client_order_id.strip():
                    self._audit("RECOVERY_REJECTED", "", "client order id must be non-empty")
                    raise ControlledExecutionError("client order id must be non-empty")
                reconciliation = await reconcile_order(client_order_id)
                reconciliations.append(reconciliation)
                if not reconciliation.matched:
                    self._audit("RECONCILIATION_REQUIRED", client_order_id, reconciliation.reason or "broker state mismatch")
                    self._started = False
                    self._activated = False
                    self._kill_switch = True
                    raise ControlledExecutionError("broker reconciliation mismatch")
            self._started = True
            self._activated = False
            self._kill_switch = True
            self._audit("RECOVERY_HEALTHY", "", "broker state refreshed and reconciled; explicit activation still required")
            return tuple(reconciliations)
        except Exception as exc:
            self._started = False
            self._activated = False
            self._kill_switch = True
            if not isinstance(exc, ControlledExecutionError):
                self._audit("RECOVERY_REJECTED", "", f"broker recovery failed: {type(exc).__name__}")
            raise

    def activate(self, confirmation: str) -> None:
        if not self._started:
            self._audit("ACTIVATION_REJECTED", "", "execution startup has not completed")
            raise ControlledExecutionError("execution startup has not completed")
        if confirmation != self._confirmation_phrase:
            self._audit("ACTIVATION_REJECTED", "", "explicit confirmation did not match")
            raise ControlledExecutionError("explicit live-execution confirmation required")
        self._activated = True
        self._kill_switch = False
        self._audit("EXECUTION_ACTIVATED", "", "explicit confirmation accepted")

    def trip_kill_switch(self, reason: str = "manual") -> None:
        if not reason.strip():
            raise ValueError("kill-switch reason must be non-empty")
        self._kill_switch = True
        self._audit("KILL_SWITCH_ACTIVATED", "", reason)

    def deactivate(self, reason: str = "manual") -> None:
        if not reason.strip():
            raise ValueError("deactivation reason must be non-empty")
        self._activated = False
        self._kill_switch = True
        self._audit("EXECUTION_DEACTIVATED", "", reason)

    async def shutdown(self, reason: str = "shutdown") -> None:
        """Fail closed before returning control to the application."""
        if not reason.strip():
            raise ValueError("shutdown reason must be non-empty")
        self._activated = False
        self._kill_switch = True
        self._started = False
        self._audit("EXECUTION_SHUTDOWN", "", reason)

    async def submit(
        self,
        order: BrokerOrder,
        *,
        market_price: Decimal,
        snapshot: RiskSnapshot,
    ) -> BrokerOrder:
        if not self._started:
            self._reject(order.client_order_id, "execution startup has not completed")
        if not self._activated:
            self._reject(order.client_order_id, "live execution is not activated")
        if self._kill_switch:
            self._reject(order.client_order_id, "live execution kill switch is active")
        decision = self._risk_gate.evaluate(order, market_price, snapshot)
        if not decision.approved:
            self._reject(order.client_order_id, decision.reason)
        self._audit("BROKER_SUBMISSION_ATTEMPTED", order.client_order_id, "risk checks approved")
        try:
            result = await self._broker.place_order(order)
        except Exception as exc:
            self._started = False
            self._activated = False
            self._kill_switch = True
            self._audit(
                "BROKER_SUBMISSION_FAILED",
                order.client_order_id,
                f"broker submission failed: {type(exc).__name__}; execution fail-closed pending reconciliation",
            )
            raise
        if result.status is BrokerOrderStatus.REJECTED:
            self._audit("BROKER_REJECTED", order.client_order_id, "broker rejected order")
            raise ControlledExecutionError("broker rejected order")
        if not result.order_id.strip():
            self._audit("BROKER_CONFIRMATION_INVALID", order.client_order_id, "broker returned no order id")
            raise ControlledExecutionError("broker did not confirm an order id")
        self._audit("BROKER_CONFIRMED", order.client_order_id, result.status.value)
        return result

    def _reject(self, client_order_id: str, reason: str) -> None:
        self._audit("EXECUTION_REJECTED", client_order_id, reason)
        raise ControlledExecutionError(reason)

    def _audit(self, event_type: str, client_order_id: str, reason: str) -> None:
        if self._audit_sink is not None:
            self._audit_sink(ExecutionAuditEvent(event_type, client_order_id, reason, datetime.now(timezone.utc)))
