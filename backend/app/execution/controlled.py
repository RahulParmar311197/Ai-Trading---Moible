from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Awaitable, Callable, Protocol, Sequence

from app.brokers.base import BrokerAuthentication, BrokerOrder, BrokerOrderStatus, BrokerPosition, BrokerReconciliation
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


PostFillStateSynchronizer = Callable[[BrokerOrder], Awaitable[None]]


@dataclass(frozen=True)
class ExecutionAuditEvent:
    event_type: str
    client_order_id: str
    reason: str
    timestamp: datetime


class ControlledExecutionError(RuntimeError):
    """Raised when a controlled live-execution prerequisite is not satisfied."""


class ControlledBrokerExecution:
    """Explicitly activated broker execution with deterministic safety gates."""

    def __init__(self, broker: ExecutionBroker, risk_gate: DeterministicExecutionGate, *, confirmation_phrase: str, audit_sink: Callable[[ExecutionAuditEvent], None] | None = None, idempotency_store: BrokerIdempotencyStore, post_fill_state_sync: PostFillStateSynchronizer | None = None) -> None:
        if not confirmation_phrase.strip():
            raise ValueError("confirmation phrase must be non-empty")
        self._idempotency_store = idempotency_store
        self._broker = IdempotentBroker(broker, idempotency_store)
        self._risk_gate = risk_gate
        self._confirmation_phrase = confirmation_phrase
        self._audit_sink = audit_sink
        self._post_fill_state_sync = post_fill_state_sync
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
            live_statuses = {BrokerOrderStatus.NEW, BrokerOrderStatus.OPEN, BrokerOrderStatus.PARTIALLY_FILLED}
            unexpected_live_orders = tuple(order for order in broker_orders if order.status in live_statuses and order.client_order_id not in expected_ids)
            if unexpected_live_orders:
                client_order_id = unexpected_live_orders[0].client_order_id
                self._audit("RECONCILIATION_REQUIRED", client_order_id, "broker reported live order outside expected local order set")
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
                if reconciliation.broker_status in {BrokerOrderStatus.REJECTED, BrokerOrderStatus.CANCELLED}:
                    self._idempotency_store.clear(client_order_id)
                    self._audit("IDEMPOTENCY_RESERVATION_CLEARED", client_order_id, "broker reconciliation reached a terminal non-live status")
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
        if not reason.strip():
            raise ValueError("shutdown reason must be non-empty")
        self._activated = False
        self._kill_switch = True
        self._started = False
        self._audit("EXECUTION_SHUTDOWN", "", reason)

    async def submit(self, order: BrokerOrder, *, market_price: Decimal, snapshot: RiskSnapshot) -> BrokerOrder:
        if not self._started:
            self._reject(order.client_order_id, "execution startup has not completed")
        if not self._activated:
            self._reject(order.client_order_id, "live execution is not activated")
        if self._kill_switch:
            self._reject(order.client_order_id, "live execution kill switch is active")
        await self._validate_fresh_position(order, snapshot)
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
            self._audit("BROKER_SUBMISSION_FAILED", order.client_order_id, f"broker submission failed: {type(exc).__name__}; execution fail-closed pending reconciliation")
            raise
        try:
            self._validate_confirmation(order, result)
        except ControlledExecutionError as exc:
            self._started = False
            self._activated = False
            self._kill_switch = True
            self._audit("BROKER_CONFIRMATION_INVALID", order.client_order_id, str(exc))
            raise
        if result.status is BrokerOrderStatus.REJECTED:
            self._audit("BROKER_REJECTED", order.client_order_id, "broker rejected order")
            raise ControlledExecutionError("broker rejected order")
        if result.status in {BrokerOrderStatus.PARTIALLY_FILLED, BrokerOrderStatus.FILLED}:
            await self._synchronize_post_fill_state(result)
        self._audit("BROKER_CONFIRMED", order.client_order_id, result.status.value)
        return result

    async def _synchronize_post_fill_state(self, result: BrokerOrder) -> None:
        if self._post_fill_state_sync is None:
            self._started = False
            self._activated = False
            self._kill_switch = True
            self._audit("POST_FILL_STATE_SYNC_REQUIRED", result.client_order_id, "filled broker confirmation requires an explicit post-fill state synchronizer; execution fail-closed")
            raise ControlledExecutionError("post-fill broker state synchronization is required")
        try:
            await self._post_fill_state_sync(result)
        except Exception as exc:
            self._started = False
            self._activated = False
            self._kill_switch = True
            self._audit("POST_FILL_STATE_SYNC_FAILED", result.client_order_id, f"post-fill broker state synchronization failed: {type(exc).__name__}; execution fail-closed")
            raise ControlledExecutionError("post-fill broker state synchronization failed") from exc
        self._audit("POST_FILL_STATE_SYNCHRONIZED", result.client_order_id, "post-fill broker state synchronization completed")

    async def _validate_fresh_position(self, order: BrokerOrder, snapshot: RiskSnapshot) -> None:
        get_positions = getattr(self._broker, "get_positions", None)
        if not callable(get_positions):
            self._reject(order.client_order_id, "broker position boundary unavailable")
        try:
            positions = await get_positions()
        except Exception as exc:
            self._started = False
            self._activated = False
            self._kill_switch = True
            self._audit("POSITION_REFRESH_FAILED", order.client_order_id, f"broker position refresh failed: {type(exc).__name__}; execution fail-closed")
            raise
        if not isinstance(positions, (tuple, list)) or any(not isinstance(position, BrokerPosition) for position in positions):
            self._started = False
            self._activated = False
            self._kill_switch = True
            self._audit("POSITION_REFRESH_INVALID", order.client_order_id, "broker returned invalid position state")
            raise ControlledExecutionError("broker returned invalid position state")
        broker_quantity = sum(position.quantity for position in positions if position.symbol == order.symbol)
        if broker_quantity != snapshot.position_quantity:
            self._started = False
            self._activated = False
            self._kill_switch = True
            self._audit("POSITION_STATE_MISMATCH", order.client_order_id, "broker position differs from supplied risk snapshot; execution fail-closed")
            raise ControlledExecutionError("broker position differs from supplied risk snapshot")

    @staticmethod
    def _validate_confirmation(submitted: BrokerOrder, result: BrokerOrder) -> None:
        if result.client_order_id != submitted.client_order_id:
            raise ControlledExecutionError("broker confirmation client order id mismatch")
        if result.symbol != submitted.symbol:
            raise ControlledExecutionError("broker confirmation symbol mismatch")
        if result.side is not submitted.side:
            raise ControlledExecutionError("broker confirmation side mismatch")
        if result.order_type is not submitted.order_type:
            raise ControlledExecutionError("broker confirmation order type mismatch")
        if result.quantity != submitted.quantity:
            raise ControlledExecutionError("broker confirmation quantity mismatch")
        if result.filled_quantity > result.quantity:
            raise ControlledExecutionError("broker confirmation filled quantity exceeds order quantity")
        if result.status is BrokerOrderStatus.FILLED and result.filled_quantity != result.quantity:
            raise ControlledExecutionError("filled broker confirmation has incomplete fill quantity")
        if result.status is BrokerOrderStatus.PARTIALLY_FILLED and not 0 < result.filled_quantity < result.quantity:
            raise ControlledExecutionError("partial broker confirmation has invalid fill quantity")
        if result.average_price is not None and (not result.average_price.is_finite() or result.average_price <= 0):
            raise ControlledExecutionError("broker confirmation average price must be finite and positive")

    def _reject(self, client_order_id: str, reason: str) -> None:
        self._audit("EXECUTION_REJECTED", client_order_id, reason)
        raise ControlledExecutionError(reason)

    def _audit(self, event_type: str, client_order_id: str, reason: str) -> None:
        if self._audit_sink is not None:
            self._audit_sink(ExecutionAuditEvent(event_type, client_order_id, reason, datetime.now(timezone.utc)))
