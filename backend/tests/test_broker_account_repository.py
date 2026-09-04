from uuid import UUID, uuid4

import pytest

from app.brokers.account_repository import BrokerAccountRepository


class FakeDb:
    def __init__(self):
        self.rows = []

    def fetch_all(self, query, params):
        return [r for r in self.rows if r["user_id"] == params["user_id"]]

    def fetch_one(self, query, params):
        return next(
            (r for r in self.rows if r["id"] == params["id"] and r["user_id"] == params["user_id"]),
            None,
        )

    def execute_returning(self, query, params):
        if "INSERT INTO" in str(query):
            if any(
                r["user_id"] == params["user_id"]
                and r["provider"] == params["provider"]
                and r["environment"] == params["environment"]
                for r in self.rows
            ):
                raise RuntimeError("duplicate unique constraint")
            if any(
                r["provider"] == params["provider"]
                and r["environment"] == params["environment"]
                and r["external_account_id"] == params["external_account_id"]
                for r in self.rows
            ):
                raise RuntimeError("duplicate unique constraint")
            row = {
                "id": params["id"],
                "user_id": params["user_id"],
                "provider": params["provider"],
                "environment": params["environment"],
                "external_account_id": params["external_account_id"],
                "credential_ref": params["credential_ref"],
                "enabled": False,
            }
            self.rows.append(row)
            return row
        for row in self.rows:
            if row["id"] == params["id"] and row["user_id"] == params["user_id"]:
                row["enabled"] = params["enabled"]
                return row
        return None


def test_broker_accounts_are_scoped_to_user_and_credentials_are_not_exposed():
    db = FakeDb()
    repository = BrokerAccountRepository(db)
    user_a, user_b = uuid4(), uuid4()

    account = repository.create(user_a, "upstox", "sandbox", "ACC-A", "secret-ref")

    assert repository.list_for_user(user_a) == (account,)
    assert repository.list_for_user(user_b) == ()
    assert account.has_credential_ref is True
    assert not hasattr(account, "credential_ref")
    assert repository.get_for_user(user_b, account.id) is None


def test_broker_account_creation_is_disabled_by_default_and_enable_is_user_scoped():
    db = FakeDb()
    repository = BrokerAccountRepository(db)
    user_a, user_b = uuid4(), uuid4()
    account = repository.create(user_a, "DHAN", "LIVE", "CLIENT-A")

    assert account.enabled is False
    with pytest.raises(KeyError):
        repository.set_enabled(user_b, account.id, True)

    enabled = repository.set_enabled(user_a, account.id, True)
    assert enabled.enabled is True


def test_broker_account_rejects_unsupported_provider_or_environment():
    repository = BrokerAccountRepository(FakeDb())
    user_id = uuid4()

    with pytest.raises(ValueError):
        repository.create(user_id, "ZERODHA", "SANDBOX", "ACC")
    with pytest.raises(ValueError):
        repository.create(user_id, "UPSTOX", "PRODUCTION", "ACC")
    with pytest.raises(ValueError):
        repository.create(user_id, "UPSTOX", "SANDBOX", "   ")
