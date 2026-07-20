"""Tests for the FollowupDraftingAgent (RAG + HITL)."""

from unittest.mock import MagicMock, patch

import pytest


def _tenant() -> object:
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    return tsvc.create_tenant(name="A", slug="a", admin=u)


@pytest.mark.django_db
@pytest.mark.django_db
def test_draft_followup_returns_draft_text_and_saves_to_reminder():
    """The agent generates a draft and stores it as a draft Reminder."""
    from ai_service.agents import followup_draft
    from followups.models import Reminder

    t = _tenant()
    with (
        patch(
            "ai_service.agents.followup_draft.retrieve_examples",
            return_value=["past example"],
        ),
        patch("ai_service.llm.factory.get_chat_model") as factory,
    ):
        llm = MagicMock()
        llm.invoke.return_value.content = "Hi Acme, your invoice is due on Friday."
        factory.return_value = llm
        out = followup_draft.draft_followup(
            tenant_id=t.id,
            invoice_number="INV-1",
            due_date_iso="2026-12-31",
            recipient_email="a@acme.io",
        )

    assert "Friday" in out["draft_text"]
    rem = Reminder.objects.get(tenant=t, subject__contains="INV-1")
    assert rem.status == Reminder.Status.DRAFT
    assert rem.draft_text.startswith("Hi Acme")


@pytest.mark.django_db
def test_draft_followup_routes_reminder_to_draft_status():
    """A draft Reminder is created in DRAFT status (not PENDING)."""

    from ai_service.agents import followup_draft
    from followups.models import Reminder

    t = _tenant()
    with (
        patch(
            "ai_service.agents.followup_draft.retrieve_examples",
            return_value=[],
        ),
        patch("ai_service.llm.factory.get_chat_model") as factory,
    ):
        llm = MagicMock()
        llm.invoke.return_value.content = "Reminder text"
        factory.return_value = llm
        followup_draft.draft_followup(
            tenant_id=t.id,
            invoice_number="INV-2",
            due_date_iso="2026-12-31",
            recipient_email="x@y.io",
        )

    rem = Reminder.objects.get(tenant=t, subject__contains="INV-2")
    assert rem.status == Reminder.Status.DRAFT
    assert rem.draft_text == "Reminder text"


@pytest.mark.django_db(transaction=True)
def test_draft_followup_endpoint_returns_draft():
    """POST /agents/draft-followup returns the draft text + reminder id."""

    from fastapi.testclient import TestClient

    from ai_service.main import app

    client = TestClient(app)
    t = _tenant()

    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from ai_service.config import settings

    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "user_id": 1,
            "tenant_id": t.id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )

    with (
        patch(
            "ai_service.agents.followup_draft.retrieve_examples",
            return_value=[],
        ),
        patch("ai_service.llm.factory.get_chat_model") as factory,
    ):
        llm = MagicMock()
        llm.invoke.return_value.content = "Please pay by Friday."
        factory.return_value = llm
        r = client.post(
            "/agents/draft-followup",
            json={
                "tenant_id": t.id,
                "invoice_number": "INV-API",
                "due_date": "2026-12-31",
                "recipient_email": "a@acme.io",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 201, f"{r.status_code} {r.text}"
    body = r.json()
    assert body["draft_text"].startswith("Please pay")
    assert "reminder_id" in body
