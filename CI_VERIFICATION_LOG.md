# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33614791892` — commit `45b0000f10f5afee87157df370afc5d8d5623a7d`: backend completed successfully with **235 non-integration tests passed, 4 deselected, 1 warning**, and **4 PostgreSQL integration tests passed, 235 deselected, 1 warning**; Android completed `assembleDebug` successfully. This verifies the latest controlled-live position-state hardening and corrected fixtures.
- `33614031579` — commit `f7c9d3b2f6d0158bab4ed0b7555952a25b0d73c7`: backend completed successfully with **234 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33613147236` — confirmation-hardening commit: backend completed successfully with **229 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33612460702` — execution-gate hardening: backend completed successfully with **216 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33611954145` — unknown broker-status hardening: backend completed successfully with **213 non-integration tests passed and 4 integration tests passed**; Android completed `assembleDebug` successfully.
- `33602457519` — commit `1ef8f592fab8ea58dcc151d85d1f814aebe03541`: backend completed successfully with **211 non-integration tests passed** and **3 PostgreSQL integration tests passed**; Android completed `gradle assembleDebug` successfully. This verifies terminal broker idempotency reservation clearing after reconciled `REJECTED`/`CANCELLED` states.
- `33601890367` — commit `4bc648593e1fd26059507529bbf190e66e6cd4af`: backend completed successfully with **208 non-integration tests passed** and **3 PostgreSQL integration tests passed**. The companion Android workflow run `33601890458` for the same commit completed `gradle assembleDebug` successfully.
- `33601730753` — commit `1647774ef955ab7369b3c9932d20e608e6f9f4b6`: backend completed successfully with **204 non-integration tests passed** and **3 PostgreSQL integration tests passed**; Android `gradle assembleDebug` completed successfully. This verifies fail-closed broker submission failure handling and its regression test.
- `33601518005` — commit `a18d1daf06984cdb596906e86b35dc07fca6929e`: backend and Android jobs both completed successfully. This verifies the explicit idempotency-store requirement.
- `33600557479` — commit `533f537a15489ec12d4bf1eb6611684845d874c0`: backend and Android debug build both completed successfully. Backend verified Dhan submission-status semantics and regression coverage.
- `33600307751` — commit `4ec1cd983375f2cba91cf34a72514f37dcc78f05`: backend tests and Android debug build both completed successfully. Backend completed dependency installation, official Upstox protobuf verification, **193 non-integration tests**, and **3 PostgreSQL integration tests**; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies broker-session error sanitization and the accumulated controlled-live safety suite.
- `33599917698` — commit `ce63a7a2eed00f171d1800fb2fab318ebc392a27`: backend tests and Android debug build both completed successfully. Backend completed dependency installation, official Upstox protobuf verification, 192 non-integration tests, and 3 PostgreSQL integration tests; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies durable idempotency completion persistence and its reservation-guard regression coverage.
- `33599202340` — commit `8b241e958ddc98a821c80e82f34b2e4f281eb286`: backend tests and Android debug build both completed successfully. Backend recorded 192 non-integration tests passed and 3 PostgreSQL integration tests passed; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies unexpected broker live-order recovery hardening and regression coverage.

## Backend evidence

Run `33614791892` checked out commit `45b0000f10f5afee87157df370afc5d8d5623a7d` on GitHub Actions with Python 3.12.14 and PostgreSQL 16. The official Upstox protobuf import succeeded. The non-integration suite reported **235 passed, 4 deselected, 1 warning in 1.64s**. The integration suite reported **4 passed, 235 deselected, 1 warning in 0.92s**. No provider credentials were used.

## Android evidence

Run `33614791892` completed the Android `assembleDebug` job successfully using the CI-installed pinned Gradle 8.10.2. The separate Android workflow run `33614791848` for the same position-state documentation commit also completed its debug build successfully.

## Current verification

The latest implementation/status commit on `main` is `45b0000f10f5afee87157df370afc5d8d5623a7d`; its dedicated CI run `33614791892` is fully green. The subsequent documentation-only commits updating this log and project status are not treated as implementation-test evidence until their own CI runs complete.

## Historical failed verification

The initial position-refresh contract verification run `33614542133` failed with fixture incompatibilities after the intentional safety hardening. The failure was investigated and corrected; it is retained here as evidence of genuine test-driven verification rather than hidden.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated. Durable idempotency has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Position state is refreshed before controlled-live submission and mismatches fail closed. Recovery-provider failures remain fail-closed and credential-free.
