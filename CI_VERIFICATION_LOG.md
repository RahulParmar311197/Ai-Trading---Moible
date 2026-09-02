# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33601890367` — commit `4bc648593e1fd26059507529bbf190e66e6cd4af`: backend job completed successfully with **208 non-integration tests passed** and **3 PostgreSQL integration tests passed**. The companion Android workflow run `33601890458` for the same commit completed `gradle assembleDebug` successfully. The CI workflow's Android job was still in progress when this entry was recorded; the separate Android workflow provides completed Android build evidence for the same commit.
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

Run `33601890367` completed dependency installation on Python 3.12.14, official Upstox protobuf verification, non-integration pytest, and integration pytest against a PostgreSQL 16 service successfully. The non-integration suite reported **208 passed, 3 deselected**; the integration suite reported **3 passed, 208 deselected**. The backend checked out commit `4bc648593e1fd26059507529bbf190e66e6cd4af`.

Run `33601730753` verified **204 non-integration tests passed** and **3 integration tests passed** for commit `1647774ef955ab7369b3c9932d20e608e6f9f4b6`. Earlier successful runs verify durable completion persistence, unexpected-live-order recovery, explicit idempotency-store enforcement, Dhan order semantics, and broker-session error sanitization.

## Android evidence

For commit `4bc648593e1fd26059507529bbf190e66e6cd4af`, Android workflow run `33601890458` completed `gradle assembleDebug` successfully. For commit `1647774ef955ab7369b3c9932d20e608e6f9f4b6`, run `33601730753` also completed its Android `gradle assembleDebug` successfully. The CI workflow's Android job for run `33601890367` remained in progress at the time of this update, so it is not represented as a fully completed two-job CI run.

## Current verification

The latest implementation commit on `main` is `4bc648593e1fd26059507529bbf190e66e6cd4af`. Backend CI and the separate Android workflow both pass for that commit. No claim is made that the still-running Android job in CI run `33601890367` has completed.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated. Recovery-provider failures now have regression coverage proving fail-closed state and sanitized audit reasons without requiring live credentials.
