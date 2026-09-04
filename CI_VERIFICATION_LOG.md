# CI Verification Log

Last updated: 2026-09-04

## Verified passing runs

- `33858141630` — commit `cf0d8fd782e4172891dfb337af3bd21288ee741c`: **full CI completed successfully**. Backend dependencies, official Upstox protobuf verification, PostgreSQL migrations, non-integration pytest, integration pytest, and Android `assembleDebug` all passed.
- `33854870591` — prior main commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: full CI completed successfully.
- `33854870731` — prior main commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: Android CI completed successfully.

## Current verification

Run `33858141630` verifies the broker authentication transport regression commit. Tests explicitly verify Dhan uses `access-token` without Bearer and Upstox retains `Authorization: Bearer`.

Commit `6eef5fa655f1c3bd63e52f581769264881cf546c` adds a manual Dhan sandbox read-only smoke workflow. The workflow requires `DHAN_SANDBOX_CLIENT_ID` and `DHAN_SANDBOX_ACCESS_TOKEN` repository secrets, targets the documented Dhan sandbox base URL through `DhanBroker(sandbox=True)`, performs account/positions/orders reads, and separately asserts that sandbox mutation remains disabled by default.

The Dhan sandbox workflow was subsequently hardened with a `/profile` authentication diagnostic before portfolio reads. The latest operator-executed run reached that diagnostic and failed with HTTP 403 from the Dhan sandbox `/profile` request. This is a broker-authentication/runtime failure, not evidence of a successful sandbox connection; no mutation step was reached and no order was submitted.

## Runtime evidence

The project operator has confirmed that the **Upstox sandbox place/cancel smoke execution succeeded** using the repository's dedicated sandbox workflow/token path. This is operator-confirmed runtime evidence; the connected GitHub integration cannot inspect repository secrets or independently reproduce the secret-backed execution.

This sandbox result does not constitute production broker verification or live-money activation.

Dhan sandbox runtime verification remains **failed/blocked**: repository secrets are present in the workflow environment, but the sandbox `/profile` authentication request currently returns HTTP 403. The workflow remains read-only and mutation-gated. The failure must be resolved and a fresh successful `/profile` plus portfolio-read run obtained before Dhan sandbox runtime can be marked verified.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 production validation remain gated. Automated broker tests use deterministic synthetic client IDs. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Broker-state synchronization requires an explicit daily-P&L baseline, and persisted-session binding resolves that baseline without inventing trading-day semantics. Post-fill confirmations have an explicit fail-closed synchronization boundary. Recovery/provider failures remain fail-closed and credential-free.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. No local test execution is claimed from this environment. External broker and AI provider runtime claims are made only where explicitly evidenced or operator-confirmed.
