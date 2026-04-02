from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./bootstrap-test.db")
os.environ.setdefault("JWT_SECRET", "bootstrap-secret-key-1234")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass123")

from app.core.config import clear_settings_cache
from app.db.session import reset_database_state
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    database_path = tmp_path / "finance-dashboard-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-123456")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "AdminPass123")

    clear_settings_cache()
    reset_database_state()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    reset_database_state()
    clear_settings_cache()


def get_auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
