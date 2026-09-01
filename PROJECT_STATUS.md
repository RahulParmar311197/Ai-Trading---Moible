# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Current branch

`main` only.

## Current stage

**Stage 6 — Options**

## Latest implementation state

- Strategy DSL is integrated with deterministic backtesting and replay evaluation.
- Structured market context is built from visible candles plus deterministic SMC/ICT facts.
- AI has a provider-neutral HTTP/service boundary and `/api/v1/ai/analyze`, `/api/v1/ai/strategy`, `/api/v1/ai/explain-trade` endpoints. AI remains advisory and cannot authorize execution.
- Options have provider-neutral contracts, deterministic Black-Scholes Greeks, liquidity/spread filtering, deterministic delta-based strike selection, a multi-leg expiry payoff engine, risk metrics, deterministic strategy selection, a provider-neutral option-chain boundary, and options analytics APIs.
- Live option-chain provider integration remains unfinished and requires a real provider implementation/credentials.

## Latest milestone — options payoff/strategy layer

### IMPLEMENTED

- `OptionContract.lot_size` added to support correct multi-leg notional calculations.
- Deterministic `payoff_at()` for multi-leg expiry P&L.
- Deterministic maximum-profit/maximum-loss detection with unbounded results represented as `null`.
- Breakeven detection across piecewise-linear option payoffs.
- Capital requirement and risk/reward calculation when the loss side is bounded.
- Risk-profile-aware deterministic strategy catalogue for bullish, bearish and neutral bias.
- Liquidity-ranked option selection using the existing liquidity validator.
- Provider-neutral `OptionChainProvider` plus safe unconfigured implementation.
- `/api/v1/options/payoff` endpoint.
- `/api/v1/options/strategies` endpoint.
- `/api/v1/options/liquidity` endpoint.
- Options payoff/strategy unit coverage including lot size, bounded spreads, unbounded calls and risk-profile restrictions.

### TESTS RUN

`UNVERIFIED — no Codespace/runtime session is exposed through the connected tools.`

### TESTS PASSED

No local test execution claimed for this milestone.

### BUILDS

No local build execution claimed.

### CI

A fresh GitHub Actions result for the latest options commits has not yet been observed.

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

- [ ] Paper broker
- [ ] Simulated order lifecycle
- [ ] Positions/average price
- [ ] Realized/unrealized P&L
- [ ] Fees/slippage
- [ ] Risk controls
- [ ] Audit trail

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

**LIVE/AUTONOMOUS TRADING REMAINS GATED.** No commit enables unrestricted live or autonomous execution. AI remains subordinate to deterministic strategy, validation, risk and execution controls.

## Runtime limitation

No Codespace/runtime session is exposed through the connected tools, so no local test command is claimed. GitHub Actions is the runtime verification path available through the repository integration.

## Recent commits on main

- `7b479bb` — correct options payoff test expectations
- `d423f3e` — add options payoff and strategy tests
- `5848bf4` — export options payoff and strategy services
- `4125705` — add options analytics API
- `0b8592c` — add provider-neutral option-chain boundary
- `184ac37` — add deterministic options strategy selection
- `f7f8db8` — add option contract lot size
- `db37677` — add deterministic multi-leg payoff engine
- `350627e` — fix Pydantic options quantity validation
- `465bb6a` — align startup tests with liveness/readiness separation
- `a2a392d` — options contracts, Greeks and liquidity foundation

## Next execution

1. Inspect GitHub Actions for fresh verification of the latest main commits.
2. Fix any reported failures.
3. If clean, continue Stage 6 with a concrete provider adapter boundary only where repository architecture and available credentials support it.
4. Then begin Stage 7 paper trading, reusing existing execution/risk abstractions rather than creating duplicates.
