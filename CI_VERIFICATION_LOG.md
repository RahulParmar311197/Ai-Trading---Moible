# CI Verification Log

Last updated: 2026-09-04

## Verified passing runs

- `33854870591` — current `main` commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: **full CI completed successfully**. GitHub reports backend and Android jobs completed successfully; backend includes migrations, non-integration pytest, integration pytest, and official Upstox protobuf verification; Android completed `assembleDebug` with pinned Gradle 8.10.2.
- `33854870731` — current `main` commit `27b293eb41ea6645261f6212abdc6f5e65099a6c`: **Android CI completed successfully**.
- `33713476172` — prior main commit `8399d66e2d5d58f57c5c8e274229c9abb505d3c3`: full CI completed successfully.
- `33712940894` — prior main commit `e0fbf77b7fc55970a6d1d96a8f91d62a7e4a5821`: full CI completed successfully.

## Current verification

The latest full-CI verification is run `33854870591`, head `27b293eb41ea6645261f6212abdc6f5e65099a6c`, completed successfully on 2026-09-04. The latest commit adds regression coverage requiring Upstox and Dhan reconciliation to fail closed when broker order status is missing or blank.

The latest CI therefore verifies the broker reconciliation hardening currently on `main`, including backend tests and Android build.

## Backend evidence

The backend CI job for run `33854870591` completed successfully with PostgreSQL migrations, non-integration pytest, integration pytest, and official Upstox protobuf verification. The Dhan/Upstox missing-status reconciliation regression tests are included in this head.

Durable idempotency, broker position refresh, session-bound risk state, post-fill synchronization boundaries, emergency controls, and broker reconciliation remain covered by the repository's test suite and CI history.

## Android evidence

Run `33854870591` completed Android `assembleDebug` successfully. The Android AI integration remains advisory-only and does not authorize or execute broker orders.

## Runtime evidence

The project operator has confirmed that the **Upstox sandbox place/cancel smoke execution succeeded** using the repository's dedicated sandbox workflow/token path. This is recorded as operator-confirmed runtime evidence; the connected GitHub integration cannot inspect repository secrets or independently reproduce the secret-backed execution.

This sandbox result does not constitute production broker verification or live-money activation.

## Historical failed verification

Run `33712769202` for intermediate commit `f77b8996955ae426a71dc39e7dd4025ca0288d2e` failed only in backend non-integration tests because a fixed-date Dhan-auth fixture had expired relative to the 2026-09-03 runner date. The failing test was corrected in `7267d144b6bc7e4a5c6e0dc03d56889ecb85a879`; the corrected state was verified green by run `33712940894`.

The predecessor risk-state verification run `33617011571` failed because the newly hardened `RiskSnapshot` rejected non-finite P&L before the old test could exercise the gate. The test was corrected rather than weakening validation, and the corrected commit is green.

The initial position-refresh contract verification run `33614542133` failed with fixture incompatibilities after intentional safety hardening. The failure was investigated and corrected; it is retained as evidence of genuine test-driven verification.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. No local test execution is claimed from this environment. External broker and AI provider runtime claims are made only where explicitly evidenced or operator-confirmed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 production validation remain gated. Automated broker tests use deterministic synthetic client IDs. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Broker-state synchronization requires an explicit daily-P&L baseline, and persisted-session binding resolves that baseline without inventing trading-day semantics. Post-fill confirmations have an explicit fail-closed synchronization boundary. Recovery/provider failures remain fail-closed and credential-free.
