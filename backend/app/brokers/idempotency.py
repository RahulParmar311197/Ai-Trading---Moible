from __future__ import annotations

import hashlib
import json
from typing import Protocol

from .base import BrokerOrder


class IdempotencyConflict(ValueError):
    """Raised when a client reuses an idempotency key for a different order."""


class IdempotencyPending(RuntimeError):
    """Raised when a prior submission is unresolved and must be reconciled first."""


class IdempotencyStore(Protocol):
    """Provider-neutral persistence boundary for broker idempotency state."""

    def begin(self, order: BrokerOrder) -> BrokerOrder | None: ...

    def complete(self, order: BrokerOrder, result: BrokerOrder) -> BrokerOrder: ...

    def clear(self, client_order_id: str) -> None: ...


class BrokerIdempotencyStore:
    """In-memory idempotency registry for a single broker process.

    The registry never creates or authorizes orders. It prevents the same
    client_order_id from being submitted twice and rejects conflicting reuse.
    Production controlled-live execution should use a durable implementation.
    """

    def __init__(self) -> None:
        self._requests: dict[str, str] = {}
        self._results: dict[str, BrokerOrder] = {}

    @staticmethod
    def fingerprint(order: BrokerOrder) -> str:
        payload = {
            "client_order_id": order.client_order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "order_type": order.order_type.value,
            "quantity": order.quantity,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def begin(self, order: BrokerOrder) -> BrokerOrder | None:
        key = order.client_order_id
        fingerprint = self.fingerprint(order)
        previous = self._requests.get(key)
        if previous is not None and previous != fingerprint:
            raise IdempotencyConflict(
                f"client_order_id already used for a different order: {key}"
            )
        if previous is not None:
            cached = self._results.get(key)
            if cached is not None:
                return cached
            raise IdempotencyPending(
                f"client_order_id has an unresolved broker submission: {key}"
            )
        self._requests[key] = fingerprint
        return None

    def complete(self, order: BrokerOrder, result: BrokerOrder) -> BrokerOrder:
        key = order.client_order_id
        fingerprint = self.fingerprint(order)
        if self.fingerprint(result) != fingerprint:
            raise IdempotencyConflict(
                f"broker result does not match idempotency reservation: {key}"
            )
        previous = self._requests.get(key)
        if previous is None:
            # Recovery may discover a terminal broker order whose reservation
            # was not loaded into this process. The authoritative broker order
            # itself is the only safe basis for reconstructing that reservation.
            self._requests[key] = fingerprint
        elif previous != fingerprint:
            raise IdempotencyConflict(
                f"client_order_id reservation does not match completion order: {key}"
            )
        self._results[key] = result
        return result

    def clear(self, client_order_id: str) -> None:
        """Forget a key only after the caller has externally resolved its state.

        A broker submission exception can be ambiguous: the broker may have
        accepted the order even when the client observed a timeout or transport
        error. Therefore the idempotent decorator intentionally does not clear
        failed submissions automatically. Reconciliation must resolve the
        broker state before explicitly clearing a key for a fresh submission.
        """
        self._requests.pop(client_order_id, None)
        self._results.pop(client_order_id, None)


class IdempotentBroker:
    """Provider-neutral broker decorator enforcing client-order idempotency."""

    def __init__(self, broker: object, store: IdempotencyStore) -> None:
        self._broker = broker
        self._idempotency = store

    @property
    def idempotency(self) -> IdempotencyStore:
        return self._idempotency

    async def place_order(self, order: BrokerOrder) -> BrokerOrder:
        cached = self._idempotency.begin(order)
        if cached is not None:
            return cached
        try:
            result = await self._broker.place_order(order)
        except Exception:
            # Preserve the idempotency reservation because the broker may have
            # accepted the order before a transport/provider error was observed.
            # Reconciliation must resolve the ambiguous state before reuse.
            raise
        return self._idempotency.complete(order, result)

    def __getattr__(self, name: str) -> object:
        return getattr(self._broker, name)
