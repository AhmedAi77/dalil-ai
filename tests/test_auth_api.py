from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import AuthRepository, Database
from app.main import app
from app.services.auth_service import AuthService, get_auth_service


def test_cookie_authentication_flow_and_route_protection(tmp_path: Path) -> None:
    settings = Settings(database_path=tmp_path / "api-auth.db")
    database = Database(settings.database_path)
    database.initialize()
    auth = AuthService(AuthRepository(database), session_days=7)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_auth_service] = lambda: auth

    try:
        with TestClient(app) as client:
            protected = client.get("/documents")
            assert protected.status_code == 401

            registered = client.post(
                "/auth/register",
                json={
                    "name": "Portfolio Owner",
                    "email": "owner@example.com",
                    "password": "strong-password",
                },
            )
            assert registered.status_code == 201
            assert registered.json()["email"] == "owner@example.com"
            cookie = registered.headers["set-cookie"]
            assert "HttpOnly" in cookie
            assert "SameSite=strict" in cookie

            assert client.get("/auth/me").status_code == 200
            assert client.post("/auth/logout").json() == {"logged_out": True}
            assert client.get("/auth/me").status_code == 401
    finally:
        app.dependency_overrides.clear()
