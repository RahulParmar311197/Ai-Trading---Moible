# Architecture Notes

The platform is Android-first with a Python/FastAPI backend. The intended progression is:

Analyze → Replay → Backtest → Paper Trade → Controlled Live Trade.

The Android client should remain presentation-focused. Deterministic trading, validation, risk, execution, and broker integration belong behind backend/domain interfaces.

This document will be expanded as each architecture stage is implemented.
