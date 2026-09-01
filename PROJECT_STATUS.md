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

## In progress

- [ ] Verify official Upstox SDK protobuf import/version in CI
- [ ] Verify complete backend test suite on current `main` after the timeframe API fix
- [ ] Verify live provider startup path without external credentials
- [ ] Complete official Gradle wrapper files and validate `./gradlew assembleDebug`
- [ ] Verify Android CI build passes on GitHub Actions after the latest commit
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
- [ ] SDK dependency/version CI verification
- [ ] Full backend CI verification
- [ ] Android CI execution verification
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

GitHub Actions run `33497106611` for commit `a97581064dceb19d251797a0c6a30485a055a736` confirmed that the official Upstox protobuf import step passed, but the backend non-integration suite failed with 51 passed, 1 failed, and 1 deselected. The failure was `tests/test_markets_api.py::test_supported_timeframes`: adding the required internal `Timeframe.TICK` enum caused the public `/api/v1/markets/timeframes` endpoint to expose `tick`. This was corrected by filtering `Timeframe.TICK` from the public candle-timeframe response.

## Current verification run

Commit `79792fa7f9e1e65417e9ec44cb34607a9b7e8870` on `main` contains the API fix. GitHub Actions run `33497328952` is currently in progress; Android is building and backend verification has not yet been reported for this commit. Therefore the fix is currently `UNVERIFIED` until the runtime result completes.

## Next task

Verify GitHub Actions run `33497328952`. Fix only confirmed failures. If backend and Android verification pass, perform the remaining Stage 1 integration audit and then proceed to the next dependency only when Stage 1 evidence supports it.
