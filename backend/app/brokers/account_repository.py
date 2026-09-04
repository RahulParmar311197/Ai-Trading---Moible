"""User-scoped persistence boundary for broker-account metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from app.database.session import SQLAlchemyExecutor


@dataclass(frozen=True, slots=True)
class BrokerAccount:
    id: UUID
    user_id: UUID
    provider: str
    environment: str
    external_account_id: str
    enabled: bool
    has_credential_ref: bool


class BrokerAccountRepository:
    """Persist broker metadata while never returning credential material."""

    def __init__(self, db: SQLAlchemyExecutor) -> None:
        self.db = db

    @staticmethod
    def _map(row: dict[str, Any]) -> BrokerAccount:
        return BrokerAccount(
            id=UUID(str(row["id"])),
            user_id=UUID(str(row["user_id"])),
            provider=str(row["provider"]),
            environment=str(row["environment"]),
            external_account_id=str(row["external_account_id"]),
            enabled=bool(row["enabled"]),
            has_credential_ref=bool(row.get("credential_ref")),
        )

    def list_for_user(self, user_id: UUID) -> tuple[BrokerAccount, ...]:
        rows = self.db.fetch_all(
            """
            SELECT id, user_id, provider, environment, external_account_id,
                   credential_ref, enabled
            FROM broker_accounts
            WHERE user_id = :user_id
            ORDER BY provider, environment
            """,
            {"user_id": str(user_id)},
        )
        return tuple(self._map(dict(row)) for row in rows)

    def get_for_user(self, user_id: UUID, account_id: UUID) -> BrokerAccount | None:
        row = self.db.fetch_one(
            """
            SELECT id, user_id, provider, environment, external_account_id,
                   credential_ref, enabled
            FROM broker_accounts
            WHERE id = :id AND user_id = :user_id
            """,
            {"id": str(account_id), "user_id": str(user_id)},
        )
        return None if row is None else self._map(dict(row))

    def create(
        self,
        user_id: UUID,
        provider: str,
        environment: str,
        external_account_id: str,
        credential_ref: str | None = None,
    ) -> BrokerAccount:
        provider = provider.strip().upper()
        environment = environment.strip().upper()
        external_account_id = external_account_id.strip()
        credential_ref = credential_ref.strip() if credential_ref is not None else None
        if provider not in {"UPSTOX", "DHAN"}:
            raise ValueError("unsupported broker provider")
        if environment not in {"SANDBOX", "LIVE"}:
            raise ValueError("unsupported broker environment")
        if not external_account_id:
            raise ValueError("external account id is required")
        if credential_ref == "":
            credential_ref = None
        account_id = uuid4()
        try:
            row = self.db.execute_returning(
                """
                INSERT INTO broker_accounts
                    (id, user_id, provider, environment, external_account_id, credential_ref)
                VALUES
                    (:id, :user_id, :provider, :environment, :external_account_id, :credential_ref)
                RETURNING id, user_id, provider, environment, external_account_id,
                          credential_ref, enabled
                """,
                {
                    "id": str(account_id),
                    "user_id": str(user_id),
                    "provider": provider,
                    "environment": environment,
                    "external_account_id": external_account_id,
                    "credential_ref": credential_ref,
                },
            )
        except Exception as exc:
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                raise ValueError("broker account already exists") from exc
            raise
        if row is None:
            raise RuntimeError("broker account was not persisted")
        return self._map(dict(row))

    def set_enabled(self, user_id: UUID, account_id: UUID, enabled: bool) -> BrokerAccount:
        row = self.db.execute_returning(
            """
            UPDATE broker_accounts
            SET enabled = :enabled, updated_at = NOW()
            WHERE id = :id AND user_id = :user_id
            RETURNING id, user_id, provider, environment, external_account_id,
                      credential_ref, enabled
            """,
            {"id": str(account_id), "user_id": str(user_id), "enabled": enabled},
        )
        if row is None:
            raise KeyError("broker account not found")
        return self._map(dict(row))
