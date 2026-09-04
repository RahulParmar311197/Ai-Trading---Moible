# AI Trading Platform — Project Status

Last updated: 2026-09-04

## Current branch

`main` only.

## Current stage

**Stage 10 — Autonomous Trading Foundation**

## Verification update

- Upstox sandbox workflow is on `main` and requires `UPSTOX_SANDBOX_ACCESS_TOKEN` from repository secrets.
- The sandbox workflow network preflight is diagnostic-only; the actual place/cancel integration test remains the authoritative sandbox execution check.
- A real sandbox place/cancel execution has not yet been successfully verified.
- Live trading remains explicitly gated and is not production verified.
- Dhan cancellation handling now requires an authoritative broker cancellation response and a subsequent authoritative order refresh confirming the requested broker order ID is `CANCELLED`; fabricated local cancellation state is no longer accepted.

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
- Durable PostgreSQL idempotency uses atomic reservation and atomic result persistence; concurrent callers cannot both claim a new client-order key, and terminal results cannot be overwritten by a conflicting result.
- Recovery refreshes broker positions/orders, reconciles requested IDs, and rejects unexpected live broker orders outside the explicit expected local order set. It never auto-activates trading.
- Recovery now carries an authoritative reconciled `BrokerOrder` and completes idempotency only for confirmed terminal `FILLED` results; unresolved NEW/OPEN/PARTIALLY_FILLED states remain pending, while REJECTED/CANCELLED remain explicitly clearable.
- Before every controlled live submission, the execution boundary refreshes broker positions and requires the submitted `RiskSnapshot.position_quantity` to match the current broker position for the order symbol.
- Risk/session state is durable and explicitly session-bound; no local wall-clock trading-day boundary is invented.
- Partial/filled confirmations require explicit post-fill broker-state synchronization. Synchronization failure stops the lifecycle and keeps the kill switch active.
- The application runtime composes durable PostgreSQL audit, idempotency, risk-state, session-baseline, and emergency-control stores. Runtime construction remains inert and never activates trading.
- Provider-neutral AI HTTP compatibility and Android advisory AI integration are verified; AI cannot authorize execution.
- A deterministic portfolio risk monitor provides gross/net exposure, per-position notional, P&L, and pairwise correlation checks without any broker mutation or execution authorization.
- A durable emergency execution stop defaults active, persists its state in PostgreSQL, fails closed on persistence/read failure, and is checked before broker authentication at startup, as well as at activation and submission boundaries. Clearing it is explicit and does not auto-activate trading.
- The autonomous decision pipeline, deterministic autonomous intent handoff, and autonomous-to-controlled execution bridge are merged to `main`; the bridge requires both portfolio-risk approval and execution-risk approval before delegation.
- Durable idempotency regression coverage is merged: unresolved reservations remain pending, completed results are replayed, conflicting reuse is rejected, and explicit reconciliation/clear permits reuse.
- Dhan cancellation is fail-closed: cancellation requires a matching broker order ID and `CANCELLED` response, followed by an authoritative `GET /orders/{order_id}` confirmation before returning the mapped order.

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
- [x] Dhan cancellation hardening with authoritative post-cancel order refresh and regression tests
- [ ] Live broker runtime verification
- [ ] Upstox sandbox smoke execution with a real sandbox token

### Stage 9 — Controlled Live Trading

- [x] Explicit activation boundary
- [x] Deterministic risk gate and position limits before broker mutation
- [x] Fresh broker position refresh and snapshot consistency check before broker mutation
- [x] Broker order-id confirmation
- [x] Kill switch and fail-closed startup/shutdown
- [x] Persisted emergency-stop state is authoritative before broker authentication at startup
- [x] Audit-event boundary and durable audit repository
- [x] Recovery/reconciliation boundary
- [x] Unexpected-live-order recovery rejection
- [x] Durable idempotency persistence across restart
- [x] Ambiguous broker submission fail-closed behavior
- [x] Explicit idempotency-store requirement
- [x] Atomic durable reservation and concurrency regression coverage
- [x] Atomic durable terminal-result completion and no-overwrite protection
- [x] Terminal `REJECTED`/`CANCELLED` reservation clearing after reconciliation
- [x] Durable idempotency unresolved/completed/conflict/reuse regression coverage
- [x] Recovered terminal `FILLED` result completes idempotency and replays without broker resubmission
- [x] Reconciliation rejects inconsistent embedded broker-order identity/status
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
- [x] PR #22 backend CI and Android CI verified successfully after reconciliation regression fixes
- [x] PR #26 backend CI and Android CI verified successfully after atomic durable-completion regression fixes
- [x] PR #27 backend CI and Android CI verified successfully; persisted emergency stop is fail-closed before broker authentication
- [ ] Production broker runtime verification
- [ ] Real live activation

