# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Working rule

Work directly on `main` only. Before implementation, inspect this file, `AI_TRADING_PLATFORM_BLUEPRINT_FULL.md`, the uploaded blueprint when available, and the actual repository state. Update this file after meaningful milestones.

## Current stage

**Stage 5 — Strategy & AI Foundation**

## Completed

- [x] Repository/project foundation
- [x] Full master blueprint preserved
- [x] FastAPI + Android skeleton
- [x] PostgreSQL and CI/test foundation
- [x] Canonical market models and normalization
- [x] Instrument/candle/tick persistence and repositories
- [x] Provider-neutral market-data feed boundary
- [x] REST market-data API and PostgreSQL wiring
- [x] WebSocket market stream
- [x] Redis live state and event publisher boundaries
- [x] Redis → WebSocket runtime boundary
- [x] Provider → publisher runtime bridge
- [x] Market-data freshness/quality validation
- [x] Provider quality-validation gate
- [x] Explicit provider-selection configuration
- [x] Upstox V3 historical candle adapter
- [x] Upstox authentication/access-token configuration
- [x] Upstox V3 live authorization/transport boundary
- [x] Upstox protobuf decoder injection boundary
- [x] Upstox SDK-backed decoder boundary
- [x] Upstox live LTP normalization
- [x] Upstox LTPC/full-feed extraction
- [x] Application startup provider selection
- [x] Safe degraded startup when live data is not configured
- [x] Redis publisher implementation and provider startup wiring
- [x] Provider → validation → publisher integration coverage
- [x] Android CI build job
- [x] Canonical deterministic candle timeframe aggregation for 1m–4h, 1D and 1W
- [x] Timeframe aggregation unit coverage
- [x] Credential-free degraded startup coverage
- [x] CI Python import-path correction
- [x] Internal `Timeframe.TICK` contract while keeping TICK out of public candle API
- [x] Official Upstox protobuf import/version verification in CI
- [x] Backend non-integration and integration suites previously passed in CI
- [x] Android `assembleDebug` previously passed in CI
- [x] Stage 2 deterministic swing detection with right-side confirmation
- [x] Stage 2 BOS/MSS/CHOCH structure detection
- [x] Stage 2 equal-high/equal-low liquidity pools and sweeps
- [x] Stage 2 three-candle FVG detection
- [x] Stage 2 displacement/order-block candidates with strength scoring
- [x] Stage 2 premium/discount dealing range
- [x] Stage 2 ICT London/New York sessions and levels
- [x] Stage 2 deterministic SMC orchestration and structured signal context
- [x] Stage 2 unit coverage for confirmation, structure, FVG, premium/discount, sessions and determinism
- [x] Stage 3 deterministic replay clock and Play/Pause/Reset/Next/Previous controls
- [x] Stage 3 configurable replay speeds 0.5x/1x/2x/5x/10x
- [x] Stage 3 deterministic historical event ordering and stable tie-breaking
- [x] Stage 3 timeframe filtering and look-ahead-safe historical state
- [x] Stage 3 deterministic replay statistics foundation and reset lifecycle
- [x] Stage 3 unit coverage
- [x] Stage 3 historical repository loading boundary
- [x] Stage 3 integration with existing deterministic SMC engine without duplicate strategy framework
- [x] Stage 4 deterministic event-driven backtest foundation
- [x] Stage 4 candle-visible strategy protocol
- [x] Stage 4 deterministic market-order validation and fills
- [x] Stage 4 current-candle stop/target handling
- [x] Stage 4 deterministic fees/slippage
- [x] Stage 4 P&L, win rate, expectancy, equity curve and drawdown foundation
- [x] Stage 4 multi-candle position lifecycle
- [x] Stage 4 explicit OPEN/CLOSE/CLOSE_END order events and trade ledger
- [x] Stage 4 chronological out-of-sample split support
- [x] Stage 4 deterministic risk-based position sizing using balance, risk percentage and stop distance
- [x] Stage 4 stable `BacktestReport` projection for API/report consumers
- [x] Stage 4 persisted backtest report migration
- [x] Stage 4 PostgreSQL backtest report repository boundary
- [x] Stage 4 `POST /api/v1/backtest` deterministic execution endpoint
- [x] Stage 4 `GET /api/v1/backtest/{id}` persisted report retrieval endpoint
- [x] Stage 4 API validation and repository serialization test coverage
- [x] Strategy DSL package boundary
- [x] Declarative strategy condition types from blueprint
- [x] Declarative AND/OR/NOT and comparison/range evaluation
- [x] Strategy risk constraints with bounded risk percentage
- [x] Structured signal context for deterministic strategy evaluation
- [x] SMC `SignalContext` → Strategy DSL adapter
- [x] Strategy DSL validation tests
- [x] Structured AI analysis/trade-proposal contracts
- [x] Deterministic AI output validation gate
- [x] AI safety validation tests
- [x] Reusable `DslBacktestStrategy` adapter over the existing backtest strategy protocol
- [x] Strategy risk percentage propagation into deterministic backtest position sizing
- [x] Backtest API accepts validated `StrategyDefinition` without creating a second strategy framework
- [x] Strategy condition equality semantics for declarative value matching
- [x] Strategy-to-backtest deterministic adapter tests
- [x] Replay strategy evaluation boundary using the existing `BacktestStrategy` protocol
- [x] Deterministic structured market-context builder from visible candles and SMC/ICT facts
- [x] Safe AI-to-DSL translation boundary with strict Pydantic validation
- [x] Rejection of executable/broker instructions from AI strategy payloads
- [x] Provider-neutral HTTP AI service boundary with explicit timeout/auth configuration
- [x] AI analysis/strategy/trade-explanation service layer
- [x] `/api/v1/ai/analyze`, `/api/v1/ai/strategy`, `/api/v1/ai/explain-trade` endpoints
- [x] AI provider configuration gate that keeps AI disabled when no endpoint is configured
- [x] AI service failure and validation unit coverage
- [x] Replay/backtest regression fixes identified by GitHub Actions
- [x] Liveness/readiness separation: `/health` remains healthy while `/ready` exposes market-data degraded state

