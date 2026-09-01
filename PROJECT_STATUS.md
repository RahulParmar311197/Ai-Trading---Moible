# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Current branch

`main` only.

## Current stage

**Stage 6 — Options Foundation**

## Latest implementation state

- Strategy DSL is integrated with deterministic backtesting and replay evaluation.
- Structured market context is built from visible candles plus deterministic SMC/ICT facts.
- AI has a provider-neutral HTTP/service boundary and `/api/v1/ai/analyze`, `/api/v1/ai/strategy`, `/api/v1/ai/explain-trade` endpoints. AI remains advisory and cannot authorize execution.
- Options now have provider-neutral contracts, deterministic Black-Scholes Greeks, liquidity/spread filtering, and deterministic delta-based strike selection.
- Multi-leg options payoff, options strategy APIs, and live option-chain provider integration remain unfinished.

## CI evidence

For commit `a2a392d1bc9aadcd6aa656f2b0f9f103e63a2218`, GitHub Actions backend tests executed **119 tests with 2 failures**; 117 passed. The two failures were stale startup tests expecting `/health` to report degraded. The implementation intentionally separates liveness (`/health`) from readiness (`/ready`), so the tests were updated accordingly in commit `465bb6a8381941b55a0c11597ad189f7a2fba970`.

The same `a2a392d1...` run's Android build is still executing; no result is claimed yet. Commit `350627e5d41e091dd8e9bdfb89ff1d829d269a92` additionally fixes a Pydantic deprecation in `OptionLeg` quantity validation. A fresh CI run for the latest `main` is required before these fixes can be marked verified.

## Completed foundations

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
- [x] Deterministic Black-Scholes price/Greeks foundation
- [x] Liquidity/spread validation
- [x] Deterministic delta-based strike selection
- [x] Options unit coverage
- [ ] Multi-leg payoff engine
- [ ] Maximum profit/loss and breakeven calculations
- [ ] Options strategy selection API
- [ ] Provider option-chain integration
- [ ] Runtime/CI verification of latest options changes

## Later stages

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

No Codespace/runtime session is exposed through the connected tools, so no local test command is claimed. GitHub Actions is the actual runtime verification path used here.

## Recent commits on main

- `350627e` — fix Pydantic options quantity validation
- `465bb6a` — align startup tests with liveness/readiness separation
- `a2a392d` — options contracts, Greeks and liquidity foundation
- `fac9191` — replay and health regression implementation fixes
- `c9389d4` — provider-neutral AI analysis service and APIs
- `0ff9c41` — market context, safe AI-to-DSL translation, replay strategy evaluation
- `2405bc9` — Strategy DSL deterministic backtesting integration

## Next execution

1. Wait for/inspect the fresh CI result for the latest `main` fixes.
2. Fix any remaining test failures.
3. Complete the multi-leg options payoff/strategy layer if repository write tooling permits it.
4. Add the options API/provider boundary.
5. Move to Stage 7 paper trading only after the options foundation is sufficiently verified.
