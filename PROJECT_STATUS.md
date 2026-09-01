# AI Trading Platform — Project Status

Last updated: 2026-09-01

## Working rule

Before every implementation task, check this file, `AI_TRADING_PLATFORM_BLUEPRINT_FULL.md`, and the current `main` repository state. Work directly on `main` only. Update this file after each completed milestone or meaningful change.

## Current stage

**Stage 1 — Market data**

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

## In progress

- [ ] Verify live provider startup path without external credentials
- [ ] Complete official Gradle wrapper files and validate `./gradlew assembleDebug`
- [ ] Complete Stage 1 final integration verification

## Stage 1 checklist

- [x] Canonical market-data models
- [x] Provider-neutral normalization
- [x] Instrument persistence
- [x] Candle persistence
- [x] Tick persistence
- [x] Provider adapter interface
- [x] REST market-data API
- [x] REST persistence wiring
- [x] WebSocket market stream
- [x] Redis live-state boundary
- [x] Redis event publisher
- [x] Redis → WebSocket wiring
- [x] Provider → publisher bridge
- [x] Freshness/quality validation
- [x] Provider selection boundary
- [x] Upstox historical adapter
- [x] Upstox live transport boundary
- [x] Upstox protobuf decoder boundary
- [x] Upstox SDK decoder adapter
- [x] Upstox live normalization
- [x] Upstox feed-field extraction
- [x] Application startup provider wiring
- [x] Redis publisher startup wiring
- [x] Provider startup integration test
- [x] Provider validation/publisher integration coverage
- [x] Timeframe aggregation
- [x] Android CI build job
- [x] CI Python import path corrected
- [x] Internal tick event timeframe support
- [x] Public candle timeframe API excludes tick events
- [x] SDK dependency/version CI verification
- [x] Full backend CI verification
- [x] Android CI execution verification
- [ ] Stage 1 final integration verification

## Later stages

### Stage 2 — SMC/ICT
- [ ] Swing detection
- [ ] Market structure
- [ ] BOS
- [ ] MSS/CHoCH
- [ ] Liquidity
- [ ] FVG
- [ ] Order blocks
- [ ] Premium/discount
- [ ] ICT session features

### Stage 3 — Replay
- [ ] Replay clock
- [ ] Historical market state
- [ ] Replay execution simulator
- [ ] Look-ahead protection
- [ ] Replay statistics

### Stage 4 — Backtesting
- [ ] Event loop
- [ ] Strategy interface
- [ ] Execution simulator
- [ ] Fees/slippage
- [ ] Performance metrics
- [ ] Equity/drawdown reporting
- [ ] Out-of-sample support

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

## Last confirmed CI result

GitHub Actions run `33497383708` for the current market-data verification work completed successfully. Both jobs passed: `backend-tests` completed the official Upstox protobuf import check, non-integration pytest suite, and integration pytest suite successfully; `android-build` completed `assembleDebug` successfully. This confirms the timeframe API fix on `main` is no longer failing in CI.

The remaining Stage 1 verification gap is the official Gradle wrapper artifact/path and final end-to-end integration audit. The repository currently has `android/gradlew` as a placeholder that delegates to an installed `gradle` command, so the official wrapper requirement remains unverified and must not be marked complete without generating/validating it through real Gradle tooling.

## Next task

Complete the Stage 1 final integration audit and, where the repository/runtime permits, replace the Android wrapper placeholder with an official generated Gradle wrapper. Do not fabricate `gradle-wrapper.jar`. After Stage 1 is genuinely verified, begin Stage 2 SMC/ICT using the existing strategy architecture and search-before-create rule.
