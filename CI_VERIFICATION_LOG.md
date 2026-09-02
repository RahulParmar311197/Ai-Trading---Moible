# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33600307751` — commit `4ec1cd983375f2cba91cf34a72514f37dcc78f05`: backend tests and Android debug build both completed successfully. Backend completed dependency installation, official Upstox protobuf verification, **193 non-integration tests**, and **3 PostgreSQL integration tests**; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies broker-session error sanitization and the accumulated controlled-live safety suite.
- `33599917698` — commit `ce63a7a2eed00f171d1800fb2fab318ebc392a27`: backend tests and Android debug build both completed successfully. Backend completed dependency installation, official Upstox protobuf verification, 192 non-integration tests, and 3 PostgreSQL integration tests; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies durable idempotency completion persistence and its reservation-guard regression coverage.
- `33599202340` — commit `8b241e958ddc98a821c80e82f34b2e4f281eb286`: backend tests and Android debug build both completed successfully. Backend recorded 192 non-integration tests passed and 3 PostgreSQL integration tests passed; Android completed `gradle assembleDebug` using pinned Gradle 8.10.2. This run verifies the unexpected broker live-order recovery hardening and regression coverage.
- `33598262758` — commit `82a01ee059ad765bafdd7a454eea0a3229b42e3e`: backend tests and Android debug build both completed successfully. Backend recorded 190 non-integration tests passed and 3 PostgreSQL integration tests passed; Android completed `gradle assembleDebug`.
- `33597951805` — commit `1c906d6a40a2519b423cbd44a8bb73634bba7f2f`: backend tests and Android debug build both completed successfully.
- `33597117321` — commit `a460713aa17c5e721a278b472bd16ac5c7da466f`: backend tests and Android debug build both completed successfully.
- `33597128224` — commit `b354ebc4ad538d3a98817c72f4496b08c06cb8a8`: backend tests and Android debug build both completed successfully.
- `33597128231` — commit `b354ebc4ad538d3a98817c72f4496b08c06cb8a8`: Android debug build completed successfully.
- `33597156260` — commit `85d98926787334ad77319598f3abd9c8c2a359e6`: backend tests and Android debug build both completed successfully.
- `33597156289` — commit `85d98926787334ad77319598f3abd9c8c2a359e6`: Android debug build completed successfully.

## Backend evidence

Run `33600307751` completed dependency installation on Python 3.12.14, official Upstox protobuf verification, non-integration pytest, and integration pytest against a PostgreSQL 16 service successfully. The non-integration suite reported 193 passed and 3 deselected; the integration suite reported 3 passed and 193 deselected. The backend checked out commit `4ec1cd983375f2cba91cf34a72514f37dcc78f05`.

Run `33599917698` verified durable idempotency completion persistence. Run `33599202340` verified unexpected-live-order recovery hardening. Run `33598262758` verified the explicit controlled idempotency-store requirement. Run `33597951805` verified the durable broker-idempotency implementation and broker contract export fixes. The earlier failing run `33597725639` is intentionally not listed as passing evidence.

## Android evidence

The verified Android job for run `33600307751` completed `gradle assembleDebug` successfully using the repository's pinned Gradle 8.10.2 CI setup. The same Android verification was completed by runs `33599917698`, `33599202340`, and `33598262758` for preceding controlled-execution hardening commits.

## Current verification

Run `33600557479` (run number 338), for commit `533f537a15489ec12d4bf1eb6611684845d874c0`, is **in progress**. It contains the Dhan submission-status hardening and new regression tests. No passing claim is made for run 338 until both backend and Android jobs complete successfully.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated.
