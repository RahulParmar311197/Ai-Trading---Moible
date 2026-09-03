# Autonomous Decision Pipeline

The Stage 10 decision pipeline converts a validated strategy candidate into a **broker-neutral execution intent**. It does not submit orders, hold broker credentials, activate live execution, or bypass `ControlledBrokerExecution`.

## Deterministic flow

```text
Strategy / AI candidate
        ↓
Candidate validation
        ↓
Fresh authoritative session + risk state
        ↓
Projected portfolio exposure / correlation check
        ↓
Deterministic execution risk gate
        ↓
Broker-neutral ExecutionIntent
        ↓
ControlledBrokerExecution (separate boundary)
```

AI-generated candidates are explicitly tagged as advisory provenance. The pipeline treats them as untrusted structured inputs and still requires deterministic validation, fresh state, portfolio risk approval, and the existing execution gate.

## Fail-closed rules

- stale decision state is rejected;
- missing/invalid candidate return history is rejected;
- unsatisfied strategy conditions are rejected;
- projected portfolio limits are evaluated before an intent is returned;
- deterministic order/position/daily-loss risk limits are evaluated independently;
- portfolio or execution risk rejection produces no intent;
- no broker mutation is reachable from this component.

A returned `ExecutionIntent` is **not an order authorization**. Live submission remains subject to authenticated startup, explicit activation, emergency/kill-switch state, broker-state refresh, durable idempotency, broker confirmation, post-fill synchronization, and audit controls in `ControlledBrokerExecution`.
