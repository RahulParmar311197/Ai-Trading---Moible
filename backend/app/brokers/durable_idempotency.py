from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .base import BrokerOrder
from .idempotency import BrokerIdempotencyStore, IdempotencyConflict


class DurableBrokerIdempotencyStore:
    """PostgreSQL-backed idempotency state that survives process restarts."""

    def __init__(self, db: Any) -> None:
        self.db = db

    @staticmethod
    def fingerprint(order: BrokerOrder) -> str:
        return BrokerIdempotencyStore.fingerprint(order)

    def begin(self, order: BrokerOrder) -> BrokerOrder | None:
        key = order.client_order_id
        fingerprint = self.fingerprint(order)
        self.db.execute(
            """
            INSERT INTO broker_idempotency_keys (client_order_id, fingerprint, result, updated_at)
            VALUES (:client_order_id, :fingerprint, NULL, :updated_at)
            ON CONFLICT (client_order_id) DO NOTHING
            """,
            {"client_order_id": key, "fingerprint": fingerprint, "updated_at": datetime.now(timezone.utc)},
        )
        row = self.db.fetch_one(
            "SELECT fingerprint, result FROM broker_idempotency_keys WHERE client_order_id = :client_order_id",
            {"client_order_id": key},
        )
        if row is None:
            raise RuntimeError("idempotency reservation disappeared")
        if row["fingerprint"] != fingerprint:
            raise IdempotencyConflict(f"client_order_id already used for a different order: {key}")
        if row["result"] is None:
            return None
        return BrokerOrder.model_validate(row["result"])

    def complete(self, order: BrokerOrder, result: BrokerOrder) -> BrokerOrder:
        """Persist a broker result only against an existing matching reservation."""
        self.db.execute(
            """
            UPDATE broker_idempotency_keys
            SET result = CAST(:result AS JSONB), updated_at = :updated_at
            WHERE client_order_id = :client_order_id AND fingerprint = :fingerprint
            """,
            {
                "client_order_id": order.client_order_id,
                "fingerprint": self.fingerprint(order),
                "result": json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        row = self.db.fetch_one(
            "SELECT client_order_id FROM broker_idempotency_keys WHERE client_order_id = :client_order_id AND fingerprint = :fingerprint AND result IS NOT NULL",
            {"client_order_id": order.client_order_id, "fingerprint": self.fingerprint(order)},
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
