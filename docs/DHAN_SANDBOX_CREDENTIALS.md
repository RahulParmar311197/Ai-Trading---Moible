# Dhan Sandbox Credentials

Dhan sandbox credentials must be supplied through the environment that is actually running the test. Never commit credentials to the repository.

## Codespaces

Create these two **Codespaces secrets** with the exact names below:

- `DHAN_SANDBOX_CLIENT_ID`
- `DHAN_SANDBOX_ACCESS_TOKEN`

Codespaces exposes configured secrets to the Codespace as environment variables. After creating or changing a Codespaces secret, restart/rebuild the Codespace as needed so the environment receives the updated value.

Verify presence without printing the values:

```bash
python - <<'PY'
import os
for name in ("DHAN_SANDBOX_CLIENT_ID", "DHAN_SANDBOX_ACCESS_TOKEN"):
    print(f"{name}: {'configured' if os.getenv(name) else 'missing'}")
PY
```

Do **not** echo the token, include it in command arguments, commit a `.env` containing it, or place it in logs.

## GitHub Actions

Codespaces secrets are separate from GitHub Actions secrets. The manual workflow `.github/workflows/dhan-sandbox-readonly.yml` therefore reads:

- repository/environment secret `DHAN_SANDBOX_CLIENT_ID`
- repository/environment secret `DHAN_SANDBOX_ACCESS_TOKEN`

The workflow first checks that both are non-empty and then performs a read-only Dhan sandbox authentication/profile check. The workflow does not obtain credentials from the Codespace.

## Required separation

```text
Codespaces secret
  -> Codespace environment
  -> local development / diagnostic commands

GitHub Actions secret
  -> dhan-sandbox-readonly.yml
  -> Dhan sandbox smoke test
```

Using the same secret names in both places is intentional, but the secret stores are independent. Updating a Codespaces secret does not update the GitHub Actions secret, and vice versa.

## Dhan sandbox safety

The application must remain fail-closed. Sandbox configuration does not authorize live orders. The Dhan sandbox workflow explicitly verifies that the default mutation gate rejects order submission.

A successful credential configuration check is **not** evidence that Dhan authentication or runtime access works. Runtime verification requires a successful `/profile` response followed by account, positions, and orders reads. The current project must not claim Dhan sandbox runtime success until those checks pass.

If `/profile` returns an upstream 403 or another authentication/network failure, diagnose the provider response without exposing credentials and do not bypass the failure by adding guessed headers or disabling safety gates.
