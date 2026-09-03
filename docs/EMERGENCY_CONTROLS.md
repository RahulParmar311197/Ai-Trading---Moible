# Durable Emergency Execution Control

The controlled execution boundary has a durable emergency-stop state in PostgreSQL.

## Safety semantics

- The database migration creates a singleton control row with `active = TRUE` as the fail-closed initial state.
- Startup authenticates the broker but never activates execution. If the durable emergency state is unavailable, startup fails closed.
- Activation requires the exact existing execution confirmation phrase and is rejected while the durable emergency stop is active or unavailable.
- `trip_kill_switch()` always activates the local in-process stop first. If durable persistence fails, the local stop remains active and the operation fails closed.
- Clearing the durable emergency stop requires explicit confirmation and a non-empty operator reason. Clearing never activates execution; a separate activation step remains mandatory.
- Every emergency transition is emitted through the existing execution audit boundary.

## Operational rule

An emergency-stop state is safety state, not a UI preference. Missing, malformed, or unavailable state must be treated as active/unsafe. Production operation must therefore keep the migration applied and the PostgreSQL dependency healthy before controlled execution can be activated.

This control does not authorize orders and does not bypass deterministic risk checks, broker confirmation, idempotency, reconciliation, or post-fill synchronization.
