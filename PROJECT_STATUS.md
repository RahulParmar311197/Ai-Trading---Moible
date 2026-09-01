# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Current branch

`main` only.

## Current stage

**Stage 7 — Paper Trading Foundation**

## Latest implementation state

- Strategy DSL is integrated with deterministic backtesting and replay evaluation.
- Structured market context is built from visible candles plus deterministic SMC/ICT facts.
- AI has a provider-neutral HTTP/service boundary and `/api/v1/ai/analyze`, `/api/v1/ai/strategy`, `/api/v1/ai/explain-trade` endpoints. AI remains advisory and cannot authorize execution.
- Options have provider-neutral contracts, deterministic Black-Scholes Greeks, liquidity/spread filtering, deterministic delta-based strike selection, multi-leg expiry payoff, risk metrics, deterministic strategy selection, a provider-neutral option-chain boundary, and options analytics APIs.
- Paper trading has deterministic in-memory order/fill/position execution, configurable fees/slippage, limit-order behavior, duplicate-order protection, position/account P&L accounting, configurable order-notional and position limits, a kill switch, and a paper-only API. Persistence, partial fills, replay integration, and full risk/audit integration remain unfinished.

## Latest milestone — paper risk controls

### IMPLEMENTED

- Maximum paper order-notional guard.
- Maximum absolute paper position-size guard.
- Persistent in-process realized P&L accumulator for daily-loss decisions.
- Deterministic kill switch rejecting all new paper orders while halted.
- Explicit kill-switch clear operation.
- Automatic paper trading halt when configured realized-loss threshold is reached.
- Paper account endpoint now reports halted state.
- Paper API exposes kill-switch activation/clear endpoints.
- Unit coverage for order/position limits and kill-switch behavior.

### TESTS RUN

`UNVERIFIED — no Codespace/runtime session is exposed through the connected tools.`

### TESTS PASSED

No local test execution claimed for this milestone.

### BUILDS

No local build execution claimed.

### CI

GitHub Actions for the latest `main` commits is queued/in progress; no pass/fail result is claimed until a completed run is observed.

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

- [ ] Provider-neutral broker abstraction
- [ ] Dhan adapter
- [ ] Upstox order/position/account adapter
- [ ] Authentication boundary
- [ ] Reconciliation/idempotency

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

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** Paper trading is isolated from real broker execution. AI remains subordinate to deterministic strategy, validation, risk and execution controls.

## Runtime limitation

No Codespace/runtime session is exposed through the connected tools, so no local test command is claimed. GitHub Actions is the runtime verification path available through the repository integration.

## Recent commits on main

- `1d3644c` — expose paper kill switch status and controls
- `e53a278` — cover paper risk limits and kill switch
- `f62a72f` — add deterministic paper risk limits and kill switch
- `63308d7` — register paper trading API
- `d29b3f1` — add paper trading API
- `5b6818d` — add paper trading tests
- `76875d0` — implement deterministic paper execution
- `f203bca` — define paper order/fill/position contracts
- `e26408f` — add paper trading package
- `7b479bb` — correct options payoff test expectations
- `d423f3e` — add options payoff and strategy tests
- `5848bf4` — export options payoff and strategy services
- `4125705` — add options analytics API
- `0b8592c` — add provider-neutral option-chain boundary

## Next execution

1. Inspect completed GitHub Actions for the latest `main` commits and fix any real failures.
2. Implement deterministic partial-fill behavior in the paper broker where practical.
3. Add persistent paper order/fill/audit storage using the repository's existing database abstractions after inspection.
4. Integrate replay with the paper broker.
5. Then build the provider-neutral broker abstraction before any controlled live functionality.
