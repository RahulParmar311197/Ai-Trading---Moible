# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Working rule

Before every implementation task, check this file, `AI_TRADING_PLATFORM_BLUEPRINT_FULL.md`, and the current `main` repository state. Work directly on `main` only. Update this file after each completed milestone or meaningful change.

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
- [x] Redis publisher implementation
- [x] Provider → Redis publisher startup wiring on `main`
- [x] Provider → Redis startup integration test
- [x] Provider → validation → publisher integration coverage aligned with actual runtime API
- [x] Android CI build job added to GitHub Actions
- [x] Canonical deterministic candle timeframe aggregation for 1m–4h, 1D and 1W
- [x] Timeframe aggregation unit coverage
- [x] Credential-free degraded startup path exercised through the FastAPI lifespan in unit coverage
- [x] Confirmed and fixed CI Python import-path failure caused by `PYTHONPATH=backend` while the job already runs in `backend`
- [x] Added internal `Timeframe.TICK` contract required by live LTP normalization
- [x] Kept internal `TICK` out of the public candle-timeframe API
- [x] Official Upstox protobuf import/version verification passed in CI
- [x] Backend non-integration test suite passed in CI after timeframe API fix
- [x] Backend integration test suite passed in CI after timeframe API fix
- [x] Android `assembleDebug` passed in CI after timeframe API fix
- [x] Stage 2 deterministic swing detection with right-side confirmation
- [x] Stage 2 market-structure break detection (BOS/MSS/CHOCH)
- [x] Stage 2 equal-high/equal-low liquidity pools and sweep detection
- [x] Stage 2 three-candle FVG detection
- [x] Stage 2 displacement-based order-block candidates with strength scoring
- [x] Stage 2 premium/discount dealing-range calculation
- [x] Stage 2 explicit ICT London/New York session windows and session levels
- [x] Stage 2 deterministic SMC orchestration and structured signal context
- [x] Stage 2 unit coverage for confirmation, structure, FVG, premium/discount, sessions, and determinism
- [x] Stage 3 deterministic replay clock with Play/Pause/Reset/Next/Previous controls
- [x] Stage 3 configurable replay speeds: 0.5x, 1x, 2x, 5x, 10x
- [x] Stage 3 deterministic historical event ordering with stable tie-breaking
- [x] Stage 3 timeframe-filtered replay using canonical Candle/Timeframe
- [x] Stage 3 look-ahead-safe historical market state (only data at or before replay time)
- [x] Stage 3 deterministic replay statistics foundation
- [x] Stage 3 replay reset/state lifecycle
- [x] Stage 3 unit coverage for ordering, look-ahead protection, controls, reset, timeframe filtering, and statistics
- [x] Stage 3 historical repository loading boundary
- [x] Stage 3 integration with the existing deterministic SMC engine without creating a duplicate strategy framework
- [x] Stage 4 deterministic event-driven backtest foundation
- [x] Stage 4 strategy protocol using candle-visible state only
- [x] Stage 4 market-order validation and deterministic fills
- [x] Stage 4 stop/target resolution from the current candle
- [x] Stage 4 deterministic fees and slippage
- [x] Stage 4 P&L, win rate, expectancy, equity curve, and drawdown foundation
- [x] Stage 4 unit coverage for look-ahead safety, stops/targets, fees/slippage, validation, and metrics

## Stage 1 status

**PARTIAL / UNVERIFIED**

Backend and Android CI verification is complete for the recorded market-data work, but the repository still contains a placeholder `android/gradlew` and does not contain an official generated `gradle-wrapper.jar`. Local Codespace/runtime execution is unavailable from this environment, so official wrapper and local end-to-end verification remain `UNVERIFIED`.

## Stage 2 status

**PARTIAL / UNVERIFIED**

The deterministic SMC/ICT engine and unit coverage are implemented. Earlier CI evidence verified backend/Android foundations, but the latest SMC/replay sequence requires fresh CI confirmation before calling the stage fully verified. API/client integration remains to be assessed against the complete product flow.

## Stage 3 checklist

- [x] Replay clock
- [x] Historical market state
- [x] Deterministic event ordering
- [x] Timeframe replay
- [x] Look-ahead protection
- [x] Play/pause/reset/step controls
- [x] Replay speed controls
- [x] Deterministic replay statistics foundation
- [x] Unit coverage
- [x] Historical repository loading boundary
- [x] Existing SMC integration boundary
- [ ] Runtime/CI verification of latest Stage 3 implementation
- [ ] Full SMC/strategy replay execution lifecycle
- [ ] Replay trade execution integration

## Stage 4 checklist

- [x] Event-driven candle loop foundation
- [x] Strategy interface/protocol
- [x] Deterministic market-order validation
- [x] Current-candle stop/target handling
- [x] Fees/slippage
- [x] Basic P&L metrics
- [x] Equity curve and max drawdown foundation
- [x] Unit coverage
- [ ] Multi-candle position/order lifecycle
- [ ] Explicit trade ledger/order events
- [ ] Position sizing/risk integration
- [ ] Out-of-sample split support
- [ ] Full runtime/CI verification
- [ ] Backtest API/report integration

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

Live/autonomous trading must not be enabled until replay, backtesting, paper trading, risk controls, broker reconciliation, failure handling, and explicit user activation are implemented and tested.

AI remains subordinate to deterministic strategy, validation, risk, and execution gates.

## Runtime verification

GitHub Actions is the available repository verification path. Local Codespace/runtime execution is unavailable from this environment because outbound GitHub access is blocked by network DNS. No local test command is claimed as executed here.

The latest backtest commit `92fcae2` currently has no reported commit status/workflow result available through the connected GitHub API, so its tests are `UNVERIFIED`.

## Next task

Complete the Stage 4 multi-candle position/order lifecycle and explicit trade ledger while preserving the current deterministic strategy boundary. Then add out-of-sample support and API/report integration, run/verify CI, and continue toward Stage 5 only after Stage 4 is genuinely verified.