## Stage 1 status

**PARTIAL / UNVERIFIED** — prior CI verification exists for market-data work, but the placeholder Android Gradle wrapper and missing official `gradle-wrapper.jar` remain. Latest complete Stage 1 verification is not yet established.

## Stage 2 status

**PARTIAL / UNVERIFIED** — deterministic SMC/ICT implementation and unit coverage exist; fresh end-to-end verification and complete API/client product-flow integration remain outstanding.

## Stage 3 status

**PARTIAL / UNVERIFIED** — replay foundation, SMC integration, and reusable strategy evaluation boundary exist; latest complete verification and replay-to-paper execution remain outstanding.

## Stage 4 status

**PARTIAL / UNVERIFIED** — deterministic engine, risk sizing, report projection, persistence migration/repository, API endpoints, and reusable Strategy DSL backtest adapter exist. GitHub Actions found and drove fixes for strategy invocation visibility and replay state indexing; the latest fix is awaiting a fresh workflow result.

## Stage 4 checklist

- [x] Event-driven candle loop foundation
- [x] Strategy interface/protocol
- [x] Deterministic market-order validation
- [x] Current-candle stop/target handling
- [x] Fees/slippage
- [x] Basic P&L metrics
- [x] Equity curve and max drawdown foundation
- [x] Unit coverage
- [x] Multi-candle position/order lifecycle
- [x] Explicit trade ledger/order events
- [x] Deterministic risk-based position sizing
- [x] Out-of-sample split support
- [x] Stable report projection
- [x] Backtest persistence migration
- [x] Backtest report repository
- [x] POST backtest API
- [x] GET backtest report API
- [x] API/repository unit coverage
- [x] Integrate reusable Strategy DSL into backtest strategy evaluation
- [x] Integrate reusable strategy protocol into replay evaluation
- [ ] Fresh CI/runtime verification after fixes
- [ ] Broader risk-engine integration required by later trading stages

## Stage 5 — AI / Strategy

- [x] Declarative Strategy DSL foundation
- [x] SMC signal-context adapter
- [x] Structured AI analysis/trade-proposal contracts
- [x] Deterministic AI output validation gate
- [x] Strategy DSL → backtest execution adapter
- [x] Strategy DSL → replay evaluation boundary
- [x] Structured market context pipeline from visible/replay market facts
- [x] Safe AI-to-DSL declarative translation/validation boundary
- [x] Provider-neutral AI service boundary
- [x] AI analysis endpoint
- [x] AI strategy endpoint
- [x] AI trade explanation endpoint
- [ ] Real external AI provider contract verification
- [ ] Android AI feature integration

## Later stages

### Stage 6 — Options
- [ ] Option chain
- [ ] Greeks
- [ ] IV
- [ ] Payoff engine
- [ ] Options liquidity validation

### Stage 7 — Paper trading
- [ ] Paper broker
- [ ] Simulated order lifecycle
- [ ] Position management
- [ ] Portfolio P&L

### Stage 8 — Brokers
- [ ] Broker abstraction
- [ ] Dhan adapter
- [ ] Upstox adapter
- [ ] Authentication/authorization
- [ ] Order reconciliation
- [ ] Idempotency

### Stage 9 — Controlled live trading
- [ ] Risk engine
- [ ] Kill switches
- [ ] Market-data freshness checks
- [ ] Broker health checks
- [ ] Audit logging
- [ ] Limited live deployment

### Stage 10 — Autonomous trading
- [ ] Autonomous decision pipeline
- [ ] Portfolio-level risk
- [ ] Correlation exposure
- [ ] Position monitoring
- [ ] Emergency controls
- [ ] Production validation

## Safety gates

Live/autonomous trading remains disabled/gated. It must not be enabled until replay, backtesting, paper trading, risk controls, broker reconciliation, failure handling and explicit user activation are implemented and tested. AI remains subordinate to deterministic strategy, validation, risk and execution gates.

## Runtime / CI verification

GitHub Actions is the available real runtime verification path. For commit `0ff9c41141cc086c566ab9377b289c0b3fd4dda1`, Android `assembleDebug` passed, while the backend non-integration suite reported 4 failures: one stale backtest strategy-visibility expectation, one health-contract expectation, and two replay strategy index errors. Those failures were inspected from the actual CI logs and fixes were prepared on `main`. A fresh workflow for the current fix commit is required before marking these changes verified. No local/Codespace command is claimed as executed.

## Recent commits on main

- `c9389d4` — provider-neutral AI analysis service and APIs
- `0ff9c41` — deterministic market context, safe AI-to-DSL translation, and replay strategy evaluation
- `2405bc9` — integrate Strategy DSL with deterministic backtesting
- `7600193` — status update for AI safety and strategy context milestones
- `3f481d5` — AI safety validation tests
- `3b18f9a` — deterministic AI output validation gate
- `943bfb3` — structured AI analysis/trade proposal contracts
- `8fb8c5b` — AI contract boundary

## Next task

Verify the fresh CI result for the fixes. If green, continue Stage 6 with provider-neutral option-chain contracts, deterministic Black-Scholes-style Greeks, payoff calculation, and liquidity validation. If CI reports new failures, fix those first. Keep live/autonomous execution gated.
