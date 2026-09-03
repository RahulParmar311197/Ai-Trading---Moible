# GitHub Codespaces verification

Open the repository in a Codespace and wait for the post-create dependency install to finish.

## Backend

```bash
cd backend
export PYTHONPATH=.
pytest -q -m 'not integration'
```

For PostgreSQL integration tests, start the compose services and set:

```bash
docker compose -f .devcontainer/docker-compose.yml up -d
export TEST_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/ai_trading'
cd backend
pytest -q -m integration
```

## Android

From the repository root:

```bash
cd android
gradle assembleDebug
```

## Upstox sandbox

Use the existing `UPSTOX_SANDBOX_ACCESS_TOKEN` only as a Codespaces secret/environment variable. Never commit it or place it in a file tracked by git.

```bash
cd backend
export PYTHONPATH=.
pytest -q tests/test_upstox_sandbox.py -m integration
```

A sandbox failure caused by DNS, proxy, or outbound-network restrictions is an environment failure, not evidence that the broker adapter or order flow is broken. Production/live order submission must remain disabled unless explicitly and separately configured.
