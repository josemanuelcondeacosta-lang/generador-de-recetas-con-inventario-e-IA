from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient

from app.database import make_engine


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-" * 3)
    with TemporaryDirectory() as folder:
        url = f"sqlite:///{Path(folder, 'test.sqlite3').as_posix()}"
        monkeypatch.setenv("DATABASE_URL", url)
        from app import main

        engine = make_engine(url)
        monkeypatch.setattr(main, "engine", engine)
        try:
            with TestClient(main.app) as client:
                yield client
        finally:
            engine.dispose()


@pytest.fixture
def account(client):
    def create(email="estudiante@example.com"):
        response = client.post("/api/auth/register", json={
            "email": email, "password": "contraseña de prueba",
        })
        assert response.status_code == 201
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    return create
