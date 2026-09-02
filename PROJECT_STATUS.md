# AI Trading Platform — Project Status

Last updated: 2026-09-02

## Current branch

`main` only.

## Current stage

**Stage 9 — Controlled Live Trading Foundation**

## Verified implementation state

- Deterministic strategy/backtest/replay foundations are integrated; AI remains advisory and cannot authorize execution.
- Options analytics and provider-neutral option-chain contracts are implemented; live option-chain integration remains unverified.
- Paper trading has deterministic order/fill/position/P&L/risk/kill-switch behavior, durable persistence, restart hydration, and replay-to-paper execution.
- Provider-neutral broker contracts, authentication boundaries, reconciliation, idempotency, Upstox/Dhan adapters, instrument resolution/catalogue ingestion, and secret-safe session handling are implemented.
- Upstox and Dhan live mutation remains disabled by default.
- `ControlledBrokerExecution` is inert until authenticated startup and exact explicit activation. The kill switch defaults active, deterministic risk approval is mandatory before mutation, broker order-id confirmation is required, audit events are emitted, and shutdown/recovery fail closed.
- Controlled live construction requires an explicitly supplied idempotency store; there is no silent process-local fallback.
- Ambiguous broker submission exceptions preserve the idempotency reservation and force fail-closed reconciliation before reuse.
- Durable PostgreSQL idempotency uses an atomic `INSERT ... ON CONFLICT DO NOTHING RETURNING` reservation and a transactional returning executor, so concurrent callers cannot both claim a new client-order key.
- Durable idempotency completion persists and verifies broker results; terminal reconciled `REJECTED`/`CANCELLED` reservations are explicitly cleared, while live/pending states remain reserved.
- Recovery refreshes broker positions/orders, reconciles requested IDs, and rejects unexpected live broker orders outside the explicit expected local order set. It never auto-activates trading.
- Before every controlled live submission, the execution boundary refreshes broker positions and requires the submitted `RiskSnapshot.position_quantity` to match the current broker position for the order symbol. Refresh failures, malformed position responses, or mismatches fail closed before broker mutation.
- `RiskSnapshot` rejects non-finite balance/P&L and invalid position quantities at construction time, keeping malformed risk state fail-closed before evaluation.
- `BrokerStateSynchronizer` provides a broker-refresh primitive that aggregates provider position P&L and requires an explicit daily realized-P&L baseline when deriving the next risk snapshot; no lifetime broker P&L is silently treated as today's P&L.
- `PostgresRiskSessionBaselineStore` provides durable, idempotent persistence for an explicitly supplied risk-session baseline. Conflicting reinitialization is rejected and missing sessions fail closed; the store intentionally does not invent market/trading-day boundaries.
- `risk_snapshot_from_persisted_session` binds fresh broker state to the persisted baseline for an explicitly supplied session ID, so callers cannot silently substitute a wall-clock baseline or broker lifetime P&L.
- Partial/fill confirmations now require an explicit post-fill state-synchronization callback. Missing or failed synchronization forces the controlled executor into a stopped/kill-switch state and emits an audit event; successful synchronization is audited before the lifecycle remains active. This callback does not attempt to undo a broker fill.

## Stage status

### Stage 1 — Market Data

- [x] Canonical contracts, provider-neutral interfaces, Upstox boundaries, normalization/quality validation, aggregation, Redis live-state boundaries, PostgreSQL persistence, REST/WebSocket APIs, safe degraded startup, historical CI verification
- [ ] Final verification including the official Gradle wrapper artifact requirement

### Stage 2 — SMC/ICT

- [x] Swing structure, BOS/MSS/CHOCH, liquidity pools/sweeps, FVG, displacement/order-block candidates, premium/discount, session levels, deterministic orchestration/tests
- [ ] Fresh full product-flow verification

### Stage 3 — Replay

- [x] Deterministic replay clock/controls, speeds, event ordering, look-ahead-safe history, SMC replay, reusable strategy evaluation, replay-to-paper

### Stage 4 — Backtesting

- [x] Event-driven loop, strategy protocol, deterministic fills, fees/slippage, positions, P&L metrics, ledger/order events, risk sizing, OOS split, persisted reports/API, strategy DSL adapter, deterministic risk gate

### Stage 5 — AI

- [x] Strategy DSL, SMC context adapter, structured contracts, output safety gate, market-context builder, safe AI-to-DSL boundary, provider-neutral service, analyze/strategy/explain APIs
- [ ] Real external-provider compatibility verification
- [ ] Android AI integration

### Stage 6 — Options

- [x] Contracts, quotes/OI/volume/IV fields, lot sizes, Black-Scholes Greeks, liquidity/spread validation, delta strike selection, multi-leg payoff/risk metrics, strategy selection, analytics API, provider-neutral chain interface
- [ ] Live option-chain provider integration
- [ ] Fresh runtime verification of latest options changes

### Stage 7 — Paper Trading

- [x] Paper broker, market/limit lifecycle, long/short positions, P&L, fees/slippage, duplicate protection, notional/position limits, kill switch/loss halt, paper API, durable persistence, partial fills, restart hydration, risk-gate enforcement, replay-to-paper, CI verification

### Stage 8 — Brokers

