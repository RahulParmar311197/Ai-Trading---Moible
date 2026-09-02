-- Authoritative daily-P&L baseline keyed by an explicit upstream risk-session id.
-- This table intentionally does not define market/trading-day boundaries.
CREATE TABLE IF NOT EXISTS risk_session_baselines (
    session_id TEXT PRIMARY KEY CHECK (length(trim(session_id)) > 0),
    daily_realized_pnl_baseline NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
