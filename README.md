# AI Trading Platform

Android-first, multi-market AI trading platform based on the project blueprint.

## Development philosophy

Analyze → Replay → Backtest → Paper Trade → Controlled Live Trade

The AI is not the final execution authority. Deterministic strategy validation, risk controls, and broker execution controls must approve live orders.

## Project status

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) before starting work. This file is maintained as the implementation checklist and must be updated after meaningful changes.

## Planned stack

- Android: Kotlin, Jetpack Compose, MVVM, Clean Architecture
- Backend: Python, FastAPI, Pydantic
- Data: PostgreSQL, Redis
- Quant: NumPy, Pandas, Polars, SciPy
- Infrastructure: Docker, Nginx, Prometheus, Grafana

## Security

Never commit real API keys, broker credentials, JWT secrets, certificates, or production environment files. Use `.env.example` as the configuration template.

## Current stage

Stage 0 — Architecture / repository foundation.
