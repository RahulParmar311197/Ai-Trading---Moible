# AI Trading Platform — Project Status

Last updated: 2026-09-03

## Current branch

`main` only.

## Current stage

**Stage 10 — Autonomous Trading Foundation**

## Verified implementation state

- Deterministic strategy/backtest/replay foundations are integrated; AI remains advisory and cannot authorize execution.
- Options analytics and provider-neutral option-chain contracts are implemented. A fail-closed DhanHQ v2 option-chain adapter is wired behind explicit runtime configuration and requires authoritative Dhan catalogue metadata for execution fields; live provider runtime remains unverified.
- Paper trading has deterministic order/fill/position/P&L/risk/kill-switch behavior, durable persistence, restart hydration, and replay-to-paper execution.
- Provider-neutral broker contracts, authentication boundaries, reconciliation, idempotency, Upstox/Dhan adapters, instrument resolution/catalogue ingestion, and secret-safe session handling are implemented.
- Upstox and Dhan live mutation remains disabled by default.
- Upstox has an explicit sandbox mode with a separate `allow_sandbox_orders` gate. Sandbox permission cannot enable live orders.
- `ControlledBrokerExecution` is inert until authenticated startup and exact explicit activation. The kill switch defaults active, deterministic risk approval is mandatory before mutation, broker order-id confirmation is required, audit events are emitted, and shutdown/recovery fail closed.
- Controlled live construction requires an explicitly supplied idempotency store; there is no silent process-local fallback.
- Ambiguous broker submission exceptions preserve the idempotency reservation and force fail-closed reconciliation before reuse.
- Durable PostgreSQL idempotency uses atomic reservation and transactional result persistence; concurrent callers cannot both claim a new client-order key.
- Recovery refreshes broker positions/orders, reconciles requested IDs, and rejects unexpected live broker orders outside the explicit expected local order set. It never auto-activates trading.
- Before every controlled live submission, the execution boundary refreshes broker positions and requires the submitted `RiskSnapshot.position_quantity` to match the current broker position for the order symbol.
- Risk/session state is durable and explicitly session-bound; no local wall-clock trading-day boundary is invented.
- Partial/filled confirmations require explicit post-fill broker-state synchronization. Synchronization failure stops the lifecycle and keeps the kill switch active.
- The application runtime composes durable PostgreSQL audit, idempotency, risk-state, session-baseline, and emergency-control stores. Runtime construction remains inert and never activates trading.
- Provider-neutral AI HTTP compatibility and Android advisory AI integration are verified; AI cannot authorize execution.
- A deterministic portfolio risk monitor now provides gross/net exposure, per-position notional, P&L, and pairwise correlation checks without any broker mutation or execution authorization.
- A durable emergency execution stop now defaults active, persists its state in PostgreSQL, fails closed on persistence/read failure, and is checked at startup, activation, and submission boundaries. Clearing it is explicit and does not auto-activate trading.
- The emergency-control implementation was merged to `main` as squash commit `956c91590f6ae4c5c5a1a1bf2df16771b4059805` after CI and Android CI passed for the exact PR head.

## Stage status

### Stage 1 — Market Data

- [x] Canonical contracts, provider-neutral interfaces, Upstox boundaries, normalization/quality validation, aggregation, Redis live-state boundaries, PostgreSQL persistence, REST/WebSocket APIs, safe degraded startup, historical CI verification
- [x] Official Gradle wrapper artifact generated, checksum verified, committed to `main`, and consumed by the Android build workflow

### Stage 2 — SMC/ICT

- [x] Swing structure, BOS/MSS/CHOCH, liquidity pools/sweeps, FVG, displacement/order-block candidates, premium/discount, session levels, deterministic orchestration/tests
- [x] Fresh full product-flow verification covering backtest and replay-to-paper continuity; CI backend and Android builds passed

### Stage 3 — Replay

- [x] Deterministic replay clock/controls, speeds, event ordering, look-ahead-safe history, SMC replay, reusable strategy evaluation, replay-to-paper

### Stage 4 — Backtesting

- [x] Event-driven loop, strategy protocol, deterministic fills, fees/slippage, positions, P&L metrics, ledger/order events, risk sizing, OOS split, persisted reports/API, strategy DSL adapter, deterministic risk gate

### Stage 5 — AI

- [x] Strategy DSL, SMC context adapter, structured contracts, output safety gate, market-context builder, safe AI-to-DSL boundary, provider-neutral service, analyze/strategy/explain APIs
- [x] Provider compatibility contract tests for generic/OpenAI-style responses and failure sanitization
- [x] Android advisory AI integration and CI build verification
- [ ] Real external AI-provider runtime verification

### Stage 6 — Options

- [x] Contracts, quotes/OI/volume/IV fields, lot sizes, Black-Scholes Greeks, liquidity/spread validation, delta strike selection, multi-leg payoff/risk metrics, strategy selection, analytics API, provider-neutral chain interface
- [x] Fail-closed DhanHQ v2 option-chain adapter with authoritative catalogue metadata resolution and documented 3-second unique-request cooldown
- [x] Dhan adapter deterministic MockTransport tests covering mapping, missing metadata, and cooldown behavior
- [x] Dhan option-chain runtime configuration boundary using explicit credentials, segment, and deployment-supplied authoritative catalogue CSV
- [ ] Live option-chain provider runtime integration
- [ ] Fresh runtime verification of latest options changes

