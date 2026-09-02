-- Durable controlled-execution audit state. Credential values are intentionally excluded.
CREATE TABLE IF NOT EXISTS execution_audit_events (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    client_order_id TEXT,
    reason TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_execution_audit_events_occurred_at
    ON execution_audit_events (occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_audit_events_client_order
    ON execution_audit_events (client_order_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_audit_events_type
    ON execution_audit_events (event_type, occurred_at DESC);
