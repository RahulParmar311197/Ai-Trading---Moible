# CI Verification Log

Last updated: 2026-09-04

## Verified passing runs

- `33862416980` — commit `b523e454c956b6887132dca3873803baeeae76d7`: **full CI completed successfully**. Backend dependency installation, official Upstox protobuf verification, PostgreSQL migrations, non-integration pytest (`380 passed, 6 deselected`), integration pytest (`5 passed, 1 skipped`), and Android `assembleDebug` all passed.
- `33858141630` — commit `cf0d8fd782e4172891dfb337af3bd21288ee741c`: full CI completed successfully.
- `33854870591` — prior main commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: full CI completed successfully.
- `33854870731` — prior main commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: Android CI completed successfully.

## Current verification

Run `33862416980` verifies the Dhan sandbox 403 classification regression commit. Backend and Android jobs both completed successfully. The backend run applied all PostgreSQL migrations, ran the full non-integration suite, and ran the integration suite.

The Dhan sandbox workflow requires `DHAN_SANDBOX_CLIENT_ID` and `DHAN_SANDBOX_ACCESS_TOKEN` repository secrets, targets the documented Dhan sandbox base URL through `DhanBroker(sandbox=True)`, performs account/positions/orders reads, and separately asserts that sandbox mutation remains disabled by default.

The Dhan sandbox workflow was hardened with a `/profile` authentication diagnostic before portfolio reads. The latest operator-executed runtime run reached that diagnostic and failed with HTTP 403 from the Dhan sandbox `/profile` request. This is a broker-authentication/runtime failure, not evidence of a successful sandbox connection; no portfolio read or mutation step was reached and no order was submitted.

The latest `main` change adds safe diagnostic classification for non-standard Dhan 403 responses without logging credentials or raw provider response bodies. A fresh sandbox workflow run is required to obtain the resulting provider-response classification.

## Runtime evidence

The project operator has confirmed that the **Upstox sandbox place/cancel smoke execution succeeded** using the repository's dedicated sandbox workflow/token path. This is operator-confirmed runtime evidence; the connected GitHub integration cannot inspect repository secrets or independently reproduce the secret-backed execution.

This sandbox result does not constitute production broker verification or live-money activation.

Dhan sandbox runtime verification remains **failed/blocked**: repository secrets are present in the workflow environment, but the sandbox `/profile` authentication request currently returns HTTP 403. The workflow remains read-only and mutation-gated. The failure must be resolved and a fresh successful `/profile` plus portfolio-read run obtained before Dhan sandbox runtime can be marked verified.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 production validation remain gated. Automated broker tests use deterministic synthetic client IDs. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Broker-state synchronization requires an explicit daily-P&L baseline, and persisted-session binding resolves that baseline without inventing trading-day semantics. Post-fill confirmations have an explicit fail-closed synchronization boundary. Recovery/provider failures remain fail-closed and credential-free.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. No local test execution is claimed from this environment. External broker and AI provider runtime claims are made only where explicitly evidenced or operator-confirmed.
