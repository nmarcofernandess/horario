"""Test básico de health da API."""
from fastapi.testclient import TestClient

from apps.backend.main import app

client = TestClient(app)


def test_health():
    """GET /health retorna ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
