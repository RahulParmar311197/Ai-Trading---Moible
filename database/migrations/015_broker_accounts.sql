-- User-owned broker account metadata.
-- Secrets are intentionally not stored here; credential_ref is an opaque reference
-- to an external secret-management boundary owned by the deployment.
CREATE TABLE IF NOT EXISTS broker_accounts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('UPSTOX', 'DHAN')),
    environment TEXT NOT NULL CHECK (environment IN ('SANDBOX', 'LIVE')),
    external_account_id TEXT NOT NULL,
    credential_ref TEXT,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT broker_accounts_external_account_id_chk
        CHECK (length(trim(external_account_id)) > 0),
    CONSTRAINT broker_accounts_credential_ref_chk
        CHECK (credential_ref IS NULL OR length(trim(credential_ref)) > 0),
    UNIQUE (user_id, provider, environment),
    UNIQUE (provider, environment, external_account_id)
);

CREATE INDEX IF NOT EXISTS idx_broker_accounts_user
    ON broker_accounts (user_id, provider, environment);

CREATE INDEX IF NOT EXISTS idx_broker_accounts_enabled
    ON broker_accounts (enabled)
    WHERE enabled = TRUE;
