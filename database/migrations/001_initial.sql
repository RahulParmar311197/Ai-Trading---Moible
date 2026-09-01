-- Initial database foundation.
-- Trading/domain tables will be introduced in later migrations.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(32) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations(version)
VALUES ('001_initial')
ON CONFLICT (version) DO NOTHING;
