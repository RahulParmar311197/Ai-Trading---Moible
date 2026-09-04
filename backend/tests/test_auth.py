from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.auth.service import AuthService, hash_password, verify_password


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)


def test_password_policy_rejects_short_password() -> None:
    with pytest.raises(ValueError, match="12 and 256"):
        hash_password("too-short")


class FakeDb:
    def __init__(self) -> None:
        self.user = None
        self.session = None
        self.revoked = False

    def execute(self, query, params):
        if "INSERT INTO users" in query:
            self.user = {
                "id": params["id"],
                "email": params["email"],
                "password_hash": params["password_hash"],
                "name": params["name"],
                "status": "ACTIVE",
            }
        elif "INSERT INTO auth_sessions" in query:
            self.session = params
        elif "UPDATE auth_sessions SET last_seen_at" in query:
            pass
        elif "UPDATE auth_sessions SET revoked_at" in query:
            self.revoked = True

    def fetch_one(self, query, params):
        if "FROM users" in query:
            if self.user and self.user["email"] == params["email"]:
                return self.user
            return None
        if "FROM auth_sessions" in query:
            if self.session is None or self.revoked or self.session["token_hash"] != params["token_hash"]:
                return None
            return self.user
        return None


def test_auth_service_login_authenticate_and_logout() -> None:
    db = FakeDb()
    service = AuthService(db)
    user = service.register("User@Example.com", "correct horse battery staple", "Test User")
    assert user.email == "user@example.com"

    token, logged_in, expires = service.login("USER@example.com", "correct horse battery staple")
    assert logged_in == user
    assert expires > datetime.now(timezone.utc)
    assert service.authenticate(token) == user

    service.logout(token)
    with pytest.raises(ValueError, match="invalid session"):
        service.authenticate(token)


def test_auth_service_rejects_invalid_credentials() -> None:
    db = FakeDb()
    service = AuthService(db)
    service.register("user@example.com", "correct horse battery staple", "Test")
    with pytest.raises(ValueError, match="invalid credentials"):
        service.login("user@example.com", "wrong password")
