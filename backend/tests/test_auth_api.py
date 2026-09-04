from decimal import Decimal

from fastapi.testclient import TestClient

from app.api import paper as paper_api
from app.api.auth import get_auth_service
from app.auth import AuthService
from app.main import app
from app.paper.engine import PaperBroker


class FakeDb:
    def __init__(self):
        self.users = {}
        self.sessions = {}

    def fetch_one(self, query, params):
        text = str(query)
        if "FROM users" in text:
            if "WHERE email" in text:
                return next((u for u in self.users.values() if u["email"] == params["email"]), None)
        if "FROM auth_sessions" in text:
            session = self.sessions.get(params["token_hash"])
            if session and session["expires_at"] > params["now"] and session["revoked_at"] is None:
                return self.users[session["user_id"]]
        return None

    def execute(self, query, params):
        text = str(query)
        if "INSERT INTO users" in text:
            self.users[params["id"]] = dict(params)
        elif "INSERT INTO auth_sessions" in text:
            self.sessions[params["token_hash"]] = dict(params)
        elif "UPDATE auth_sessions SET last_seen_at" in text:
            pass
        elif "UPDATE auth_sessions SET revoked_at" in text:
            self.sessions[params["token_hash"]]["revoked_at"] = params["now"]
        return None


def test_auth_register_login_me_and_paper_requires_auth(monkeypatch):
    db = FakeDb()
    auth = AuthService(db)
    broker = PaperBroker(starting_balance=Decimal("1000"))
    monkeypatch.setattr(paper_api, "get_paper_broker", lambda user_id: broker)
    app.dependency_overrides[get_auth_service] = lambda: auth
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/paper/account").status_code == 401
            registered = client.post(
                "/api/v1/auth/register",
                json={"email": "trader@example.com", "password": "StrongPassword123!", "name": "Trader"},
            )
            assert registered.status_code == 201
            logged_in = client.post(
                "/api/v1/auth/login",
                json={"email": "trader@example.com", "password": "StrongPassword123!"},
            )
            assert logged_in.status_code == 200
            token = logged_in.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
            assert client.get("/api/v1/paper/account", headers=headers).status_code == 200
    finally:
        app.dependency_overrides.pop(get_auth_service, None)
