# AI Trading Platform — Project Status

Last updated: 2026-09-02

## Current branch

`main` only.

## Current stage

**Stage 9 — Controlled Live Trading Foundation**

## Latest implementation state

- Strategy DSL is integrated with deterministic backtesting and replay evaluation.
- Structured market context is built from visible candles plus deterministic SMC/ICT facts.
- AI has a provider-neutral HTTP/service boundary and `/api/v1/ai/analyze`, `/api/v1/ai/strategy`, `/api/v1/ai/explain-trade` endpoints. AI remains advisory and cannot authorize execution.
- Options have provider-neutral contracts, deterministic Black-Scholes Greeks, liquidity/spread filtering, deterministic delta-based strike selection, multi-leg expiry payoff, risk metrics, deterministic strategy selection, a provider-neutral option-chain boundary, and options analytics APIs.
- Paper trading has deterministic in-memory order/fill/position execution, configurable fees/slippage, limit-order behavior, duplicate-order protection, P&L accounting, configurable order-notional and position limits, a kill switch, and a paper-only API.
- Paper trading now has durable order/fill/position/audit persistence, deterministic partial-fill simulation, and restart hydration. Account balance, cumulative realized P&L, and halt state are persisted separately so restoration does not replay orders or contact live brokers.
- Replay-to-paper execution is implemented through a paper-only adapter. Replay-visible candles drive deterministic strategy evaluation; signals are translated into paper market orders, and optional stop/target brackets are evaluated on later replay candles. The adapter cannot route replay orders to live brokers.
- `DeterministicExecutionGate` is provider-neutral and performs pure pre-trade order-notional, position-quantity, daily-loss, halt, price and quantity checks. It never submits an order itself.
- The deterministic execution gate is an optional pre-trade gate on `PaperBroker.place_order`; rejected orders stop before paper persistence.
- Provider-specific authentication boundaries now cover Upstox authorization-code exchange and daily token-expiry calculation, plus Dhan consent generation, consent consumption, and supported token renewal. Credential values remain transport-only.
- Successful broker tokens can be converted directly into the existing secret-safe `StaticTokenBrokerSession` boundary without changing broker domain models.
- Stage 8 has provider-neutral account/order/position/broker protocols, non-secret authentication context, deterministic reconciliation, idempotency enforcement, Upstox/Dhan adapters, instrument resolution/catalogue ingestion, and mutation disabled by default.
- Added `ControlledBrokerExecution`: construction is inert, startup verifies the broker authentication boundary without enabling mutation, activation requires an exact explicit confirmation phrase, a kill switch defaults active, risk approval is mandatory before broker mutation, broker confirmation is required, idempotency wraps the mutation boundary, audit events are emitted through an optional sink, and shutdown fails closed.
- Controlled execution now has a provider-neutral durable audit repository/sink plus a dedicated PostgreSQL migration. Audit persistence stores only execution event type, client order id, reason, timestamp and a safe JSON payload; credential values are excluded.
- Controlled execution recovery now fails closed: recovery disables new entries, re-authenticates, refreshes positions/orders, reconciles requested client orders, and requires explicit reactivation after a healthy recovery. Reconciliation mismatch or unavailable recovery boundaries keep execution stopped.
- Broker idempotency now treats submission exceptions as potentially ambiguous: a failed provider call keeps the client-order key reserved and blocks both identical retries and conflicting reuse until the state is externally reconciled and explicitly cleared.
- Added a PostgreSQL-backed broker idempotency repository and migration so reserved client-order keys survive process restart; CI integration testing verifies a second repository instance can recover a completed result and still rejects conflicting reuse.
- Controlled live execution now requires an explicitly supplied idempotency store at construction, preventing a live executor from silently falling back to process-local idempotency state that disappears after restart. Test-only executors explicitly inject the in-memory store.
- Controlled execution remains an integration boundary only; no production/live activation has been enabled or configured.

## CI evidence

GitHub Actions run `33598262758` for commit `82a01ee059ad765bafdd7a454eea0a3229b42e3e` completed successfully. The backend job completed dependency installation, official Upstox protobuf verification, 190 non-integration tests, and 3 PostgreSQL integration tests. The Android job completed `gradle assembleDebug` using the pinned Gradle 8.10.2 CI setup.

The prior run `33598239655` exposed a test-fixture mismatch after the explicit idempotency-store requirement was introduced; the repository test helper was corrected before the successful `33598262758` verification. Do not count the failed run as verification evidence.

