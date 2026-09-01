# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Working rule

Work directly on `main` only. Before implementation, inspect this file, `AI_TRADING_PLATFORM_BLUEPRINT_FULL.md`, the uploaded blueprint when available, and the actual repository state. Update this file after meaningful milestones.

## Current stage

**Stage 4 — Backtesting**

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

## Stage 1 status

**PARTIAL / UNVERIFIED** — prior CI verification exists for market-data work, but the placeholder Android Gradle wrapper and missing official `gradle-wrapper.jar` remain. Local runtime execution is unavailable.

## Stage 2 status

**PARTIAL / UNVERIFIED** — deterministic SMC/ICT implementation and unit coverage exist; fresh end-to-end verification and complete API/client product-flow integration remain outstanding.

## Stage 3 status

**PARTIAL / UNVERIFIED** — replay foundation and SMC integration exist; latest runtime/CI verification and replay-to-trade execution integration remain outstanding.

## Stage 4 status

**PARTIAL / UNVERIFIED** — deterministic engine, risk sizing, report projection, persistence migration/repository, and API endpoints now exist. The API currently accepts an explicit deterministic order plan as its transport adapter because the repository does not yet contain the blueprint's full reusable Strategy/DSL registry. This avoids inventing executable strategy code or a duplicate strategy framework. Latest runtime/CI verification remains unavailable.

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
- [ ] Full runtime/CI verification of latest Stage 4 changes
- [ ] Reusable strategy/DSL integration for backtest requests
- [ ] Broader risk-engine integration required by later trading stages

## Later stages

### Stage 5 — AI
- [ ] Structured market context
- [ ] AI analysis service
- [ ] Strategy DSL
- [ ] AI output validation
- [ ] Trade explanation

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

GitHub Actions is the available repository verification path. No workflow run is currently reported for latest commit `aed4fffc90677161eb5d379b3cb2368a61badac1`, and the connected commit status API reports no statuses. Therefore the newly added API/repository tests remain **UNVERIFIED**. No local/Codespace test execution is claimed.

## Recent commits on main

- `5912246` — persisted backtest report storage migration
- `4698ca3` — PostgreSQL backtest report repository
- `b54921c` — deterministic backtest API and report retrieval
- `818b3eb` — backtest repository dependency wiring
- `5ef6ccf` — backtest API router registration
- `550b8fd` — nested report JSON serialization fix
- `88a8b8b` — backtest API execution/validation tests
- `1fa1c55` — backtest report/persistence exports
- `aed4fff` — backtest repository serialization test

## Next task

Build the reusable blueprint-aligned Strategy/DSL boundary that can be consumed by replay, backtest, paper trading and later AI strategy generation, then integrate it with the existing deterministic backtest protocol. Do not bypass risk or create duplicate strategy frameworks. Keep runtime/CI verification explicitly UNVERIFIED until an actual workflow or runtime executes successfully.