- [x] Provider-neutral broker/auth/reconciliation contracts, idempotency, durable PostgreSQL idempotency, ambiguous-submission protection, Upstox/Dhan adapters, mutation gating, instrument resolution/catalogues, secret-safe sessions, token exchange/renewal boundaries, CI verification
- [ ] Live broker runtime verification

### Stage 9 — Controlled Live Trading

- [x] Explicit activation boundary
- [x] Deterministic risk gate and position limits before broker mutation
- [x] Fresh broker position refresh and snapshot consistency check before broker mutation
- [x] Broker order-id confirmation
- [x] Kill switch and fail-closed startup/shutdown
- [x] Audit-event boundary and durable audit repository
- [x] Recovery/reconciliation boundary
- [x] Unexpected-live-order recovery rejection
- [x] Durable idempotency persistence across restart
- [x] Ambiguous broker submission fail-closed behavior
- [x] Explicit idempotency-store requirement
- [x] Atomic durable reservation and concurrency regression coverage
- [x] Terminal `REJECTED`/`CANCELLED` reservation clearing after reconciliation
- [x] Regression test for stale/mismatched position snapshot
- [x] Broker-state synchronization primitive with explicit daily-P&L baseline
- [x] Fail-closed validation for non-finite risk snapshot inputs
- [x] Durable risk-session baseline persistence primitive with conflict/missing-session safeguards
- [x] Persisted-session risk snapshot binding
- [x] CI verification of the risk-session baseline and persisted-session risk snapshot implementation
- [x] Fail-closed post-fill synchronization boundary for partial/filled confirmations
- [ ] Authoritative trading-session boundary/lifecycle integration
- [ ] Concrete post-fill broker-state propagation using the synchronizer, persisted session baseline, and durable live-state sink
- [ ] Production broker runtime verification
- [ ] Real live activation

### Stage 10 — Autonomous Trading

- [ ] Autonomous decision pipeline
- [ ] Portfolio-level risk/correlation exposure/position monitoring
- [ ] Emergency controls
- [ ] Production validation

## Latest CI evidence

- Run `33619555439` for implementation commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`: backend and Android jobs both completed successfully. Backend recorded **252 non-integration tests passed, 5 deselected, 1 warning** and **5 PostgreSQL integration tests passed, 252 deselected, 1 warning**. Android `assembleDebug` completed successfully with the pinned Gradle 8.10.2 workflow setup.
- Run `33619555530` is the Android-only workflow for commit `9b8611102a49b7f580e5111ae0ba1a29219e84e6`; `assembleDebug` completed successfully.
- Run `33619172631` for commit `021b82532e3e6efa276268425af7080f94f9bb2a`: backend completed successfully with **249 non-integration tests passed, 5 deselected, 1 warning** and **5 PostgreSQL integration tests passed, 249 deselected, 1 warning**.
- Run `33618698177` for commit `ef60eb80518ec8b858fa1b94a756930458bd8043`: backend and Android jobs both completed successfully; backend recorded **247 non-integration passed** and **4 PostgreSQL integration tests passed**.
- Run `33617134105` for commit `919253298d47ff2708bfb0c540292bff7c80c0cb`: **242 non-integration passed, 4 deselected, 1 warning; 4 PostgreSQL integration tests passed, 242 deselected, 1 warning; Android `assembleDebug` passed**.
- Run `33617011571` for predecessor commit `c49a16791817542b5f2ea4c19e8090c558616b1a` remains a genuine failed verification and is retained in the CI log.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. No local test execution is claimed; GitHub Actions is the available runtime verification path.

## Safety status

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** Controlled execution requires successful authenticated startup plus exact explicit activation; broker position state is refreshed before every submission and must agree with the supplied risk snapshot; partial/filled confirmations require explicit post-fill synchronization and failures stop the lifecycle with the kill switch active; recovery/startup keep the kill switch active; shutdown and ambiguous broker failures fail closed. Dhan/Upstox live mutation remains disabled by default. AI remains subordinate to deterministic validation, strategy, risk and execution controls. Production broker runtime verification and real live activation have not been performed.

## Remaining blockers / unverified items

1. Official Gradle wrapper artifact (`gradle-wrapper.jar`) is still absent; CI installs Gradle 8.10.2 directly, so final Stage 1 wrapper verification remains blocked.
2. The durable risk-session baseline primitive and persisted-session risk-snapshot binding are implemented and CI-verified, but the runtime architecture still lacks an authoritative upstream trading-session boundary/lifecycle. The application must supply the session identity rather than silently deriving a market day.
3. Post-fill synchronization is now an explicit fail-closed lifecycle boundary, but it is not yet wired to a concrete `BrokerStateSynchronizer`, persisted risk-session baseline, and durable live-state sink that can be verified end-to-end.
4. Production broker runtime and real live activation are unverified because no sandbox/test broker credentials are available through the connected tools.
5. Stage 5 external AI-provider compatibility and Android AI integration remain unverified.
6. Stage 6 live option-chain provider integration remains unverified.
7. Stage 2 fresh full product-flow verification remains unverified.
8. Stage 10 autonomous trading remains gated and must not be enabled without all blueprint prerequisites and evidence.
