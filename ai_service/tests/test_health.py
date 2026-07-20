"""Health endpoint tests."""

from fastapi.testclient import TestClient

from ai_service.main import app

client = TestClient(app)


def test_healthz_returns_ok():
    """GET /healthz returns 200 with status=ok (liveness probe)."""
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readyz_reports_dependency_flags(monkeypatch):
    """GET /readyz returns status plus ollama/pgvector reachability flags."""
    monkeypatch.setattr("ai_service.llm.factory.ollama_reachable", lambda: True)
    monkeypatch.setattr("ai_service.db.pgvector_reachable", lambda: True)
    r = client.get("/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["ollama"] is True
    assert body["pgvector"] is True
