from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Protocol

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus
from app.brokers.idempotency import BrokerIdempotencyStore, IdempotentBroker

from .gate import DeterministicExecutionGate, RiskSnapshot


class ExecutionBroker(Protocol):
    async def place_order(self, order: BrokerOrder) -> BrokerOrder: ...


class ExecutionLifecycleBroker(ExecutionBroker, Protocol):
    async def authenticate(self) -> BrokerAuthentication: ...


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
    activation phrase, a successful authenticated broker session, and a clear
    kill switch. Every mutation passes risk evaluation and idempotency.
    """

    def __init__(
        self,
        broker: ExecutionBroker,
        risk_gate: DeterministicExecutionGate,
        *,
        confirmation_phrase: str,
        audit_sink: Callable[[ExecutionAuditEvent], None] | None = None,
        idempotency_store: BrokerIdempotencyStore | None = None,
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
            self._audit(
                "BROKER_SUBMISSION_FAILED",
                order.client_order_id,
                f"broker submission failed: {type(exc).__name__}",
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
