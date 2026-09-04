# AI Trading Platform — Project Status

Last updated: 2026-09-04

## Current branch

`main` only.

## Current stage

**Stage 10 — Autonomous Trading Foundation**

## Verification update

- Upstox sandbox place/cancel smoke execution is operator-confirmed runtime evidence; repository secrets are not inspectable through the connected GitHub integration.
- Main CI run `33866098324` completed successfully for database migration `015_broker_accounts.sql`: PostgreSQL migrations, backend non-integration/integration tests, and Android `assembleDebug` passed. fileciteturn695file0L2-L10
- Broker-account metadata is user-owned and exposed only through authenticated API boundaries. Raw broker tokens are not stored or returned.
- Authenticated broker-account API regression coverage and the fail-closed credential-provider regression test are implemented; fresh CI verification for those commits is pending.
- The internal broker-account factory resolves an opaque credential reference through `CredentialProvider` and constructs Upstox/Dhan adapters with all broker mutation gates disabled. It cannot enable live trading from account metadata.
- The account repository retains the opaque credential reference only for this internal resolution boundary; the authenticated API response continues to expose only `has_credential_ref`.
- A fail-closed external credential-provider boundary is implemented; no broker token is resolved until a deployment supplies a real secret-management implementation.
- Authenticated read-only broker state now flows through the factory boundary; the state endpoint exposes account, positions and orders only and performs no broker mutation.
- Blank or whitespace-only credential references are rejected before secret resolution.
- Live trading remains explicitly gated and is not production verified.

## Verified implementation state

- Deterministic strategy/backtest/replay foundations are integrated; AI remains advisory and cannot authorize execution.
- Options analytics and provider-neutral option-chain contracts are implemented. Live provider runtime remains unverified.
- Paper trading has deterministic order/fill/position/P&L/risk/kill-switch behavior, durable persistence, restart hydration, and replay-to-paper execution.
- Provider-neutral broker contracts, authentication boundaries, reconciliation, idempotency, Upstox/Dhan adapters, instrument resolution/catalogues, and secret-safe session handling are implemented.
- Controlled execution remains inert until authenticated startup and explicit activation; deterministic risk, durable idempotency, broker confirmation, post-fill synchronization, reconciliation, and emergency-stop controls remain fail-closed.
- Autonomous decision and controlled-execution bridge do not independently authorize live broker submission.
- User-owned broker-account metadata persistence and authenticated management API are implemented. Account operations are scoped by authenticated `user_id` at the repository query boundary.
- Broker-account API does not accept an access token field, never returns `credential_ref`, and newly created accounts remain disabled until explicitly enabled.
- External credential resolution is deliberately fail-closed through `CredentialProvider`; the default provider raises `CredentialUnavailable` rather than inventing or reading credentials.
- `BrokerAccountFactory` is an internal construction boundary: it requires a user-scoped enabled account, a credential reference, and successfully resolved credentials; LIVE accounts still receive `allow_live_orders=False`.

## Stage status

### Stage 8 — Brokers

- [x] Provider-neutral broker/auth/reconciliation contracts, idempotency, durable PostgreSQL idempotency, ambiguous-submission protection, Upstox/Dhan adapters, mutation gating, instrument resolution/catalogues, secret-safe sessions
- [x] Explicit Upstox sandbox mode and operator-confirmed place/cancel smoke execution
- [x] Dhan sandbox isolation, authentication transport, cancellation hardening, missing-status fail-closed behavior and regression tests
- [x] User-owned broker-account metadata migration and authenticated account-management boundary
- [x] Fail-closed external credential-provider abstraction
- [x] Internal credential-resolution/broker-construction boundary with regression tests
- [x] Authenticated read-only broker state API wired through the credential/factory boundary
- [ ] CI verification of broker-account repository/API, credential boundary, factory, and broker-state commits
- [ ] Production-grade external secret-management implementation
- [ ] Dhan sandbox external runtime verification
- [ ] Production/live broker runtime verification

### Stage 9 — Controlled Live Trading

- [x] Explicit activation boundary, deterministic risk gate, position consistency check, broker order-id confirmation, kill switch, fail-closed startup/shutdown, durable emergency stop, audit, recovery/reconciliation and durable idempotency
- [x] CI verification of controlled execution safety mechanisms
- [ ] Production broker runtime verification
- [ ] Real live activation

### Stage 10 — Autonomous Trading

- [x] Deterministic autonomous decision pipeline and broker-neutral intent handoff
- [x] Autonomous-to-controlled bridge with portfolio-risk and execution-risk gates
- [x] Emergency controls and durable idempotency regression coverage
- [ ] Production validation

## Latest CI evidence

- `33866098324` completed successfully on 2026-09-04 for commit `d82cc64350796a66237cd5aa641cbedc18327dca`. Both backend-tests and android-build completed successfully; backend applied migrations and ran both pytest suites, while Android completed `assembleDebug`. fileciteturn695file0L2-L10
- Commits after `33866098324` add broker-account API regressions, credential-boundary coverage, broker factory, and broker-state API tests; they require fresh full CI verification before being marked CI-verified.

## Safety status

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** User-owned broker metadata is not itself broker authorization. No stored account is connected to live mutation through this API. Missing credentials fail closed, the default credential provider cannot resolve secrets, and broker-state endpoints are read-only. The broker factory explicitly constructs mutation-disabled adapters. Production broker runtime verification and real live activation have not been performed.

## Remaining blockers / unverified items

1. Fresh CI verification of the broker-account API, credential boundary, factory, and broker-state API commits is pending.
2. A production-grade secret-management implementation is required before user-owned accounts can resolve broker credentials.
3. Dhan sandbox external runtime verification remains blocked by the previously observed upstream HTTP 403 until valid sandbox credentials/access are available and the workflow is rerun.
4. Stage 5 external AI-provider runtime verification remains unverified.
5. Stage 6 live option-chain provider runtime verification remains unverified.
6. Production broker runtime and live activation remain explicitly gated.
