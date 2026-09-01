# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Current branch

`main` only.

## Current stage

**Stage 8 — Broker Boundary Foundation**

## Latest implementation state

- Strategy DSL is integrated with deterministic backtesting and replay evaluation.
- Structured market context is built from visible candles plus deterministic SMC/ICT facts.
- AI has a provider-neutral HTTP/service boundary and `/api/v1/ai/analyze`, `/api/v1/ai/strategy`, `/api/v1/ai/explain-trade` endpoints. AI remains advisory and cannot authorize execution.
- Options have provider-neutral contracts, deterministic Black-Scholes Greeks, liquidity/spread filtering, deterministic delta-based strike selection, multi-leg expiry payoff, risk metrics, deterministic strategy selection, a provider-neutral option-chain boundary, and options analytics APIs.
- Paper trading has deterministic in-memory order/fill/position execution, configurable fees/slippage, limit-order behavior, duplicate-order protection, P&L accounting, configurable order-notional and position limits, a kill switch, and a paper-only API. Persistence, partial fills, replay-to-paper, and full risk/audit integration remain unfinished.
- Stage 8 has a provider-neutral account/order/position/broker protocol. The boundary now explicitly models non-secret authentication context and deterministic order reconciliation. No live broker adapter has been enabled.

## CI evidence

For commit `5b6818d`, GitHub Actions completed with:

- Android build: **SUCCESS**; `gradle assembleDebug` completed successfully.
- Backend tests: **FAILURE** at `pytest -q -m 'not integration'`; the job stopped before integration tests. The failure output is not exposed by the connected GitHub log endpoint, so the exact failing assertion is **UNVERIFIED** from the available tool surface.

For the latest status commit `aad451d`, the separate Android CI workflow completed **SUCCESS**. No workflow run is exposed yet for broker commit `fa94c8d` through the connected commit workflow endpoint.

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
- [ ] Idempotency enforcement implementation
- [ ] Dhan adapter
- [ ] Upstox order/position/account adapter
- [ ] Live broker runtime verification

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

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** Paper trading is isolated from real broker execution. The broker protocol is only a provider-neutral boundary; no real broker can place live orders through it yet. AI remains subordinate to deterministic strategy, validation, risk and execution controls.

## Runtime limitation

No Codespace/runtime session is exposed through the connected tools, so no local test command is claimed. GitHub Actions is the available runtime verification path.

## Recent commits on main

- `fa94c8d` — strengthen broker authentication and reconciliation boundary
- `81c6041` — record broker boundary and CI evidence
- `ffd067f` — define account/order/position/execution contracts
- `6b74209` — add provider-neutral broker boundary
- `aad451d` — record paper risk controls and current status
- `1d3644c` — expose paper kill switch status and controls

## Next execution

1. Implement broker idempotency enforcement at the provider-neutral boundary without enabling live execution.
2. Add Dhan and Upstox adapters only behind the common interface and only after inspecting/validating current official API contracts.
3. Return to paper persistence, audit, partial fills, and replay-to-paper integration.
4. Re-run CI verification after the next stable milestone.
