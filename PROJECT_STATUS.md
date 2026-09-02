# AI Trading Platform — Project Status

Last updated: 2026-09-02

## Current branch

`main` only.

## Current stage

**Stage 8 — Broker Integration Foundation**

## Latest implementation state

- Strategy DSL is integrated with deterministic backtesting and replay evaluation.
- Structured market context is built from visible candles plus deterministic SMC/ICT facts.
- AI has a provider-neutral HTTP/service boundary and `/api/v1/ai/analyze`, `/api/v1/ai/strategy`, `/api/v1/ai/explain-trade` endpoints. AI remains advisory and cannot authorize execution.
- Options have provider-neutral contracts, deterministic Black-Scholes Greeks, liquidity/spread filtering, deterministic delta-based strike selection, multi-leg expiry payoff, risk metrics, deterministic strategy selection, a provider-neutral option-chain boundary, and options analytics APIs.
- Paper trading has deterministic in-memory order/fill/position execution, configurable fees/slippage, limit-order behavior, duplicate-order protection, P&L accounting, configurable order-notional and position limits, a kill switch, and a paper-only API.
- Paper trading now has durable order/fill/position/audit persistence, deterministic partial-fill simulation, and a restart-hydration boundary backed by the existing SQLAlchemy executor's `fetch_one`/`fetch_all` read methods. Account balance, cumulative realized P&L, and halt state are persisted separately so restoration does not replay orders or contact live brokers.
- Replay-to-paper execution is implemented through a paper-only adapter. Replay-visible candles drive deterministic strategy evaluation; signals are translated into paper market orders, and optional stop/target brackets are evaluated on later replay candles. The adapter cannot route replay orders to live brokers.
- Added a pure `DeterministicExecutionGate` with explicit order-notional, position-quantity, daily-loss, and halt checks. It returns an approval decision and never submits an order itself, preserving the deterministic DATA → VALIDATION → STRATEGY → RISK → EXECUTION GATE → BROKER separation.
- The deterministic execution gate is now an optional pre-trade gate on `PaperBroker.place_order`. When configured, rejected orders are stopped before paper order persistence; existing paper risk limits remain available for backward-compatible callers.
- Stage 8 has a provider-neutral account/order/position/broker protocol with non-secret authentication context and deterministic order reconciliation.
- Provider-neutral idempotency enforcement is implemented as an opt-in decorator/store: repeated successful submissions with the same client order ID return the original result, conflicting reuse is rejected, and failed submissions release the reservation for safe retry.
- Official Upstox and Dhan API contracts were reviewed before adding adapters. The adapters map provider account/position/order responses into the common broker models and keep live mutation disabled by default.
- Added a provider-neutral `BrokerInstrument`/`InstrumentResolver` boundary with explicit exchange segment, product type, validity enum, and lot-size metadata. Unknown canonical symbols are rejected rather than guessed.
- Wired the resolver into the explicit Upstox/Dhan live-order construction path. When live mutation is explicitly enabled, provider security IDs plus exchange/product/validity configuration now come from the resolver rather than hard-coded defaults. Unknown instruments fail before the network request. Live mutation remains disabled by default.
- Added deterministic provider catalogue ingestion for Upstox BOD JSON records and Dhan scrip-master rows. Catalogues map stable provider identifiers, exchange/segment, trading symbol, lot size, product policy and validity into the existing resolver boundary; unsupported Dhan exchange/segment combinations are rejected rather than guessed.
- Added a provider-neutral, secret-safe broker session lifecycle boundary with explicit unauthenticated/authenticated/expired/invalidated states. Upstox and Dhan adapters now own a session object and route HTTP authorization through it; the non-secret `BrokerAuthentication` projection never contains access tokens. External OAuth/token refresh can replace a session token without changing domain models.

## CI evidence

GitHub Actions run `33591340777` executed the backend suite at commit `52b82d4fd1ed6387fc4b11b430faf6d3d05be9e2` and reported **166 passed, 1 failed, 1 deselected**. The observed failure was `test_replay_paper_executes_only_through_paper_broker_and_closes_bracket`: the test expected exit order `replay-00000000-exit-00000002`, but candle index 1 already had a default high of 105 and therefore correctly triggered the 105 target before index 2. The test expectation was corrected in commit `5e41faf` to assert the index-1 exit. The same run's Android build completed successfully, including debug APK assembly.

A follow-up paper-risk integration test was added in commit `2937b4b` after wiring the optional deterministic execution gate into `PaperBroker`. No CI pass is claimed for commits after `52b82d4` until a completed run is observed.

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
- [ ] Fresh final verification

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
- [ ] Fresh final CI verification
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
- [ ] Full paper-trading verification after latest changes

### Stage 8 — Brokers

- [x] Provider-neutral account/order/position/broker protocol
- [x] Non-secret authentication context boundary
- [x] Deterministic order reconciliation result boundary
- [x] Provider-neutral idempotency enforcement decorator/store
- [x] Upstox adapter structure and read-side account/position/order mapping
- [x] Dhan adapter structure and read-side account/position/order mapping
- [x] Live mutation gating by default
- [x] Provider-neutral instrument/security-ID resolution boundary
- [x] Explicit exchange/product/validity order configuration boundary
- [x] Resolver wired into Upstox/Dhan live-order payload construction
- [x] Upstox BOD/Dhan scrip-master catalogue ingestion boundary
- [x] Secret-safe broker session lifecycle boundary
- [ ] Auth/session lifecycle integration with real OAuth/refresh endpoints
- [ ] Live broker runtime verification
- [ ] Controlled execution/risk integration

### Stage 9 — Controlled Live Trading

- [ ] Explicit activation
- [ ] Deterministic risk engine
- [ ] Position limits
- [ ] Broker confirmation
- [ ] Kill switches
- [ ] Audit logging
- [ ] Safe startup/shutdown

### Stage 10 — Autonomous Trading

- [ ] Autonomous decision pipeline
- [ ] Portfolio-level risk
- [ ] Correlation exposure
- [ ] Position monitoring
- [ ] Emergency controls
- [ ] Production validation

## Safety status

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** Paper trading is isolated from real broker execution. The Dhan and Upstox adapters default to mutation-disabled mode. AI remains subordinate to deterministic strategy, validation, risk and execution controls.

## Runtime limitation

No Codespace/runtime session is exposed through the connected tools, so no local test command is claimed. GitHub Actions is the available runtime verification path.

## Recent commits on main

- `2937b4b` — test paper broker risk gate integration
- `3ee462a` — wire deterministic risk gate into paper execution
- `5e41faf` — fix replay paper target-hit test index
- `815d450` — test deterministic execution risk gate
- `620c700` — export execution risk gate
- `dd8bf31` — add deterministic execution risk gate
- `b5efd27` — test deterministic replay-to-paper execution
- `53633d0` — export replay-to-paper execution boundary
- `a2fd377` — add deterministic replay-to-paper execution boundary
- `784a8d1` — allow persisted paper balance to reflect existing risk semantics
- `c2181f5` — test paper broker restart hydration
- `b854751` — add deterministic paper broker restart hydration
- `a3d6cba` — persist paper account state for restart recovery
- `58f946c` — add durable paper state hydration boundary
- `32260bc` — fix paper market processing for partial orders

## Next execution

1. Verify the replay-paper test correction and paper risk-gate integration in GitHub Actions and fix only observed failures.
2. Complete real broker OAuth/refresh integration without exposing or storing secrets in source.
3. Integrate controlled broker execution only behind deterministic risk, confirmation, idempotency and kill-switch gates.
4. Re-run CI verification after each stable milestone.
