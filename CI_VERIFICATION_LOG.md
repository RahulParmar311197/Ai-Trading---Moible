# CI Verification Log

Last updated: 2026-09-04

## Verified passing runs

- `33862416980` — commit `b523e454c956b6887132dca3873803baeeae76d7`: **full CI completed successfully**. Backend dependency installation, official Upstox protobuf verification, PostgreSQL migrations, non-integration pytest (`380 passed, 6 deselected`), integration pytest (`5 passed, 1 skipped`), and Android `assembleDebug` all passed.
- `33858141630` — commit `cf0d8fd782e4172891dfb337af3bd21288ee741c`: full CI completed successfully.
- `33862899646` — commit `a8bd8eb88531dbb26bb328ad58aa3b4a05817ce2`: Android CI completed successfully.
- `33854870591` — prior main commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: full CI completed successfully.
- `33854870731` — prior main commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: Android CI completed successfully.

## Current verification

Main is currently at the documentation-only verification commit `a8bd8eb88531dbb26bb328ad58aa3b4a05817ce2`. Android CI for that commit completed successfully in run `33862899646`.

The Dhan sandbox workflow requires `DHAN_SANDBOX_CLIENT_ID` and `DHAN_SANDBOX_ACCESS_TOKEN` repository secrets, targets the documented Dhan sandbox base URL through `DhanBroker(sandbox=True)`, performs account/positions/orders reads, and separately asserts that sandbox mutation remains disabled by default.

The latest operator-executed Dhan Sandbox Read-Only Smoke run `33863069710` reached the direct `/profile` diagnostic and failed with HTTP 403. The response metadata was: content type `text/html`, server `awselb/2.0`, body length 118 bytes, and non-JSON response. A SHA-256 body digest was logged without exposing the response body or credentials.

Because the response is non-JSON and originates from an AWS load-balancer response path, the run did not reach application-level Dhan authentication, account/positions/orders reads, or any mutation test. No order was submitted. This is runtime evidence of an external sandbox HTTP failure, not evidence of successful Dhan sandbox authentication.

## Runtime evidence

The project operator has confirmed that the **Upstox sandbox place/cancel smoke execution succeeded** using the repository's dedicated sandbox workflow/token path. This is operator-confirmed runtime evidence; the connected GitHub integration cannot inspect repository secrets or independently reproduce the secret-backed execution.

This sandbox result does not constitute production broker verification or live-money activation.

Dhan sandbox runtime verification remains **failed/blocked**. Repository secrets are present in the workflow environment, but the sandbox `/profile` request currently returns HTTP 403 with a non-JSON AWS load-balancer response. The workflow remains read-only and mutation-gated. A successful `/profile` plus account/positions/orders read run is required before Dhan sandbox runtime can be marked verified.

## External documentation cross-check

Current DhanHQ documentation states that the User Profile API is a simple GET used to validate access-token validity/account setup and documents the `access-token` header. Dhan's sandbox documentation separately identifies `https://sandbox.dhan.co/v2/` as the sandbox base URL and requires separate sandbox credentials. The current Dhan error documentation describes API-level failures as structured error responses; the observed HTML 403 therefore does not provide a Dhan error code such as `DH-901` or `DH-902`. citeturn1search0turn1search10turn0search7

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 production validation remain gated. Automated broker tests use deterministic synthetic client IDs. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Broker-state synchronization requires an explicit daily-P&L baseline, and persisted-session binding resolves that baseline without inventing trading-day semantics. Post-fill confirmations have an explicit fail-closed synchronization boundary. Recovery/provider failures remain fail-closed and credential-free.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. No local test execution is claimed from this environment. External broker and AI provider runtime claims are made only where explicitly evidenced or operator-confirmed.
