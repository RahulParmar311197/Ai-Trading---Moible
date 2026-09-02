# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33598262758` — commit `82a01ee059ad765bafdd7a454eea0a3229b42e3e`: backend tests and Android debug build both completed successfully. Backend recorded 190 non-integration tests passed and 3 PostgreSQL integration tests passed; Android completed `gradle assembleDebug`.
- `33597951805` — commit `1c906d6a40a2519b423cbd44a8bb73634bba7f2f`: backend tests and Android debug build both completed successfully. Backend included non-integration pytest and PostgreSQL integration pytest; Android completed `gradle assembleDebug`.
- `33597117321` — commit `a460713aa17c5e721a278b472bd16ac5c7da466f`: backend tests and Android debug build both completed successfully.
- `33597128224` — commit `b354ebc4ad538d3a98817c72f4496b08c06cb8a8`: backend tests and Android debug build both completed successfully.
- `33597128231` — commit `b354ebc4ad538d3a98817c72f4496b08c06cb8a8`: Android debug build completed successfully.
- `33597156260` — commit `85d98926787334ad77319598f3abd9c8c2a359e6`: backend tests and Android debug build both completed successfully.
- `33597156289` — commit `85d98926787334ad77319598f3abd9c8c2a359e6`: Android debug build completed successfully.

## Backend evidence

Run `33598262758` completed dependency installation, official Upstox protobuf verification, non-integration pytest, and integration pytest against PostgreSQL successfully. The non-integration suite reported 190 passed and 3 deselected; the integration suite reported 3 passed and 190 deselected. This verifies the explicit controlled idempotency-store hardening together with the durable broker-idempotency implementation and broker contract fixes on commit `82a01ee059ad765bafdd7a454eea0a3229b42e3e`.

Run `33597951805` completed the durable broker-idempotency implementation and broker contract export fixes successfully. The earlier failing run `33597725639` is intentionally not listed as passing evidence.

For runs `33597117321`, `33597128224`, and `33597156260`, the backend job also completed all configured steps successfully, including dependency installation, official Upstox protobuf verification, non-integration pytest, and integration pytest against PostgreSQL.

## Android evidence

The verified Android jobs completed `gradle assembleDebug` successfully using the repository's pinned Gradle 8.10.2 CI setup. Run `33598262758` verified the current commit `82a01ee059ad765bafdd7a454eea0a3229b42e3e`.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated.
