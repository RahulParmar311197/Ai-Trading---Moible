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
- Replay-to-paper and full deterministic risk/audit integration remain unfinished.
- Stage 8 has a provider-neutral account/order/position/broker protocol with non-secret authentication context and deterministic order reconciliation.
- Provider-neutral idempotency enforcement is implemented as an opt-in decorator/store: repeated successful submissions with the same client order ID return the original result, conflicting reuse is rejected, and failed submissions release the reservation for safe retry.
- Official Upstox and Dhan API contracts were reviewed before adding adapters. The adapters map provider account/position/order responses into the common broker models and keep live mutation disabled by default.
- Added a provider-neutral `BrokerInstrument`/`InstrumentResolver` boundary with explicit exchange segment, product type, validity enum, and lot-size metadata. Unknown canonical symbols are rejected rather than guessed.
- Wired the resolver into the explicit Upstox/Dhan live-order construction path. When live mutation is explicitly enabled, provider security IDs plus exchange/product/validity configuration now come from the resolver rather than hard-coded defaults. Unknown instruments fail before the network request. Live mutation remains disabled by default.
- Added deterministic provider catalogue ingestion for Upstox BOD JSON records and Dhan scrip-master rows. Catalogues map stable provider identifiers, exchange/segment, trading symbol, lot size, product policy and validity into the existing resolver boundary; unsupported Dhan exchange/segment combinations are rejected rather than guessed.
- Added a provider-neutral, secret-safe broker session lifecycle boundary with explicit unauthenticated/authenticated/expired/invalidated states. Upstox and Dhan adapters now own a session object and route HTTP authorization through it; the non-secret `BrokerAuthentication` projection never contains access tokens. External OAuth/token refresh can replace a session token without changing domain models.

## CI evidence

For commit `33589103436` (CI run), GitHub Actions executed the backend test suite with the current partial-fill implementation and reported **159 passed, 1 failed, 1 deselected**. The failure was `test_process_market_fills_resting_limit_orders_in_stable_order`: after an initial capped fill, `process_market()` did not revisit `PARTIALLY_FILLED` orders. This was a real implementation defect and was fixed in commit `32260bc`.

A new GitHub Actions run was triggered by the restart-hydration test commit `c2181f538c690fe2906aca1060b22e7536480f81`; at the time of this update its Android CI run was still **queued**, so no new pass/fail result is claimed.

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
- [ ] Replay-to-paper execution
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
- [ ] Broader risk-engine integration

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
- [ ] Full deterministic risk-engine integration
- [ ] Replay-to-paper integration
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

- `784a8d1` — allow persisted paper balance to reflect existing risk semantics
- `c2181f5` — test paper broker restart hydration
- `b854751` — add deterministic paper broker restart hydration
- `a3d6cba` — persist paper account state for restart recovery
- `58f946c` — add durable paper state hydration boundary
- `32260bc` — fix paper market processing for partial orders
- `2b8788e` — test deterministic paper partial fills
- `ec831aa` — keep invalid paper limits out of order book
- `4562c1a` — add deterministic paper partial fills
- `c0f1ad8` — export durable paper repository boundary

## Next execution

1. Verify the new paper persistence/hydration changes in GitHub Actions and fix only observed failures.
2. Integrate replay-to-paper after persistence and partial-fill semantics are verified.
3. Add controlled risk/execution integration only after deterministic risk boundaries are verified.
4. Complete real broker OAuth/refresh integration without exposing or storing secrets in source.
5. Re-run CI verification after each stable milestone.
