-- Durable paper-trading state. This remains isolated from live broker tables.
CREATE TABLE IF NOT EXISTS paper_orders (
    order_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type TEXT NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    limit_price NUMERIC,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('NEW', 'PARTIALLY_FILLED', 'FILLED', 'REJECTED', 'CANCELLED')),
    filled_quantity INTEGER NOT NULL DEFAULT 0 CHECK (filled_quantity >= 0),
    average_fill_price NUMERIC,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_paper_orders_created_at
    ON paper_orders (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_orders_symbol_status
    ON paper_orders (symbol, status);

CREATE TABLE IF NOT EXISTS paper_fills (
    id BIGSERIAL PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES paper_orders(order_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC NOT NULL CHECK (price > 0),
    fee NUMERIC NOT NULL DEFAULT 0 CHECK (fee >= 0),
    timestamp TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paper_fills_order_id
    ON paper_fills (order_id);
CREATE INDEX IF NOT EXISTS idx_paper_fills_timestamp
    ON paper_fills (timestamp DESC);

CREATE TABLE IF NOT EXISTS paper_positions (
    symbol TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL,
    average_price NUMERIC NOT NULL CHECK (average_price > 0),
    realized_pnl NUMERIC NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS paper_audit_events (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_id TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_paper_audit_events_created_at
    ON paper_audit_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_audit_events_entity
    ON paper_audit_events (entity_id, created_at DESC);
