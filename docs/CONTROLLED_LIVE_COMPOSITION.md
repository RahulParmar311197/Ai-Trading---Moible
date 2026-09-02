# Controlled Live Execution Composition Boundary

## Purpose

This document records the verified application-composition boundary for Stage 9 controlled live execution. It deliberately does not invent an authoritative trading-session lifecycle or enable live trading.

## Verified repository state

- `ControlledBrokerExecution` is a safety boundary, not an application singleton.
- Construction requires an explicit idempotency store.
- Startup authenticates without enabling mutation.
- Explicit activation is required before submission.
- Broker position state is refreshed before submission and must agree with the supplied risk snapshot.
- Partial/filled confirmations require post-fill synchronization.
- The concrete post-fill synchronizer requires an explicit session ID, persisted session baseline, and explicit risk-state sink.
- The application entrypoint currently wires market-data and paper-trading services, but does not construct a controlled live executor.
- Existing Redis live-state code is market-event state/fan-out and is not treated as an authoritative durable trading-state sink.

## Required upstream contracts before runtime wiring

1. **Authoritative trading-session identity/lifecycle**
   - Must be supplied by an authoritative application/domain contract.
   - The execution layer must receive the session identity explicitly.
   - No wall-clock, exchange-day, or provider-specific session boundary is inferred by this layer.

2. **Durable live-state sink**
   - Must define the durable schema and ownership for broker-derived live account/position/risk state.
   - The sink must be explicit in application composition and failure must remain fail-closed after a fill.
   - Market-event Redis state must not be substituted for this sink.

3. **Controlled executor composition**
   - Must be instantiated only after the two contracts above are available, together with broker, risk gate, audit sink, idempotency store, and post-fill synchronizer.
   - Runtime wiring must preserve the existing explicit activation and kill-switch defaults.

## Safety decision

Until these upstream contracts exist, adding application wiring would require inventing trading semantics or persistence ownership. That is not justified by the current authoritative blueprint. Live and autonomous trading therefore remain gated.
