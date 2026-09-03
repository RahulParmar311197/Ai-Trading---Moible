from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .base import BrokerOrder, BrokerOrderStatus
from .idempotency import BrokerIdempotencyStore, IdempotencyConflict, IdempotencyPending


class DurableBrokerIdempotencyStore:
    """PostgreSQL-backed idempotency state that survives process restarts."""

    def __init__(self, db: Any) -> None:
        self.db = db

    @staticmethod
    def fingerprint(order: BrokerOrder) -> str:
        return BrokerIdempotencyStore.fingerprint(order)

    def begin(self, order: BrokerOrder) -> BrokerOrder | None:
        """Atomically claim a new key; never let two callers submit it."""
        key = order.client_order_id
        fingerprint = self.fingerprint(order)
        inserted = self.db.execute_returning(
            """
            INSERT INTO broker_idempotency_keys (client_order_id, fingerprint, result, updated_at)
            VALUES (:client_order_id, :fingerprint, NULL, :updated_at)
            ON CONFLICT (client_order_id) DO NOTHING
            RETURNING client_order_id
            """,
            {"client_order_id": key, "fingerprint": fingerprint, "updated_at": datetime.now(timezone.utc)},
        )
        if inserted is not None:
            return None

        row = self.db.fetch_one(
            "SELECT fingerprint, result FROM broker_idempotency_keys WHERE client_order_id = :client_order_id",
            {"client_order_id": key},
        )
        if row is None:
            raise RuntimeError("idempotency reservation disappeared")
        if row["fingerprint"] != fingerprint:
            raise IdempotencyConflict(f"client_order_id already used for a different order: {key}")
        if row["result"] is None:
            raise IdempotencyPending(f"client_order_id has an unresolved broker submission: {key}")
        stored_result = row["result"]
        if isinstance(stored_result, str):
            stored_result = json.loads(stored_result)
        return BrokerOrder.model_validate(stored_result)

    def complete(self, order: BrokerOrder, result: BrokerOrder) -> BrokerOrder:
        """Persist a broker result only when it matches the completion order."""
        key = order.client_order_id
        fingerprint = self.fingerprint(order)
        result_fingerprint = self.fingerprint(result)
        if result_fingerprint != fingerprint:
            # NEW/OPEN results are still subject to the controlled execution
            # confirmation validator. Never cache an identity-mismatched live
            # result, but allow that validator to report the precise mismatch.
            if result.status not in {BrokerOrderStatus.NEW, BrokerOrderStatus.OPEN}:
                raise IdempotencyConflict(
                    f"broker result does not match idempotency reservation: {key}"
                )
            return result
        self.db.execute(
            """
            INSERT INTO broker_idempotency_keys (client_order_id, fingerprint, result, updated_at)
            VALUES (:client_order_id, :fingerprint, CAST(:result AS JSONB), :updated_at)
            ON CONFLICT (client_order_id) DO NOTHING
            """,
            {
                "client_order_id": key,
                "fingerprint": fingerprint,
                "result": json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        self.db.execute(
            """
            UPDATE broker_idempotency_keys
            SET result = CAST(:result AS JSONB), updated_at = :updated_at
            WHERE client_order_id = :client_order_id AND fingerprint = :fingerprint
            """,
            {
                "client_order_id": key,
                "fingerprint": fingerprint,
                "result": json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        row = self.db.fetch_one(
            "SELECT client_order_id FROM broker_idempotency_keys WHERE client_order_id = :client_order_id AND fingerprint = :fingerprint AND result IS NOT NULL",
            {"client_order_id": key, "fingerprint": fingerprint},
        )
        if row is None:
            raise RuntimeError("idempotency reservation missing or fingerprint mismatch")
        return result

    def clear(self, client_order_id: str) -> None:
        """Clear only after broker state has been externally reconciled."""
        self.db.execute(
            "DELETE FROM broker_idempotency_keys WHERE client_order_id = :client_order_id",
            {"client_order_id": client_order_id},
        )
