-- Canonical historical candle storage.
-- Keep provider-specific payloads outside this table; this is the normalized
-- representation used by replay, backtesting and strategy services.
CREATE TABLE IF NOT EXISTS market_candles (
    instrument_id TEXT NOT NULL REFERENCES instruments(id),
    timestamp TIMESTAMPTZ NOT NULL,
    timeframe TEXT NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume NUMERIC NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (instrument_id, timeframe, timestamp),
    CONSTRAINT market_candles_ohlc_chk CHECK (
        high >= GREATEST(open, close)
        AND low <= LEAST(open, close)
        AND low <= high
    ),
    CONSTRAINT market_candles_volume_chk CHECK (volume >= 0)
);

CREATE INDEX IF NOT EXISTS idx_market_candles_instrument_time
    ON market_candles (instrument_id, timestamp DESC);
