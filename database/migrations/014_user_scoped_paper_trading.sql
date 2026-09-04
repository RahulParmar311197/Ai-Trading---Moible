-- User-scoped durable paper trading state.
-- Existing legacy paper_* tables are intentionally left intact for safe migration history;
-- authenticated paper APIs use these user-scoped tables exclusively.

CREATE TABLE IF NOT EXISTS paper_user_account_state (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    balance NUMERIC NOT NULL,
    realized_pnl_total NUMERIC NOT NULL DEFAULT 0,
    halted BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS paper_user_orders (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type TEXT NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    limit_price NUMERIC,
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('NEW', 'PARTIALLY_FILLED', 'FILLED', 'REJECTED', 'CANCELLED')),
    filled_quantity INTEGER NOT NULL DEFAULT 0 CHECK (filled_quantity >= 0),
    average_fill_price NUMERIC,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, order_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_user_orders_created_at
    ON paper_user_orders (user_id, created_at DESC, order_id ASC);
CREATE INDEX IF NOT EXISTS idx_paper_user_orders_symbol_status
    ON paper_user_orders (user_id, symbol, status);

CREATE TABLE IF NOT EXISTS paper_user_fills (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC NOT NULL CHECK (price > 0),
    fee NUMERIC NOT NULL DEFAULT 0 CHECK (fee >= 0),
    timestamp TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (user_id, order_id) REFERENCES paper_user_orders(user_id, order_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_paper_user_fills_order_id
    ON paper_user_fills (user_id, order_id);
CREATE INDEX IF NOT EXISTS idx_paper_user_fills_timestamp
    ON paper_user_fills (user_id, timestamp DESC, id ASC);

CREATE TABLE IF NOT EXISTS paper_user_positions (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    average_price NUMERIC NOT NULL CHECK (average_price > 0),
    realized_pnl NUMERIC NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, symbol)
);

CREATE TABLE IF NOT EXISTS paper_user_audit_events (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    entity_id TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_paper_user_audit_created_at
    ON paper_user_audit_events (user_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_paper_user_audit_entity
    ON paper_user_audit_events (user_id, entity_id, created_at DESC);
