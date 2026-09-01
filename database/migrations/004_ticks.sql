-- Canonical market tick/trade storage.
-- The blueprint requires a ticks store but does not prescribe provider-specific
-- fields, so this table uses only the fields supported by the standard market
-- event contract plus a deterministic event identifier.
CREATE TABLE IF NOT EXISTS market_ticks (
    id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL REFERENCES instruments(id),
    timestamp TIMESTAMPTZ NOT NULL,
    price NUMERIC NOT NULL,
    volume NUMERIC NOT NULL DEFAULT 0,
    bid NUMERIC,
    ask NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT market_ticks_price_chk CHECK (price > 0),
    CONSTRAINT market_ticks_volume_chk CHECK (volume >= 0),
    CONSTRAINT market_ticks_bid_chk CHECK (bid IS NULL OR bid > 0),
    CONSTRAINT market_ticks_ask_chk CHECK (ask IS NULL OR ask > 0)
);

CREATE INDEX IF NOT EXISTS idx_market_ticks_instrument_time
    ON market_ticks (instrument_id, timestamp DESC);
