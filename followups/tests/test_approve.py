"""Tests for the FollowupDraftingAgent HITL approval path."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def authed_client(db):
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    c = APIClient()
    c.force_authenticate(user=u)
    return c, u, "a"


@pytest.mark.django_db
def test_approve_draft_flips_draft_to_pending(authed_client):
    """POST /api/reminders/{id}/approve/ promotes a draft to pending."""
    from datetime import timedelta

    from django.utils import timezone

    from followups.models import Reminder

    client, user, slug = authed_client
    t = user.memberships.first().tenant
    rem = Reminder.objects.create(
        tenant=t,
        subject="INV-X due",
        due_at=timezone.now() + timedelta(days=1),
        recipient_email="x@y.io",
        status=Reminder.Status.DRAFT,
        draft_text="drafted message",
    )
    r = client.post(f"/api/reminders/{rem.id}/approve/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200, r.data
    rem.refresh_from_db()
    assert rem.status == Reminder.Status.PENDING


@pytest.mark.django_db
def test_approve_draft_no_op_when_not_draft(authed_client):
    """Approving a non-draft reminder leaves the status unchanged."""
    from datetime import timedelta

    from django.utils import timezone

    from followups.models import Reminder

    client, user, slug = authed_client
    t = user.memberships.first().tenant
    rem = Reminder.objects.create(
        tenant=t,
        subject="pending",
        due_at=timezone.now() + timedelta(days=1),
        status=Reminder.Status.PENDING,
    )
    r = client.post(f"/api/reminders/{rem.id}/approve/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    rem.refresh_from_db()
    assert rem.status == Reminder.Status.PENDING
