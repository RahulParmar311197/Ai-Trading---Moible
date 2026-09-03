CREATE TABLE IF NOT EXISTS execution_risk_state (
    session_id TEXT PRIMARY KEY,
    balance NUMERIC NOT NULL,
    realized_pnl NUMERIC NOT NULL,
    position_quantity INTEGER NOT NULL,
    halted BOOLEAN NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
