# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33622735238` — implementation commit `d53910b663853246c6a0ec8155df9e0d1b33c900`: full CI completed successfully. Backend completed official Upstox protobuf verification plus non-integration and PostgreSQL integration pytest jobs; Android `assembleDebug` completed successfully.
- `33620032069` — implementation commit `d9f6338f81566c0488352d94a021d5a4b5a1b8cf`: Android `assembleDebug` completed successfully. Gradle Actions also reported all Gradle Wrapper jars valid in the CI environment.
- `33619901636` — preceding implementation state: backend completed official Upstox protobuf verification, **252 non-integration tests passed, 5 deselected, 1 warning**, and **5 PostgreSQL integration tests passed, 252 deselected, 1 warning**; Android `assembleDebug` completed successfully using the pinned Gradle 8.10.2 setup.
- `33619555439` — implementation commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`: backend and Android jobs both completed successfully; backend recorded **252 non-integration tests passed** and **5 PostgreSQL integration tests passed**.
- `33619555530` — Android-only workflow for commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`: `assembleDebug` completed successfully.
- `33619172631` — commit `021b82532e3e6efa276268425af7080f94f9bb2a`: backend completed successfully with **249 non-integration tests passed** and **5 PostgreSQL integration tests passed**.
- `33618698177` — commit `ef60eb80518ec8b858fa1b94a756930458bd8043`: backend and Android jobs both completed successfully; backend recorded **247 non-integration passed** and **4 PostgreSQL integration tests passed**.
- `33617134105` — commit `919253298d47ff2708bfb0c540292bff7c80c0cb`: backend completed successfully with **242 non-integration tests passed** and **4 PostgreSQL integration tests passed**; Android `assembleDebug` passed.
- `33617011571` — predecessor commit `c49a16791817542b5f2ea4c19e8090c558616b1a`: genuine failed verification retained below.

## Backend evidence

Run `33622735238` is the current full-CI verification for `d53910b663853246c6a0ec8155df9e0d1b33c900`. The backend job completed successfully, including official Upstox protobuf verification, the non-integration pytest suite, and the PostgreSQL integration suite. The corrected AI provider tests are therefore covered by the verified CI run.

The concrete `PostFillBrokerStateSynchronizer` is present in the execution package. It refreshes broker account/positions, binds derived risk state to the explicitly persisted session baseline, and requires an explicit risk-state sink. Unit/regression coverage verifies successful propagation and fail-closed behavior for refresh, baseline, and sink failures.

## Android evidence

Run `33622735238` also completed the Android `assembleDebug` job successfully using the CI workflow's pinned Gradle 8.10.2 setup. The Android AI integration remains advisory-only and does not authorize or execute broker orders.

Run `33620032069` independently verified `assembleDebug` for the preceding execution implementation state. The workflow's wrapper validation reported all wrapper JARs valid in the CI environment; this does not prove the repository contains the required official wrapper artifact.

## Current verification

The latest implementation commit before documentation updates is `d53910b663853246c6a0ec8155df9e0d1b33c900`, and its full CI run `33622735238` is green. Documentation commits record this evidence without changing runtime behavior.

## Historical failed verification

The predecessor implementation verification run `33617011571` failed because the newly hardened `RiskSnapshot` rejected non-finite P&L before the old test could exercise the gate. The test was corrected rather than weakening validation, and the corrected commit is green.

The initial position-refresh contract verification run `33614542133` failed with fixture incompatibilities after intentional safety hardening. The failure was investigated and corrected; it is retained here as evidence of genuine test-driven verification.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Broker-state synchronization requires an explicit daily-P&L baseline, and persisted-session binding resolves that baseline without inventing trading-day semantics. Post-fill confirmations have an explicit fail-closed synchronization boundary and a concrete provider-neutral synchronizer, but application wiring to a durable live-state sink remains unverified. Authoritative upstream trading-session lifecycle remains unimplemented. Recovery/provider failures remain fail-closed and credential-free.
