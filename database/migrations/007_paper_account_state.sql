-- Durable paper account state. This remains isolated from live broker tables.
CREATE TABLE IF NOT EXISTS paper_account_state (
    state_id SMALLINT PRIMARY KEY CHECK (state_id = 1),
    balance NUMERIC NOT NULL,
    realized_pnl_total NUMERIC NOT NULL DEFAULT 0,
    halted BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
