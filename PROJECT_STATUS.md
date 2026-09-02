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
- Paper trading has deterministic in-memory order/fill/position execution, configurable fees/slippage, limit-order behavior, duplicate-order protection, P&L accounting, configurable order-notional and position limits, a kill switch, and a paper-only API. Persistence, partial fills, replay-to-paper, and full risk/audit integration remain unfinished.
- Stage 8 has a provider-neutral account/order/position/broker protocol with non-secret authentication context and deterministic order reconciliation.
- Provider-neutral idempotency enforcement is implemented as an opt-in decorator/store: repeated successful submissions with the same client order ID return the original result, conflicting reuse is rejected, and failed submissions release the reservation for safe retry.
- Official Upstox and Dhan API contracts were reviewed before adding adapters. The adapters map provider account/position/order responses into the common broker models and keep live mutation disabled by default.
- Added a provider-neutral `BrokerInstrument`/`InstrumentResolver` boundary with explicit exchange segment, product type, validity enum, and lot-size metadata. Unknown canonical symbols are rejected rather than guessed.
- Wired the resolver into the explicit Upstox/Dhan live-order construction path. When live mutation is explicitly enabled, provider security IDs plus exchange/product/validity configuration now come from the resolver rather than hard-coded defaults. Unknown instruments fail before the network request. Live mutation remains disabled by default.
- Added deterministic provider catalogue ingestion for Upstox BOD JSON records and Dhan scrip-master rows. Catalogues map stable provider identifiers, exchange/segment, trading symbol, lot size, product policy and validity into the existing resolver boundary; unsupported Dhan exchange/segment combinations are rejected rather than guessed.
- Added a provider-neutral, secret-safe broker session lifecycle boundary with explicit unauthenticated/authenticated/expired/invalidated states. Upstox and Dhan adapters now own a session object and route HTTP authorization through it; the non-secret `BrokerAuthentication` projection never contains access tokens. External OAuth/token refresh can replace a session token without changing domain models.

## CI evidence

For commit `5b6818d`, GitHub Actions completed with:

- Android build: **SUCCESS**; `gradle assembleDebug` completed successfully.
- Backend tests: **FAILURE** at `pytest -q -m 'not integration'`; the job stopped before integration tests. The failure output was not exposed by the connected GitHub log endpoint, so the exact failing assertion remains **UNVERIFIED** from that historical run.

For status commit `aad451d`, the separate Android CI workflow completed **SUCCESS**.

For the current broker-session milestone commit `b684c0a`, GitHub Actions run `33588339917` was observed **IN PROGRESS** when last checked. Android was executing `gradle assembleDebug`; backend was still in checkout/setup. No completion result is claimed yet.

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
- [ ] Persistent order/trade/audit repository
- [ ] Partial-fill simulation
- [ ] Full deterministic risk-engine integration
- [ ] Replay-to-paper integration
- [ ] Full paper-trading verification

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

- `b684c0a` — export broker session lifecycle contract
- `40d5bf0` — integrate Dhan session lifecycle
- `9a62d07` — integrate Upstox session lifecycle
- `d61dd3f` — route HTTP transport through sessions
- `7dd7b53` — cover broker session lifecycle and secret boundary
- `01b2159` — add secret-safe session lifecycle boundary
- `532a326` — export instrument catalogue boundary
- `469ab2c` — cover provider catalogue ingestion
- `9052438` — add provider instrument catalogue ingestion
- `ee6816f` — verify provider order payload resolution

## Next execution

1. Complete verification of the broker-session milestone through GitHub Actions.
2. Add durable paper order/fill/position/audit persistence using the existing repository/SQL boundaries.
3. Add deterministic partial-fill simulation without weakening paper/live separation.
4. Integrate replay-to-paper only after persistence and partial-fill semantics are covered.
5. Add controlled risk/execution boundary only after deterministic risk integration is verified.
6. Re-run CI verification after each stable milestone.
