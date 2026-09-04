from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.auth import AuthService, AuthUser
from app.database.session import SQLAlchemyExecutor, create_database_engine

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_auth_service() -> AuthService:
    return AuthService(SQLAlchemyExecutor(create_database_engine()))


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    status: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: UserResponse


def _user_response(user: AuthUser) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, name=user.name, status=user.status)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest) -> UserResponse:
    try:
        return _user_response(get_auth_service().register(request.email, request.password, request.name))
    except ValueError as exc:
        raise HTTPException(status_code=409 if "registered" in str(exc) else 422, detail=str(exc)) from exc


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    try:
        token, user, expires = get_auth_service().login(request.email, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid credentials") from exc
    return LoginResponse(access_token=token, expires_at=expires.isoformat(), user=_user_response(user))


@router.post("/logout", status_code=204)
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
    if credentials is not None and credentials.scheme.lower() == "bearer":
        get_auth_service().logout(credentials.credentials)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="authentication required")
    try:
        return get_auth_service().authenticate(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid session") from exc


@router.get("/me", response_model=UserResponse)
def me(user: AuthUser = Depends(current_user)) -> UserResponse:
    return _user_response(user)
