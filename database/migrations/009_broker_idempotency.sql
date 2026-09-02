-- Durable broker idempotency state. Pending rows remain reserved across restarts.
CREATE TABLE IF NOT EXISTS broker_idempotency_keys (
    client_order_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    result JSONB,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_broker_idempotency_updated_at
    ON broker_idempotency_keys (updated_at DESC);