### Stage 10 — Autonomous Trading

- [x] Deterministic autonomous decision pipeline: candidate validation, authoritative state freshness, projected portfolio exposure/correlation checks, deterministic execution gate, broker-neutral `ExecutionIntent`, and no broker mutation/live activation path
- [x] Deterministic autonomous intent handoff into broker-neutral `BrokerOrder` materialization
- [x] Autonomous-to-controlled execution bridge with portfolio-risk and execution-risk gates before controlled delegation
- [x] Portfolio-level risk/correlation exposure/position monitoring implemented and unit-tested; merged to `main`
- [x] Emergency controls implemented and CI verified; runtime/production verification remains outstanding
- [x] Durable idempotency regression coverage merged and CI verified
- [ ] Production validation

## Latest CI evidence

- Main CI run `33852909204` (#651), head `17f84ebb7b5d214ad1181458f30d0915e63e52ac`, completed successfully on 2026-09-04. Backend tests passed including migrations, non-integration pytest, and integration pytest steps; Android `assembleDebug` passed.
- The Dhan cancellation hardening regression tests are included in CI run #651 and the backend job completed successfully.
- Earlier PR #27 head `74931b378227f3b709761f0918614adf0271f025`: Android CI run `33834375439` completed successfully; CI run `33834375456` completed successfully with backend-tests and Android build passing. PR merged to `main` as `89be79df6bb8f0d7d66fb602486aaa823b5ffccd`.
- PR #26 head `098814160c4fd6b18f948b4a84d93cf9783c885b`: CI run `33833371312` backend-tests and Android build both completed successfully; PR merged to `main` as `f2b51649954b3c95b5038fda48a70493dbaca42d`.
- PR #22 head `3b24a27848ee215f82bc2fabedb6baed92e5a3bb`: CI run `33746835072` backend-tests and Android build both completed successfully; PR merged to `main` as `62f66671c97dd9bec19a66617d0025222bae378b`.

## Runtime verification

The Codespaces environment was previously rebuilt successfully with self-contained Docker client/Compose setup. PostgreSQL 16 and Redis 7 were started locally and health-checked. The local backend suite and PostgreSQL integration suite were executed successfully. FastAPI `/health` returned 200/ok and `/ready` returned 200/degraded because live market-data and controlled execution prerequisites were intentionally not configured.

The Dhan option-chain adapter, emergency-control runtime, autonomous decision pipeline, Dhan broker runtime, Upstox broker runtime, and production broker integrations have CI-level or code-level verification only unless explicitly stated above. No live Dhan credential, real option-chain request, production broker runtime, or real live activation has been performed.

## Safety status

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** Controlled execution requires authenticated startup plus exact explicit activation; persisted emergency-stop state is checked before broker authentication at startup and must be clear before activation/submission; broker position state is refreshed before submission and must agree with the supplied risk snapshot; partial/filled confirmations require explicit post-fill synchronization and failures stop the lifecycle with the kill switch active; recovery/startup keep the kill switch active; shutdown and ambiguous broker failures fail closed. The durable emergency stop defaults active and fails closed on persistence/read errors. Dhan/Upstox live mutation remains disabled by default. AI remains subordinate to deterministic validation, strategy, risk and execution controls. The autonomous decision pipeline and bridge do not authorize broker submission without the controlled execution boundary. Production broker runtime verification and real live activation have not been performed.

## Remaining blockers / unverified items

1. Production broker runtime and real live activation are unverified. Upstox sandbox has a dedicated workflow and repository-secret path, but a real place/cancel smoke execution has not yet been successfully verified.
2. Stage 5 real external AI-provider runtime verification remains unverified; provider contract compatibility and Android integration are verified.
3. Stage 6 live option-chain provider runtime integration and fresh runtime verification remain unverified.
4. Stage 10 production validation remains unverified and gated; autonomous decision evaluation and controlled bridging are implemented and CI verified but are not an authorization path for live orders.
5. Dhan broker runtime authentication and live/paper external runtime behavior remain unverified; cancellation logic is implementation/test/CI verified only.
