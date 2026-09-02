# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33619555439` — implementation commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`: backend and Android jobs both completed successfully. Backend completed official Upstox protobuf verification, **252 non-integration tests passed, 5 deselected, 1 warning**, and **5 PostgreSQL integration tests passed, 252 deselected, 1 warning**; Android completed `assembleDebug` successfully using the pinned Gradle 8.10.2 workflow setup.
- `33619555530` — Android-only workflow for implementation commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`: `assembleDebug` completed successfully.
- `33619172631` — implementation commit `021b82532e3e6efa276268425af7080f94f9bb2a`: backend completed successfully with **249 non-integration tests passed, 5 deselected, 1 warning**, and **5 PostgreSQL integration tests passed, 249 deselected, 1 warning**.
- `33618698177` — commit `ef60eb80518ec8b858fa1b94a756930458bd8043`: backend and Android jobs both completed successfully. Backend completed official Upstox protobuf verification, **247 non-integration tests passed, 4 deselected, 1 warning**, and **4 PostgreSQL integration tests passed, 247 deselected, 1 warning**; Android completed `assembleDebug` successfully using the pinned Gradle 8.10.2.
- `33617703355` — status commit `8b92233209548d5121f80b4d1851a27de300a100`: backend and Android jobs both completed successfully.
- `33617703352` — Android-only workflow for status commit `8b92233209548d5121f80b4d1851a27de300a100`: `assembleDebug` completed successfully.
- `33617134105` — commit `919253298d47ff2708bfb0c540292bff7c80c0cb`: backend completed successfully with **242 non-integration tests passed, 4 deselected, 1 warning**, and **4 PostgreSQL integration tests passed, 242 deselected, 1 warning**; Android completed `assembleDebug` successfully.
- `33617134090` — Android-only workflow for commit `919253298d47ff2708bfb0c540292bff7c80c0cb`: `assembleDebug` completed successfully.
- `33614791892` — commit `45b0000f10f5afee87157df370afc5d8d5623a7d`: backend completed successfully with **235 non-integration tests passed, 4 deselected, 1 warning**, and **4 PostgreSQL integration tests passed, 235 deselected, 1 warning**; Android completed `assembleDebug` successfully.
- `33614031579` — commit `f7c9d3b2f6d0158bab4ed0b7555952a25b0d73c7`: backend completed successfully with **234 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33613147236` — confirmation-hardening commit: backend completed successfully with **229 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33612460702` — execution-gate hardening: backend completed successfully with **216 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33611954145` — unknown broker-status hardening: backend completed successfully with **213 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33602457519` — commit `1ef8f592fab8ea58dcc151d85d1f814aebe03541`: backend completed successfully with **211 non-integration tests passed** and **3 PostgreSQL integration tests passed**; Android completed `gradle assembleDebug` successfully.
- `33601890367` — commit `4bc648593e1fd26059507529bbf190e66e6cd4af`: backend completed successfully with **208 non-integration tests passed** and **3 PostgreSQL integration tests passed**; companion Android workflow run `33601890458` completed `gradle assembleDebug` successfully.
- `33601730753` — commit `1647774ef955ab7369b3c9932d20e608e6f9f4b6`: backend completed successfully with **204 non-integration tests passed** and **3 PostgreSQL integration tests passed**; Android `gradle assembleDebug` completed successfully.
- `33601518005` — commit `a18d1daf06984cdb596906e86b35dc07fca6929e`: backend and Android jobs both completed successfully.
- `33600557479` — commit `533f537a15489ec12d4bf1eb6611684845d874c0`: backend and Android debug build both completed successfully.
- `33600307751` — commit `4ec1cd983375f2cba91cf34a72514f37dcc78f05`: backend and Android debug build both completed successfully; backend completed **193 non-integration tests** and **3 PostgreSQL integration tests**.
- `33599917698` — commit `ce63a7a2eed00f171d1800fb2fab318ebc392a27`: backend and Android debug build both completed successfully; backend completed 192 non-integration tests and 3 PostgreSQL integration tests.
- `33599202340` — commit `8b241e958ddc98a821c80e82f34b2e4f281eb286`: backend and Android debug build both completed successfully; backend recorded 192 non-integration tests passed and 3 PostgreSQL integration tests passed.

## Backend evidence

Run `33619555439` checked out implementation commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6` on GitHub Actions with Python 3.12.14 and PostgreSQL 16. The official Upstox protobuf import succeeded. The non-integration suite reported **252 passed, 5 deselected, 1 warning in 1.23s**. The integration suite reported **5 passed, 252 deselected, 1 warning in 1.18s**. No provider credentials were used.

The post-fill execution boundary is now covered by regression tests: a `FILLED`/`PARTIALLY_FILLED` confirmation without a synchronization callback fails closed; a successful callback is invoked before the lifecycle remains active; and callback failure stops the lifecycle with the kill switch active. This is a lifecycle safety boundary, not an inferred account/P&L synchronization implementation.

## Android evidence

Run `33619555530` is the Android-only workflow for implementation commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`; `assembleDebug` completed successfully.

Run `33619555439` also completed its Android `assembleDebug` job successfully using the pinned Gradle 8.10.2 setup.

## Current verification

The latest implementation commit is `9b8611102a49b7f580e5111ae0ba1a29219e84e6`. Its backend and Android verification are green in run `33619555439`, with the companion Android-only run `33619555530` also green.

The latest documentation commit is `bef2c613f6d8d239e5e5fb9901fdf1a3a0c36a74`; its own CI verification must be observed before being recorded as passing.

## Historical failed verification

The predecessor implementation verification run `33617011571` failed because the newly hardened `RiskSnapshot` rejected non-finite P&L before the old test could exercise the gate. The test was corrected rather than weakening validation, and the corrected commit is green.

The initial position-refresh contract verification run `33614542133` failed with fixture incompatibilities after intentional safety hardening. The failure was investigated and corrected; it is retained here as evidence of genuine test-driven verification.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Broker-state synchronization requires an explicit daily-P&L baseline, and persisted-session binding resolves that baseline without inventing trading-day semantics. Post-fill confirmations now have an explicit fail-closed synchronization boundary, but concrete broker-state propagation into the live lifecycle remains unimplemented. Authoritative upstream trading-session lifecycle remains unimplemented. Recovery-provider failures remain fail-closed and credential-free.
