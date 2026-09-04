"""Authenticated, read-only broker state endpoints.

These endpoints intentionally use the broker-account factory. They never submit or
cancel orders, and unavailable credentials/provider failures remain fail-closed.
"""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import current_user
from app.auth import AuthUser
from app.brokers.account_repository import BrokerAccountRepository
from app.brokers.credential_provider import CredentialProvider, UnconfiguredCredentialProvider, CredentialUnavailable
from app.brokers.factory import BrokerAccountFactory, BrokerUnavailable
from app.brokers.base import Account, BrokerOrder, BrokerPosition
from app.database.session import SQLAlchemyExecutor, create_database_engine

router = APIRouter(prefix="/api/v1/brokers/accounts", tags=["broker-state"])


@lru_cache(maxsize=1)
def get_broker_account_repository() -> BrokerAccountRepository:
    return BrokerAccountRepository(SQLAlchemyExecutor(create_database_engine()))


def get_credential_provider() -> CredentialProvider:
    return UnconfiguredCredentialProvider()


def get_broker_factory() -> BrokerAccountFactory:
    return BrokerAccountFactory(get_broker_account_repository(), get_credential_provider())


class BrokerStateResponse(BaseModel):
    account: Account
    positions: tuple[BrokerPosition, ...]
    orders: tuple[BrokerOrder, ...]


async def _state(account_id: UUID, user: AuthUser) -> BrokerStateResponse:
    try:
        broker = get_broker_factory().build(user_id=user.id, account_id=account_id)
        authentication = await broker.authenticate()
        if not authentication.authenticated:
            raise HTTPException(status_code=503, detail="broker authentication unavailable")
        return BrokerStateResponse(
            account=await broker.get_account(),
            positions=await broker.get_positions(),
            orders=await broker.get_orders(),
        )
    except HTTPException:
        raise
    except (BrokerUnavailable, CredentialUnavailable):
        raise HTTPException(status_code=503, detail="broker credentials or account are unavailable") from None
    except Exception as exc:
        raise HTTPException(status_code=502, detail="broker state unavailable") from exc


@router.get("/{account_id}/state", response_model=BrokerStateResponse)
async def broker_state(account_id: UUID, user: AuthUser = Depends(current_user)) -> BrokerStateResponse:
    return await _state(account_id, user)
