# CI Verification Log

Last updated: 2026-09-02

## Verified passing runs

- `33597117321` — commit `a460713aa17c5e721a278b472bd16ac5c7da466f`: backend tests and Android debug build both completed successfully.
- `33597128224` — commit `b354ebc4ad538d3a98817c72f4496b08c06cb8a8`: backend tests and Android debug build both completed successfully.
- `33597128231` — commit `b354ebc4ad538d3a98817c72f4496b08c06cb8a8`: Android debug build completed successfully.
- `33597156260` — commit `85d98926787334ad77319598f3abd9c8c2a359e6`: backend tests and Android debug build both completed successfully.
- `33597156289` — commit `85d98926787334ad77319598f3abd9c8c2a359e6`: Android debug build completed successfully.

## Backend evidence

For runs `33597117321`, `33597128224`, and `33597156260`, the backend job completed all configured steps successfully, including dependency installation, official Upstox protobuf verification, non-integration pytest, and integration pytest against PostgreSQL.

## Android evidence

The verified Android jobs completed `gradle assembleDebug` successfully using the repository's pinned Gradle 8.10.2 CI setup.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. These are GitHub Actions results only; no local test execution is claimed.

## Safety

CI success does not authorize live or autonomous trading. Production broker runtime verification, real live activation, and Stage 10 autonomous prerequisites remain gated.