### Stage 7 — Paper Trading

- [x] Paper broker, market/limit lifecycle, long/short positions, P&L, fees/slippage, duplicate protection, notional/position limits, kill switch/loss halt, paper API, durable persistence, partial fills, restart hydration, risk-gate enforcement, replay-to-paper, CI verification

### Stage 8 — Brokers

- [x] Provider-neutral broker/auth/reconciliation contracts, idempotency, durable PostgreSQL idempotency, ambiguous-submission protection, Upstox/Dhan adapters, mutation gating, instrument resolution/catalogues, secret-safe sessions, token exchange/renewal boundaries, CI verification
- [x] Explicit Upstox sandbox adapter mode and opt-in place/cancel smoke-test path
- [ ] Live broker runtime verification
- [ ] Upstox sandbox smoke execution with a real sandbox token

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
- [x] CI verification of risk-session baseline and persisted-session risk snapshot implementation
- [x] Fail-closed post-fill synchronization boundary for partial/filled confirmations
- [x] Concrete provider-neutral post-fill synchronizer requiring broker refresh, persisted session baseline, and explicit risk-state sink
- [x] Explicit application session-identity integration
- [x] Application/runtime composition with concrete durable PostgreSQL risk-state sink
- [x] Durable emergency execution stop and fail-closed persistence/read behavior
- [x] CI verification of emergency-control implementation and Android build
- [x] Local full backend pytest verification: 279 passed, 1 skipped
- [x] Local PostgreSQL integration verification: 5 passed, 1 skipped
- [x] Local FastAPI runtime smoke verification: `/health` 200/ok and `/ready` 200/degraded with execution/market-data intentionally unconfigured
- [ ] Production broker runtime verification
- [ ] Real live activation

### Stage 10 — Autonomous Trading

- [ ] Autonomous decision pipeline
- [x] Portfolio-level risk/correlation exposure/position monitoring implemented and unit-tested; merge/CI verification of the corresponding portfolio-risk change still needs confirmation on `main`
- [x] Emergency controls implemented and CI verified; runtime/production verification remains outstanding
- [ ] Production validation

## Latest CI evidence

- PR #13 emergency-control head `0055fa50d2f65ca9901d64d2b35967ebbf8476b3`: CI run `33737569540` and Android CI run `33737569541` both completed successfully before squash merge to `956c91590f6ae4c5c5a1a1bf2df16771b4059805`.
- Run `33734700589` for Dhan option-chain runtime wiring head `ff023700c2b9d2e26c4fff612d2ad42964eb8025`: backend-tests and Android `assembleDebug` completed successfully.
- PR #8 was merged as squash commit `13d3802fa621bd59ad33fbf8d3bef1f79b4c2e8c` after both CI workflows completed successfully.
- Run `33734236062` for the full-flow verification head `ccc278f42428d08e52383ea747a0a7d9b2885d78`: backend and companion Android CI passed; PR #7 was merged as squash commit `957e310d25a6d0ca95f634f491a5044f3303f49c`.

## Runtime verification

The Codespaces environment was previously rebuilt successfully with self-contained Docker client/Compose setup. PostgreSQL 16 and Redis 7 were started locally and health-checked. The local backend suite and PostgreSQL integration suite were executed successfully. FastAPI `/health` returned 200/ok and `/ready` returned 200/degraded because live market-data and controlled execution prerequisites were intentionally not configured.

The Dhan option-chain adapter, emergency-control runtime, and production broker integrations have CI-level or code-level verification only unless explicitly stated above. No live Dhan credential, real option-chain request, production broker runtime, or real live activation has been performed.

## Safety status

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** Controlled execution requires authenticated startup plus exact explicit activation; broker position state is refreshed before submission and must agree with the supplied risk snapshot; partial/filled confirmations require explicit post-fill synchronization and failures stop the lifecycle with the kill switch active; recovery/startup keep the kill switch active; shutdown and ambiguous broker failures fail closed. The durable emergency stop defaults active and fails closed on persistence/read errors. Dhan/Upstox live mutation remains disabled by default. AI remains subordinate to deterministic validation, strategy, risk and execution controls. Production broker runtime verification and real live activation have not been performed.

## Remaining blockers / unverified items

1. Production broker runtime and real live activation are unverified. Upstox has a documented sandbox path, but the manual sandbox smoke workflow remains environment-dependent and requires an intentionally supplied sandbox token.
2. Stage 5 real external AI-provider runtime verification remains unverified; provider contract compatibility and Android integration are verified.
3. Stage 6 live option-chain provider runtime integration and fresh runtime verification remain unverified.
4. Stage 10 autonomous decision pipeline and production validation remain unverified and gated.
5. Portfolio-risk merge/CI state on `main` must be independently verified before treating that item as fully merged/CI-verified.
