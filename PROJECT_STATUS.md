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
- `ControlledBrokerExecution` is inert until authenticated startup and exact explicit activation. The kill switch defaults active, deterministic risk approval is mandatory before mutation, broker order-id confirmation is required, audit events are emitted, and shutdown/recovery fail closed. fileciteturn583file0L2-L2
- Controlled live construction requires an explicitly supplied idempotency store; there is no silent process-local fallback.
- Ambiguous broker submission exceptions preserve the idempotency reservation and force fail-closed reconciliation before reuse. fileciteturn588file0L2-L2
- Durable PostgreSQL idempotency uses an atomic `INSERT ... ON CONFLICT DO NOTHING RETURNING` reservation and a transactional returning executor, so concurrent callers cannot both claim a new client-order key. fileciteturn585file0L2-L2 fileciteturn586file0L2-L2
- Durable idempotency completion persists and verifies broker results; terminal reconciled `REJECTED`/`CANCELLED` reservations are explicitly cleared, while live/pending states remain reserved.
- Recovery refreshes broker positions/orders, reconciles requested IDs, and rejects unexpected live broker orders outside the explicit expected local order set. It never auto-activates trading.

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
- [x] CI verification of the above safety regressions
- [ ] Production broker runtime verification
- [ ] Real live activation

### Stage 10 — Autonomous Trading

- [ ] Autonomous decision pipeline
- [ ] Portfolio-level risk/correlation exposure/position monitoring
- [ ] Emergency controls
- [ ] Production validation

## Latest CI evidence

- Commit `1ef8f592fab8ea58dcc151d85d1f814aebe03541` / run `33602457519`: **211 non-integration passed, 3 integration passed; Android `assembleDebug` passed**.
- Commit `b3d90cec9a460a31ba6e055c909be559720e7b0b` / run `33611174894`: **211 non-integration passed, 4 integration passed**. The added fourth integration test verifies that concurrent durable reservation attempts produce exactly one reservation and one pending result.
- Separate Android workflow run `33611174841` for `b3d90cec9a460a31ba6e055c909be559720e7b0b` was still running when this status was updated; no completed Android result is claimed for that commit.
- Documentation commit `326e21774774a94ae81b87cbf8f317250fbbbcb7` triggered a new CI run; that run must be verified before this status can be considered fully current.

## Runtime limitation

No local/Codespace runtime is exposed through the connected tools. No local test execution is claimed; GitHub Actions is the available runtime verification path.

## Safety status

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** Controlled execution requires successful authenticated startup plus exact explicit activation; recovery/startup keep the kill switch active; shutdown and ambiguous broker failures fail closed. Dhan/Upstox live mutation remains disabled by default. AI remains subordinate to deterministic validation, strategy, risk and execution controls. Production broker runtime verification and real live activation have not been performed.

## Remaining blockers / unverified items

1. Official Gradle wrapper artifact (`gradle-wrapper.jar`) is still absent; CI installs Gradle 8.10.2 directly, so final Stage 1 wrapper verification remains blocked.
2. Production broker runtime and real live activation are unverified because no sandbox/test broker credentials are available through the connected tools.
3. Stage 5 external AI-provider compatibility and Android AI integration remain unverified.
4. Stage 6 live option-chain provider integration remains unverified.
5. Stage 2 fresh full product-flow verification remains unverified.
6. Stage 10 autonomous trading remains gated and must not be enabled without all blueprint prerequisites and evidence.
