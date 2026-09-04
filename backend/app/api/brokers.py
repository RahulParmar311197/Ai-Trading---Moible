"""Authenticated, user-scoped broker-account metadata API."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import current_user
from app.auth import AuthUser
from app.brokers.account_repository import BrokerAccount, BrokerAccountRepository
from app.database.session import SQLAlchemyExecutor, create_database_engine

router = APIRouter(prefix="/api/v1/brokers", tags=["brokers"])


@lru_cache(maxsize=1)
def get_broker_account_repository() -> BrokerAccountRepository:
    return BrokerAccountRepository(SQLAlchemyExecutor(create_database_engine()))


class CreateBrokerAccountRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=16)
    environment: str = Field(min_length=1, max_length=16)
    external_account_id: str = Field(min_length=1, max_length=128)
    credential_ref: str | None = Field(default=None, min_length=1, max_length=512)


class BrokerAccountResponse(BaseModel):
    id: str
    provider: str
    environment: str
    external_account_id: str
    enabled: bool
    has_credential_ref: bool


def _response(account: BrokerAccount) -> BrokerAccountResponse:
    return BrokerAccountResponse(
        id=str(account.id),
        provider=account.provider,
        environment=account.environment,
        external_account_id=account.external_account_id,
        enabled=account.enabled,
        has_credential_ref=account.has_credential_ref,
    )


@router.get("/accounts", response_model=tuple[BrokerAccountResponse, ...])
def list_accounts(user: AuthUser = Depends(current_user)) -> tuple[BrokerAccountResponse, ...]:
    return tuple(_response(item) for item in get_broker_account_repository().list_for_user(user.id))


@router.post("/accounts", response_model=BrokerAccountResponse, status_code=201)
def create_account(
    request: CreateBrokerAccountRequest,
    user: AuthUser = Depends(current_user),
) -> BrokerAccountResponse:
    try:
        account = get_broker_account_repository().create(
            user.id,
            request.provider,
            request.environment,
            request.external_account_id,
            request.credential_ref,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _response(account)


@router.post("/accounts/{account_id}/enable", response_model=BrokerAccountResponse)
def enable_account(account_id: UUID, user: AuthUser = Depends(current_user)) -> BrokerAccountResponse:
    try:
        return _response(get_broker_account_repository().set_enabled(user.id, account_id, True))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="broker account not found") from exc


@router.post("/accounts/{account_id}/disable", response_model=BrokerAccountResponse)
def disable_account(account_id: UUID, user: AuthUser = Depends(current_user)) -> BrokerAccountResponse:
    try:
        return _response(get_broker_account_repository().set_enabled(user.id, account_id, False))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="broker account not found") from exc
