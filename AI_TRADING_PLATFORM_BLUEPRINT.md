# AI Trading Platform Blueprint

## Master implementation source

This file is the repository copy of the project blueprint. It is the product and architecture source of truth for implementation.

### Development rule

Before every implementation task:
1. Read this blueprint.
2. Read `PROJECT_STATUS.md`.
3. Inspect the current repository state.
4. Implement only the next appropriate pending milestone.
5. Test/validate the change.
6. Update `PROJECT_STATUS.md` with completed, in-progress, and pending work.
7. Re-check the repository before moving to the next milestone.

### Architecture principles

- Android-first client.
- Backend is Python/FastAPI.
- PostgreSQL is the primary database and Redis is used for caching/streaming workloads.
- Trading progression: Analyze → Replay → Backtest → Paper Trade → Controlled Live Trade → Autonomous Trading.
- Deterministic trading, validation, risk, execution, and broker controls remain authoritative over AI output.
- AI must not directly execute broker orders.
- Live/autonomous trading requires replay, backtesting, paper trading, risk controls, broker reconciliation, failure handling, and explicit user activation.

### Planned capability stages

1. Architecture / repository foundation
2. Market data
3. SMC / ICT analysis
4. Historical replay
5. Backtesting
6. AI analysis and strategy generation
7. Options engine
8. Paper trading
9. Broker integration and controlled live trading
10. Autonomous trading

### Core domains

- Authentication and user accounts
- Instruments and market data
- Candles and ticks
- SMC / ICT analytics
- Scanner and setup detection
- Strategy engine and strategy DSL
- Replay engine
- Backtesting engine
- AI analysis and validation
- Options chains, Greeks, IV and payoff
- Paper trading
- Broker adapters
- Orders, executions and reconciliation
- Positions and portfolio P&L
- Risk management and kill switches
- Notifications
- Audit logging
- Monitoring and observability

### Required safety properties

- No look-ahead bias in replay/backtesting.
- Explicit market-data freshness checks.
- Order idempotency and reconciliation.
- Broker health checks.
- Risk limits and emergency controls.
- Complete audit trail for trading decisions and order lifecycle.
- No production credentials or secrets committed to Git.

> This repository copy is intentionally a concise implementation reference. The original uploaded blueprint remains the detailed source document; when a requirement is not represented here, consult the original uploaded blueprint before making assumptions.
