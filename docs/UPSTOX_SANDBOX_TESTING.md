# Upstox Sandbox Testing

The repository now has an explicit Upstox sandbox mode for broker order testing.

## Upstream sandbox contract

Upstox documents its sandbox as an environment for end-to-end integration testing before connecting to the live market. Sandbox access tokens are separate from live access and cannot be used for live transactions. The currently documented sandbox-enabled APIs include Place Order, Place Order V3, Place Multi Order, Modify Order, Modify Order V3, Cancel Order, and Cancel Order V3.

The repository therefore treats sandbox order mutation as a separate capability from live order mutation:

- `sandbox=True` selects `https://sandbox.upstox.com/v2`.
- `allow_sandbox_orders=True` is required before sandbox order mutation is allowed.
- `allow_live_orders=True` does not enable sandbox mutation.
- Sandbox mode never enables live order submission.
- Live order submission remains separately disabled by default.

## Automated smoke test

`backend/tests/test_upstox_sandbox.py` contains an integration test that places one small LIMIT order with a unique client tag and then cancels the returned sandbox order. It is skipped when `UPSTOX_SANDBOX_ACCESS_TOKEN` is absent, so normal CI never fabricates a sandbox credential or makes an external order request.

The manual GitHub Actions workflow `.github/workflows/upstox-sandbox.yml` runs this smoke test only through `workflow_dispatch` and reads the token from the repository Actions secret `UPSTOX_SANDBOX_ACCESS_TOKEN`.

No sandbox or live credential is stored in the repository.

## Important verification boundary

The sandbox documentation currently lists order mutation APIs as sandbox-enabled. It does not establish that every account, portfolio, position, or recovery endpoint used by the controlled-live composition is sandbox-enabled. Consequently, a successful sandbox place/cancel smoke test must not be interpreted as verification of the complete Stage 9 controlled-live recovery, position-refresh, risk-state synchronization, or live activation path.

Those broader Stage 9 requirements remain gated until the repository has authoritative trading-session identity and durable live-state ownership, as already recorded in `docs/CONTROLLED_LIVE_COMPOSITION.md`.
