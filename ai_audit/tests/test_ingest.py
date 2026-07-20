"""Tests for the LlmCall audit model + service + ingest endpoint."""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_record_llm_call_creates_row():
    """``record_llm_call`` persists the fields on the model."""
    from ai_audit.services import record_llm_call
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    call = record_llm_call(
        tenant=t,
        agent_name="email_parse",
        input_hash="a" * 64,
        output_hash="b" * 64,
        guard_decisions=["pii_redacted"],
        user_id=u.id,
        latency_ms=120,
    )
    assert call.id is not None
    assert call.tenant_id == t.id
    assert call.agent_name == "email_parse"
    assert call.guard_decisions == ["pii_redacted"]


@pytest.mark.django_db
def test_ingest_endpoint_rejects_missing_token():
    """Without a service token the endpoint returns 401."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    client = APIClient()
    r = client.post(
        "/api/ai-audit/llm-calls/",
        {"tenant_slug": "a", "agent_name": "x", "input_text": "i", "output_text": "o"},
        format="json",
    )
    assert r.status_code == 401


@pytest.mark.django_db
def test_ingest_endpoint_accepts_valid_token(settings, monkeypatch):
    """With the right token, the endpoint records a row."""
    from ai_audit.models import LlmCall
    from tenants import services as tsvc
    from users.models import User

    monkeypatch.setenv("AI_AUDIT_SERVICE_TOKEN", "tok-1")
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    client = APIClient()
    r = client.post(
        "/api/ai-audit/llm-calls/",
        {
            "tenant_slug": "a",
            "agent_name": "email_parse",
            "input_text": "hello",
            "output_text": "world",
            "latency_ms": 42,
        },
        format="json",
        HTTP_X_AI_SERVICE_TOKEN="tok-1",
    )
    assert r.status_code == 201, r.data
    assert LlmCall.objects.filter(agent_name="email_parse").count() == 1


@pytest.mark.django_db
def test_ingest_endpoint_rejects_unknown_tenant(monkeypatch):
    """An unknown tenant_slug returns 404."""
    monkeypatch.setenv("AI_AUDIT_SERVICE_TOKEN", "tok-1")
    client = APIClient()
    r = client.post(
        "/api/ai-audit/llm-calls/",
        {
            "tenant_slug": "no-such-tenant",
            "agent_name": "x",
            "input_text": "i",
            "output_text": "o",
        },
        format="json",
        HTTP_X_AI_SERVICE_TOKEN="tok-1",
    )
    assert r.status_code == 404
