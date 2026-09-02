# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33625211010` — documentation commit `23b9f479d5f776dd92cc2e73395221d23c0a71e6`: **full CI completed successfully**. GitHub reports `backend-tests` and `android-build` both completed successfully. Backend completed official Upstox protobuf verification, non-integration pytest, and PostgreSQL integration pytest; Android completed `assembleDebug` using pinned Gradle 8.10.2.
- `33624319414` — implementation commit `ba78f6ff248d6f7e08cb47963997e868868be12f`: **full CI completed successfully**. Backend completed official Upstox protobuf verification, non-integration pytest, and PostgreSQL integration pytest; Android `assembleDebug` completed successfully.
- `33623091606` — documentation commit `f929c6b60bde69dd42d7e5b7a7ce778f01c752fd`: full CI completed successfully. Backend completed official Upstox protobuf verification plus non-integration and PostgreSQL integration pytest jobs; Android `assembleDebug` completed successfully using pinned Gradle 8.10.2.
- `33622735238` — implementation commit `d53910b663853246c6a0ec8155df9e0d1b33c900`: full CI completed successfully. Backend and Android jobs both completed successfully.
- `33620032069` — implementation commit `d9f6338f81566c0488352d94a021d5a4b5a1b8cf`: Android `assembleDebug` completed successfully.
- `33619901636` — preceding implementation state: backend completed official Upstox protobuf verification, 252 non-integration tests passed, 5 deselected, 1 warning, and 5 PostgreSQL integration tests passed; Android `assembleDebug` completed successfully.
- `33619555439` — implementation commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`: backend and Android jobs both completed successfully.
- `33617134105` — commit `919253298d47ff2708b0c540292bff7c80c0cb`: backend completed successfully with 242 non-integration tests passed and 4 PostgreSQL integration tests passed; Android `assembleDebug` passed.

## Backend evidence

Run `33625211010` is the latest full-CI verification. Its backend job `100231227978` completed successfully for official Upstox protobuf verification, non-integration pytest, and PostgreSQL integration pytest. Its Android job `100231227972` also completed successfully, including `gradle assembleDebug`.

The paper-trading hardening in `ba78f6ff248d6f7e08cb47963997e868868be12f` therefore has full CI verification. The tests specifically cover fail-closed financial-input validation without weakening the underlying validation.

The concrete `PostFillBrokerStateSynchronizer` remains provider-neutral and tested; it refreshes broker state, binds risk state to an explicitly persisted session baseline, and requires an explicit risk-state sink.

## Android evidence

Run `33625211010` completed Android `assembleDebug` successfully. The Android AI integration remains advisory-only and does not authorize or execute broker orders.

## Current verification

The latest full-CI verification is `33625211010` and is green. Documentation records only observed GitHub Actions evidence.

## Historical failed verification

The predecessor risk-state verification run `33617011571` failed because the newly hardened `RiskSnapshot` rejected non-finite P&L before the old test could exercise the gate. The test was corrected rather than weakening validation, and the corrected commit is green.

The initial position-refresh contract verification run `33614542133` failed with fixture incompatibilities after intentional safety hardening. The failure was investigated and corrected; it is retained here as evidence of genuine test-driven verification.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Broker-state synchronization requires an explicit daily-P&L baseline, and persisted-session binding resolves that baseline without inventing trading-day semantics. Post-fill confirmations have an explicit fail-closed synchronization boundary and a concrete provider-neutral synchronizer, but application wiring to a durable live-state sink remains unverified. The authoritative upstream trading-session lifecycle remains unimplemented. Recovery/provider failures remain fail-closed and credential-free.
