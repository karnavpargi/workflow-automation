"""Verify the optional /metrics endpoint is wired up.

``prometheus-fastapi-instrumentator`` is part of the free ``[ops]``
extra. When it's installed, the AI service exposes ``/metrics`` in
the Prometheus text format.
"""


def test_metrics_route_is_registered_when_dep_present():
    """``/metrics`` is in the app's route table after the instrumentator runs."""
    from ai_service.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/metrics" in paths


def test_metrics_endpoint_returns_prometheus_text_format():
    """GET /metrics returns 200 with the standard Prometheus content type."""
    from fastapi.testclient import TestClient

    from ai_service.main import app

    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    # The default Prometheus exposition format emits HELP lines.
    body = r.text
    assert "HELP" in body or "TYPE" in body