Earlier durable-idempotency verification was covered by successful GitHub Actions run `33597951805`. Earlier controlled-execution recovery/audit implementation was covered by successful GitHub Actions run `33595826727`. Earlier idempotency-safety commits were verified by successful runs `33597117321`, `33597128224`, `33597128231`, `33597156260`, and `33597156289`.

No local/Codespace test execution is claimed.

## Stage status

### Stage 1 — Market Data

- [x] Canonical Candle/Timeframe contracts
- [x] Provider-neutral market-data interface
- [x] Upstox historical/live boundaries
- [x] Normalization and quality validation
- [x] Duplicate/out-of-order/freshness handling
- [x] Timeframe aggregation for 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 1D, 1W
- [x] Redis live state/event publishing boundaries
- [x] PostgreSQL persistence/repositories
- [x] REST/WebSocket market APIs
- [x] Safe degraded startup
- [x] Historical CI verification for major market-data milestones
- [ ] Final Stage 1 verification including official Gradle wrapper artifact requirement

### Stage 2 — SMC/ICT

- [x] Swing structure
- [x] BOS/MSS/CHOCH
- [x] Equal-high/equal-low liquidity pools and sweeps
- [x] FVG
- [x] Displacement/order-block candidates
- [x] Premium/discount
- [x] ICT London/New York session levels
- [x] Deterministic orchestration and tests
- [ ] Fresh full product-flow verification

### Stage 3 — Replay

- [x] Deterministic replay clock and controls
- [x] Replay speeds
- [x] Stable event ordering
- [x] Look-ahead-safe visible history
- [x] SMC replay
- [x] Reusable strategy evaluation boundary
- [x] Replay-to-paper execution
- [x] Fresh backend CI verification at `33592488680`

### Stage 4 — Backtesting

- [x] Event-driven candle loop
- [x] Strategy protocol
- [x] Deterministic order validation/fills
- [x] Fees/slippage
- [x] Position lifecycle
- [x] P&L/win rate/expectancy/drawdown foundation
- [x] Trade ledger/order events
- [x] Risk-based sizing
- [x] Out-of-sample split
- [x] Persisted reports/repository/API
- [x] Strategy DSL execution adapter
- [x] Fresh backend CI verification at `33592488680`
- [x] Deterministic risk-gate foundation

### Stage 5 — AI

- [x] Declarative Strategy DSL
- [x] SMC signal-context adapter
- [x] Structured AI contracts
- [x] AI output validation/safety gate
- [x] Structured market-context builder
- [x] Safe AI-to-DSL translation boundary
- [x] Provider-neutral AI service
- [x] Analyze/strategy/explain-trade APIs
- [ ] Real external provider compatibility verification
- [ ] Android AI integration

### Stage 6 — Options

- [x] OptionContract / OptionChain / OptionLeg contracts
- [x] Strike/expiry/OI/volume/IV/quote fields
- [x] Contract lot-size support
- [x] Deterministic Black-Scholes price/Greeks foundation
- [x] Liquidity/spread validation
- [x] Deterministic delta-based strike selection
- [x] Multi-leg payoff engine
- [x] Maximum profit/loss and breakeven calculations
- [x] Capital requirement and risk/reward foundation
- [x] Risk-profile-aware strategy selection
- [x] Options analytics API
- [x] Provider-neutral option-chain interface
- [x] Options unit coverage
- [ ] Live option-chain provider integration
- [ ] Fresh runtime/CI verification of latest options changes

### Stage 7 — Paper Trading

- [x] Paper broker foundation
- [x] Simulated market/limit order lifecycle
- [x] Long/short positions and average price
- [x] Realized/unrealized P&L foundation
- [x] Fees/slippage simulation
- [x] Duplicate-order protection
- [x] Order-notional and position-size limits
- [x] Kill switch and loss-triggered halt foundation
- [x] Paper API boundary
- [x] Durable order/fill/position/audit repository boundary
- [x] Deterministic partial-fill simulation
- [x] Repository restart hydration and persisted account state
- [x] Deterministic risk-gate foundation
- [x] Optional risk-gate enforcement before paper order persistence
- [x] Replay-to-paper execution
- [x] Backend CI verification at `33592488680`

### Stage 8 — Brokers

