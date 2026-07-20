"""Auth tests for the agent endpoints.

The ``/agents/*`` routes must reject missing/invalid JWTs and must
use the ``tenant_id`` claim rather than a body field. This is a
multi-tenant correctness test — without JWT, anyone could pass
another tenant's id.
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from ai_service.config import settings
from ai_service.main import app


def _mint_tenant_token(tenant_id: int, *, secret: str | None = None) -> str:
    """Mint a short-lived JWT with the given tenant_id claim."""
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "user_id": 1,
            "tenant_id": tenant_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        secret or settings.jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_email_parse_rejects_missing_token(client):
    """No Authorization header returns 401/403."""
    r = client.post("/agents/email-parse", json={"raw": "hello"})
    assert r.status_code in (401, 403)


def test_email_parse_rejects_wrong_secret(client):
    """A token signed with a different secret is rejected."""
    token = _mint_tenant_token(42, secret="not-the-real-secret")
    r = client.post(
        "/agents/email-parse",
        json={"raw": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 401


@pytest.mark.django_db(transaction=True)
@pytest.mark.django_db(transaction=True)
def test_draft_followup_ignores_body_tenant_id(client):
    """The ``tenant_id`` in the body is overridden by the JWT claim.

    This is the multi-tenancy correctness contract — without it, a
    user could pass any tenant_id and the agent would write into
    another tenant's data.
    """
    from unittest.mock import MagicMock, patch

    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    real_tenant = tsvc.create_tenant(name="A", slug="a", admin=u)
    token = _mint_tenant_token(real_tenant.id)
    with (
        patch("ai_service.llm.factory.get_chat_model") as factory,
        patch("ai_service.agents.followup_draft.create_draft_reminder") as create,
    ):
        llm = MagicMock()
        llm.invoke.return_value.content = "drafted"
        factory.return_value = llm
        create.return_value = MagicMock(id=1)
        r = client.post(
            "/agents/draft-followup",
            json={
                "tenant_id": 1,  # body says 1, but JWT wins
                "invoice_number": "INV-1",
                "due_date": "2026-12-31",
                "recipient_email": "x@y.io",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201, r.text
    # The create call should have used the JWT tenant, not 1
    create.assert_called_once()
    kwargs = create.call_args.kwargs
    assert kwargs["tenant"].id == real_tenant.id
