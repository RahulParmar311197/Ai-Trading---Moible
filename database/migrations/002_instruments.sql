-- Instrument master data. Provider-specific identifiers may be added later
-- without changing the canonical domain model.
CREATE TABLE IF NOT EXISTS instruments (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    market TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    underlying TEXT,
    expiry TIMESTAMPTZ,
    strike NUMERIC,
    option_type TEXT,
    lot_size INTEGER,
    tick_size NUMERIC,
    currency TEXT NOT NULL DEFAULT 'INR',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT instruments_option_type_chk
        CHECK (option_type IS NULL OR option_type IN ('CE', 'PE')),
    CONSTRAINT instruments_lot_size_chk
        CHECK (lot_size IS NULL OR lot_size > 0),
    CONSTRAINT instruments_tick_size_chk
        CHECK (tick_size IS NULL OR tick_size > 0)
);

CREATE INDEX IF NOT EXISTS idx_instruments_symbol_exchange
    ON instruments (symbol, exchange);

CREATE INDEX IF NOT EXISTS idx_instruments_active
    ON instruments (active);