- [x] Provider-neutral account/order/position/broker protocol
- [x] Non-secret authentication context boundary
- [x] Deterministic order reconciliation result boundary
- [x] Provider-neutral idempotency enforcement decorator/store
- [x] Durable PostgreSQL idempotency repository/migration
- [x] Ambiguous submission protection: failed broker calls remain reserved until reconciliation
- [x] Upstox adapter structure and read-side account/position/order mapping
- [x] Dhan adapter structure and read-side account/position/order mapping
- [x] Live mutation gating by default
- [x] Provider-neutral instrument/security-ID resolution boundary
- [x] Explicit exchange/product/validity order configuration boundary
- [x] Resolver wired into Upstox/Dhan live-order payload construction
- [x] Upstox BOD/Dhan scrip-master catalogue ingestion boundary
- [x] Secret-safe broker session lifecycle boundary
- [x] Upstox authorization-code token exchange boundary
- [x] Dhan consent/consume-token boundary
- [x] Dhan supported token renewal boundary
- [x] Token-to-session hydration boundary
- [x] CI verification of authentication implementation at `33592488680`
- [x] CI verification of latest idempotency-safety and durable-idempotency changes
- [x] CI verification of explicit controlled-execution idempotency-store requirement at `33598262758`
- [ ] Live broker runtime verification

### Stage 9 — Controlled Live Trading

- [x] Explicit activation boundary requiring exact confirmation
- [x] Deterministic risk gate before broker mutation
- [x] Position-limit enforcement through deterministic risk gate
- [x] Broker response/order-id confirmation boundary
- [x] Kill switch defaults active and can trip execution
- [x] Audit-event boundary for activation/rejection/broker confirmation
- [x] Idempotency boundary around broker mutation
- [x] Fail-closed startup authentication check
- [x] Fail-closed shutdown boundary
- [x] CI verification of controlled execution lifecycle tests at `33594099456`
- [x] Recovery boundary: reconnect/authenticate, refresh broker state, reconcile requested orders, and remain gated until explicit reactivation
- [x] Durable audit sink/repository boundary and PostgreSQL migration
- [x] Durable audit PostgreSQL integration test executed successfully in CI run `33595826727`
- [x] Durable broker idempotency repository and restart-persistence integration test executed successfully in CI run `33597951805`
- [x] Ambiguous broker submission is fail-closed at the idempotency boundary
- [x] Controlled execution requires an explicit idempotency store; no silent process-local fallback in the controlled-live constructor
- [ ] Production broker runtime verification
- [ ] Real live activation

### Stage 10 — Autonomous Trading

- [ ] Autonomous decision pipeline
- [ ] Portfolio-level risk
- [ ] Correlation exposure
- [ ] Position monitoring
- [ ] Emergency controls
- [ ] Production validation

## Safety status

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** The controlled executor is inert until startup succeeds and explicit activation is supplied; recovery and startup leave the kill switch active; shutdown fails closed. Dhan and Upstox adapters remain mutation-disabled by default. AI remains subordinate to deterministic strategy, validation, risk and execution controls. Ambiguous broker submission errors cannot be retried through the same idempotency key until broker state is explicitly resolved. Controlled live construction also requires an explicit idempotency store so restart-safe persistence cannot be accidentally omitted.

## Runtime limitation

No Codespace/runtime session is exposed through the connected tools, so no local test command is claimed. GitHub Actions is the available runtime verification path.

## Recent commits on main

- `ed5d538` — docs: record latest controlled execution CI verification
- `82a01ee` — test: require explicit controlled idempotency store
- `aa3bfd9` — docs: record durable idempotency CI verification
- `1c906d6` — fix: export broker side contract
- `47f3b29` — fix: expose durable broker idempotency store
- `d781243` — test: verify durable broker idempotency
- `467c4bb` — feat: add broker idempotency persistence migration
- `f7401cc` — feat: add durable broker idempotency repository
- `73158d3` — docs: record verified idempotency CI evidence
- `85d9892` — update controlled execution verification status
- `b354ebc` — test ambiguous submission idempotency safety

## Next execution

1. Continue Stage 9 reconciliation/failure-semantic review for deterministic safety gaps that can be covered without live credentials.
2. Review whether broker-reported unknown/manual orders need an explicit fail-closed reconciliation policy before controlled live activation.
3. Keep Stage 1 official Gradle wrapper artifact and Stage 5/6/8 external-provider/runtime gaps explicitly unverified.
4. Keep real live activation and autonomous trading disabled until all required evidence exists.
