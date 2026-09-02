# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33611174894` — commit `b3d90cec9a460a31ba6e055c909be559720e7b0b`: backend completed successfully with **211 non-integration tests passed** and **4 PostgreSQL integration tests passed**. The Android job was still running when this entry was prepared; it is not claimed as complete until the job finishes.
- `33602457519` — commit `1ef8f592fab8ea58dcc151d85d1f814aebe03541`: backend completed successfully with **211 non-integration tests passed** and **3 PostgreSQL integration tests passed**; Android completed `gradle assembleDebug` successfully. This verifies terminal broker idempotency reservation clearing after reconciled `REJECTED`/`CANCELLED` states.
- `33602366045` — commit `14763dcf40657483a622708d244bec7f3c8f9f71`: Android debug build completed successfully. Backend integration coverage for durable pending reservations was verified in the companion CI run for the commit.
- `33601890367` — commit `4bc648593e1fd26059507529bbf190e66e6cd4af`: backend job completed successfully with **208 non-integration tests passed** and **3 PostgreSQL integration tests passed**. The companion Android workflow run `33601890458` for the same commit completed `gradle assembleDebug` successfully.
- `33601730753` — commit `1647774ef955ab7369b3c9932d20e608e6f9f4b6`: backend completed successfully with **204 non-integration tests passed** and **3 PostgreSQL integration tests passed**; Android `gradle assembleDebug` completed successfully. This verifies fail-closed broker submission failure handling and its regression test.
- `33601518005` — commit `a18d1daf06984cdb596906e86b35dc07fca6929e`: backend and Android jobs both completed successfully. This verifies the explicit idempotency-store requirement.
- `33600603414` — commit `753a823d3e3200213d460c0e6f97c497860d8e40`: Android debug build completed successfully.
- `33600557479` — commit `533f537a15489ec12d4bf1eb6611684845d874c0`: backend and Android debug build both completed successfully. Backend verified Dhan submission-status semantics and regression coverage.
- `33600307751` — commit `4ec1cd983375f2cba91cf34a72514f37dcc78f05`: backend tests and Android debug build both completed successfully. Backend completed dependency installation, official Upstox protobuf verification, **193 non-integration tests**, and **3 PostgreSQL integration tests**; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies broker-session error sanitization and the accumulated controlled-live safety suite.
- `33599917698` — commit `ce63a7a2eed00f171d1800fb2fab318ebc392a27`: backend tests and Android debug build both completed successfully. Backend completed dependency installation, official Upstox protobuf verification, 192 non-integration tests, and 3 PostgreSQL integration tests; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies durable idempotency completion persistence and its reservation-guard regression coverage.
- `33599202340` — commit `8b241e958ddc98a821c80e82f34b2e4f281eb286`: backend tests and Android debug build both completed successfully. Backend recorded 192 non-integration tests passed and 3 PostgreSQL integration tests passed; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies the unexpected broker live-order recovery hardening and regression coverage.
- `33598262758` — commit `82a01ee059ad765bafdd7a454eea0a3229b42e3e`: backend tests and Android debug build both completed successfully. Backend recorded 190 non-integration tests passed and 3 PostgreSQL integration tests passed; Android completed `gradle assembleDebug`.
- `33597951805` — commit `1c906d6a40a2519b423cbd44a8bb73634bba7f2f`: backend tests and Android debug build both completed successfully.

## Backend evidence

Run `33611174894` completed dependency installation on Python 3.12.14, official Upstox protobuf verification, non-integration pytest, and integration pytest against a PostgreSQL 16 service successfully. The non-integration suite reported **211 passed, 4 deselected**; the integration suite reported **4 passed, 211 deselected**. The new fourth integration test verifies that concurrent durable reservations yield exactly one successful reservation and one pending result.

Run `33602457519` completed successfully for commit `1ef8f592fab8ea58dcc151d85d1f814aebe03541`, with **211 non-integration tests passed** and **3 integration tests passed**.

## Android evidence

For commit `1ef8f592fab8ea58dcc151d85d1f814aebe03541`, run `33602457519` completed `gradle assembleDebug` successfully using Gradle 8.10.2 installed by CI. For commit `b3d90cec9a460a31ba6e055c909be559720e7b0b`, run `33611174841` is the separate Android workflow and was still in progress at the time of this update; no completed Android result is claimed for that commit yet.

## Current verification

The latest implementation commit on `main` is `b3d90cec9a460a31ba6e055c909be559720e7b0b`. Backend CI is **verified passing** with 211 non-integration and 4 integration tests. The companion Android build for the same commit remains **in progress** at the time of this entry, so the commit is not yet recorded as a fully green two-job CI run.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated. Durable idempotency now has CI coverage for restart persistence, unresolved pending reservations, terminal reconciliation clearing, and concurrent reservation exclusivity. Recovery-provider failures remain fail-closed and credential-free.
