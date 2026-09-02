from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from .models import Fill, Order, Position


class PaperRepository(Protocol):
    """Persistence boundary for paper state; implementations must not reach live brokers."""

    def save_order(self, order: Order) -> None: ...

    def save_fill(self, fill: Fill) -> None: ...

    def save_position(self, position: Position) -> None: ...

    def delete_position(self, symbol: str) -> None: ...

    def append_audit(self, event_type: str, entity_id: str | None, payload: Mapping[str, Any]) -> None: ...


class PostgresPaperRepository:
    """PostgreSQL implementation using the existing provider-neutral SQL boundary."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def save_order(self, order: Order) -> None:
        self.db.execute(
            """
            INSERT INTO paper_orders
              (order_id, symbol, side, order_type, quantity, limit_price,
               created_at, status, filled_quantity, average_fill_price)
            VALUES
              (:order_id, :symbol, :side, :order_type, :quantity, :limit_price,
               :created_at, :status, :filled_quantity, :average_fill_price)
            ON CONFLICT (order_id) DO UPDATE SET
              status = EXCLUDED.status,
              filled_quantity = EXCLUDED.filled_quantity,
              average_fill_price = EXCLUDED.average_fill_price,
              updated_at = NOW()
            """,
            order.model_dump(mode="json"),
        )

    def save_fill(self, fill: Fill) -> None:
        self.db.execute(
            """
            INSERT INTO paper_fills (order_id, quantity, price, fee, timestamp)
            VALUES (:order_id, :quantity, :price, :fee, :timestamp)
            """,
            fill.model_dump(mode="json"),
        )

    def save_position(self, position: Position) -> None:
        self.db.execute(
            """
            INSERT INTO paper_positions
              (symbol, quantity, average_price, realized_pnl, unrealized_pnl)
            VALUES
              (:symbol, :quantity, :average_price, :realized_pnl, :unrealized_pnl)
            ON CONFLICT (symbol) DO UPDATE SET
              quantity = EXCLUDED.quantity,
              average_price = EXCLUDED.average_price,
              realized_pnl = EXCLUDED.realized_pnl,
              unrealized_pnl = EXCLUDED.unrealized_pnl,
              updated_at = NOW()
            """,
            position.model_dump(mode="json"),
        )

    def delete_position(self, symbol: str) -> None:
        self.db.execute("DELETE FROM paper_positions WHERE symbol = :symbol", {"symbol": symbol})

    def append_audit(self, event_type: str, entity_id: str | None, payload: Mapping[str, Any]) -> None:
        self.db.execute(
            """
            INSERT INTO paper_audit_events (event_type, entity_id, payload)
            VALUES (:event_type, :entity_id, CAST(:payload AS JSONB))
            """,
            {
                "event_type": event_type,
                "entity_id": entity_id,
                "payload": __import__("json").dumps(dict(payload), sort_keys=True, separators=(",", ":")),
            },
        )
