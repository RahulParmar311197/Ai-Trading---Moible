from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from .models import Fill, Order, Position


class PaperRepository(Protocol):
    """Persistence boundary for one authenticated paper account."""

    def save_order(self, order: Order) -> None: ...

    def save_fill(self, fill: Fill) -> None: ...

    def save_position(self, position: Position) -> None: ...

    def delete_position(self, symbol: str) -> None: ...

    def save_state(self, balance: Any, realized_pnl_total: Any, halted: bool) -> None: ...

    def load_orders(self) -> list[Order]: ...

    def load_fills(self) -> list[Fill]: ...

    def load_positions(self) -> list[Position]: ...

    def load_state(self) -> Mapping[str, Any] | None: ...

    def append_audit(self, event_type: str, entity_id: str | None, payload: Mapping[str, Any]) -> None: ...


class PostgresPaperRepository:
    """PostgreSQL persistence scoped to exactly one authenticated user."""

    def __init__(self, db: Any, user_id: UUID) -> None:
        self.db = db
        self.user_id = str(user_id)

    def save_order(self, order: Order) -> None:
        params = order.model_dump(mode="json")
        params["user_id"] = self.user_id
        self.db.execute(
            """
            INSERT INTO paper_user_orders
              (user_id, order_id, symbol, side, order_type, quantity, limit_price,
               created_at, status, filled_quantity, average_fill_price)
            VALUES
              (:user_id, :order_id, :symbol, :side, :order_type, :quantity, :limit_price,
               :created_at, :status, :filled_quantity, :average_fill_price)
            ON CONFLICT (user_id, order_id) DO UPDATE SET
              status = EXCLUDED.status,
              filled_quantity = EXCLUDED.filled_quantity,
              average_fill_price = EXCLUDED.average_fill_price,
              updated_at = NOW()
            """,
            params,
        )

    def save_fill(self, fill: Fill) -> None:
        params = fill.model_dump(mode="json")
        params["user_id"] = self.user_id
        self.db.execute(
            """
            INSERT INTO paper_user_fills (user_id, order_id, quantity, price, fee, timestamp)
            VALUES (:user_id, :order_id, :quantity, :price, :fee, :timestamp)
            """,
            params,
        )

    def save_position(self, position: Position) -> None:
        params = position.model_dump(mode="json")
        params["user_id"] = self.user_id
        self.db.execute(
            """
            INSERT INTO paper_user_positions
              (user_id, symbol, quantity, average_price, realized_pnl, unrealized_pnl)
            VALUES
              (:user_id, :symbol, :quantity, :average_price, :realized_pnl, :unrealized_pnl)
            ON CONFLICT (user_id, symbol) DO UPDATE SET
              quantity = EXCLUDED.quantity,
              average_price = EXCLUDED.average_price,
              realized_pnl = EXCLUDED.realized_pnl,
              unrealized_pnl = EXCLUDED.unrealized_pnl,
              updated_at = NOW()
            """,
            params,
        )

    def delete_position(self, symbol: str) -> None:
        self.db.execute(
            "DELETE FROM paper_user_positions WHERE user_id = :user_id AND symbol = :symbol",
            {"user_id": self.user_id, "symbol": symbol},
        )

    def save_state(self, balance: Any, realized_pnl_total: Any, halted: bool) -> None:
        self.db.execute(
            """
            INSERT INTO paper_user_account_state (user_id, balance, realized_pnl_total, halted)
            VALUES (:user_id, :balance, :realized_pnl_total, :halted)
            ON CONFLICT (user_id) DO UPDATE SET
              balance = EXCLUDED.balance,
              realized_pnl_total = EXCLUDED.realized_pnl_total,
              halted = EXCLUDED.halted,
              updated_at = NOW()
            """,
            {
                "user_id": self.user_id,
                "balance": balance,
                "realized_pnl_total": realized_pnl_total,
                "halted": halted,
            },
        )

    def load_orders(self) -> list[Order]:
        rows = self.db.fetch_all(
            """
            SELECT order_id, symbol, side, order_type, quantity, limit_price,
                   created_at, status, filled_quantity, average_fill_price
            FROM paper_user_orders
            WHERE user_id = :user_id
            ORDER BY created_at ASC, order_id ASC
            """,
            {"user_id": self.user_id},
        )
        return [Order.model_validate(row) for row in rows]

    def load_fills(self) -> list[Fill]:
        rows = self.db.fetch_all(
            """
            SELECT order_id, quantity, price, fee, timestamp
            FROM paper_user_fills
            WHERE user_id = :user_id
            ORDER BY timestamp ASC, id ASC
            """,
            {"user_id": self.user_id},
        )
        return [Fill.model_validate(row) for row in rows]

    def load_positions(self) -> list[Position]:
        rows = self.db.fetch_all(
            """
            SELECT symbol, quantity, average_price, realized_pnl, unrealized_pnl
            FROM paper_user_positions
            WHERE user_id = :user_id
            ORDER BY symbol ASC
            """,
            {"user_id": self.user_id},
        )
        return [Position.model_validate(row) for row in rows]

    def load_state(self) -> Mapping[str, Any] | None:
        return self.db.fetch_one(
            """
            SELECT balance, realized_pnl_total, halted
            FROM paper_user_account_state
            WHERE user_id = :user_id
            """,
            {"user_id": self.user_id},
        )

    def append_audit(self, event_type: str, entity_id: str | None, payload: Mapping[str, Any]) -> None:
        self.db.execute(
            """
            INSERT INTO paper_user_audit_events (user_id, event_type, entity_id, payload)
            VALUES (:user_id, :event_type, :entity_id, CAST(:payload AS JSONB))
            """,
            {
                "user_id": self.user_id,
                "event_type": event_type,
                "entity_id": entity_id,
                "payload": json.dumps(dict(payload), sort_keys=True, separators=(",", ":")),
            },
        )
