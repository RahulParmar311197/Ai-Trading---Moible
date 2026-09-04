from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import brokers as brokers_api
from app.api.auth import current_user
from app.auth import AuthUser
from app.brokers.account_repository import BrokerAccountRepository
from app.main import app


class FakeRepository:
    def __init__(self):
        self.accounts = []

    def list_for_user(self, user_id):
        return tuple(account for account in self.accounts if account.user_id == user_id)

    def create(self, user_id, provider, environment, external_account_id, credential_ref=None):
        account = BrokerAccountRepository._map({
            "id": str(uuid4()),
            "user_id": str(user_id),
            "provider": provider.strip().upper(),
            "environment": environment.strip().upper(),
            "external_account_id": external_account_id.strip(),
            "credential_ref": credential_ref,
            "enabled": False,
        })
        self.accounts.append(account)
        return account


def test_broker_accounts_require_authentication():
    with TestClient(app) as client:
        assert client.get("/api/v1/brokers/accounts").status_code == 401


def test_broker_account_api_is_user_scoped_and_never_returns_credential_ref(monkeypatch):
    repository = FakeRepository()
    user = AuthUser(uuid4(), "trader@example.com", "Trader", "ACTIVE")
    monkeypatch.setattr(brokers_api, "get_broker_account_repository", lambda: repository)
    app.dependency_overrides[current_user] = lambda: user
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/brokers/accounts",
                json={
                    "provider": "upstox",
                    "environment": "sandbox",
                    "external_account_id": "ACC-A",
                    "credential_ref": "opaque-ref",
                },
            )
            assert created.status_code == 201
            body = created.json()
            assert body["provider"] == "UPSTOX"
            assert body["enabled"] is False
            assert body["has_credential_ref"] is True
            assert "credential_ref" not in body

            listed = client.get("/api/v1/brokers/accounts")
            assert listed.status_code == 200
            assert len(listed.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_broker_account_enable_and_disable_are_explicit_and_user_scoped(monkeypatch):
    user_a = AuthUser(uuid4(), "a@example.com", "A", "ACTIVE")
    user_b = AuthUser(uuid4(), "b@example.com", "B", "ACTIVE")
    account = BrokerAccountRepository._map({
        "id": str(uuid4()),
        "user_id": str(user_a.id),
        "provider": "DHAN",
        "environment": "SANDBOX",
        "external_account_id": "CLIENT-A",
        "credential_ref": None,
        "enabled": False,
    })

    class Repository:
        def set_enabled(self, user_id, account_id, enabled):
            if user_id != account.user_id or account_id != account.id:
                raise KeyError("broker account not found")
            return BrokerAccountRepository._map({
                "id": str(account.id),
                "user_id": str(account.user_id),
                "provider": account.provider,
                "environment": account.environment,
                "external_account_id": account.external_account_id,
                "credential_ref": None,
                "enabled": enabled,
            })

    monkeypatch.setattr(brokers_api, "get_broker_account_repository", lambda: Repository())
    app.dependency_overrides[current_user] = lambda: user_a
    try:
        with TestClient(app) as client:
            enabled = client.post(f"/api/v1/brokers/accounts/{account.id}/enable")
            assert enabled.status_code == 200
            assert enabled.json()["enabled"] is True
            disabled = client.post(f"/api/v1/brokers/accounts/{account.id}/disable")
            assert disabled.status_code == 200
            assert disabled.json()["enabled"] is False
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[current_user] = lambda: user_b
    try:
        with TestClient(app) as client:
            assert client.post(f"/api/v1/brokers/accounts/{account.id}/enable").status_code == 404
    finally:
        app.dependency_overrides.clear()
