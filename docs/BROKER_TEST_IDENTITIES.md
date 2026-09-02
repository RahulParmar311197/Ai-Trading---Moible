# Broker Test Identity Policy

## Purpose

Automated tests must never require a user's real Upstox or Dhan client ID. Broker identifiers used by unit, integration, and CI tests are deterministic synthetic values only.

## Test identifiers

- Generic temporary/API identity: `TEST_TEMP_CLIENT_ID`
- Upstox client ID fixture: `TEST_UPSTOX_CLIENT_ID`
- Dhan client ID fixture: `TEST_DHAN_CLIENT_ID`

These values are test identifiers, not broker credentials and must never be presented as production configuration.

## UI configuration boundary

The application may collect the real Upstox or Dhan client ID manually through the broker configuration UI when a user intentionally configures an external broker. The configured value must remain outside source control and outside automated test fixtures.

Entering or storing a broker client ID must not activate live trading. Live mutation remains behind the existing authentication, recovery, risk, confirmation, idempotency, audit, kill-switch, and explicit activation controls.

## Test requirements

1. Tests use the synthetic identifiers above or test-local equivalents.
2. Tests must not request, log, snapshot, or commit real broker credentials/client IDs.
3. Provider adapters are tested against mocked/sandbox-safe broker responses unless an externally supplied sandbox is explicitly available.
4. A real broker runtime check is reported as unverified when no external sandbox/test credentials are available; synthetic IDs do not count as live-broker verification.
