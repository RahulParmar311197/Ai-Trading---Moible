from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from uuid import UUID, uuid4

from app.database.session import SQLAlchemyExecutor

_SCRYPT_N = 16_384
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_TOKEN_BYTES = 32
_SESSION_HOURS = 12


@dataclass(frozen=True)
class AuthUser:
    id: UUID
    email: str
    name: str
    status: str


def _normalise_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 320 or parseaddr(email)[1] != email or "@" not in email:
        raise ValueError("invalid email address")
    local, domain = email.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        raise ValueError("invalid email address")
    return email


def hash_password(password: str) -> str:
    if len(password) < 12 or len(password) > 256:
        raise ValueError("password must be between 12 and 256 characters")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    encode = lambda data: base64.urlsafe_b64encode(data).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${encode(salt)}${encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = encoded.split("$", 5)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


class AuthService:
    """Durable mobile authentication using revocable opaque bearer sessions."""

    def __init__(self, db: SQLAlchemyExecutor) -> None:
        self.db = db

    def register(self, email: str, password: str, name: str) -> AuthUser:
        normalised = _normalise_email(email)
        name = name.strip()
        if not name or len(name) > 120:
            raise ValueError("name must be between 1 and 120 characters")
        user_id = uuid4()
        try:
            self.db.execute(
                """
                INSERT INTO users (id, email, password_hash, name)
                VALUES (:id, :email, :password_hash, :name)
                """,
                {"id": str(user_id), "email": normalised, "password_hash": hash_password(password), "name": name},
            )
        except Exception as exc:
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                raise ValueError("email is already registered") from exc
            raise
        return AuthUser(user_id, normalised, name, "ACTIVE")

    def login(self, email: str, password: str) -> tuple[str, AuthUser, datetime]:
        normalised = _normalise_email(email)
        row = self.db.fetch_one(
            "SELECT id, email, password_hash, name, status FROM users WHERE email = :email",
            {"email": normalised},
        )
        if row is None or not verify_password(password, str(row["password_hash"])) or row["status"] != "ACTIVE":
            raise ValueError("invalid credentials")
        user = AuthUser(UUID(str(row["id"])), str(row["email"]), str(row["name"]), str(row["status"]))
        token = secrets.token_urlsafe(_TOKEN_BYTES)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=_SESSION_HOURS)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.db.execute(
            """
            INSERT INTO auth_sessions (id, user_id, token_hash, created_at, expires_at, last_seen_at)
            VALUES (:id, :user_id, :token_hash, :created_at, :expires_at, :last_seen_at)
            """,
            {"id": str(uuid4()), "user_id": str(user.id), "token_hash": token_hash, "created_at": now, "expires_at": expires, "last_seen_at": now},
        )
        return token, user, expires

    def authenticate(self, token: str) -> AuthUser:
        if not token or len(token) > 512:
            raise ValueError("invalid session")
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        row = self.db.fetch_one(
            """
            SELECT u.id, u.email, u.name, u.status
            FROM auth_sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = :token_hash
              AND s.revoked_at IS NULL
              AND s.expires_at > NOW()
            """,
            {"token_hash": token_hash},
        )
        if row is None or row["status"] != "ACTIVE":
            raise ValueError("invalid session")
        self.db.execute("UPDATE auth_sessions SET last_seen_at = NOW() WHERE token_hash = :token_hash", {"token_hash": token_hash})
        return AuthUser(UUID(str(row["id"])), str(row["email"]), str(row["name"]), str(row["status"]))

    def logout(self, token: str) -> None:
        if not token or len(token) > 512:
            return
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.db.execute("UPDATE auth_sessions SET revoked_at = NOW() WHERE token_hash = :token_hash AND revoked_at IS NULL", {"token_hash": token_hash})
