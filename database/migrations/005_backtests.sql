CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    request JSONB NOT NULL,
    report JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_backtests_created_at ON backtests (created_at DESC);
