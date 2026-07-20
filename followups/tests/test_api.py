"""Tests for the followups DRF API."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def authed_client(db):
    """Return (APIClient, user, tenant_slug) for a freshly-created tenant+admin."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    c = APIClient()
    c.force_authenticate(user=u)
    return c, u, "a"


@pytest.mark.django_db
def test_list_reminders_returns_only_current_tenant(authed_client):
    """GET /api/reminders/ scopes results to the X-Tenant-Slug tenant."""
    from datetime import timedelta

    from django.utils import timezone

    from followups.models import Reminder
    from tenants import services as tsvc
    from users.models import User

    client, user, slug = authed_client
    t = user.memberships.first().tenant
    due = timezone.now() + timedelta(days=1)
    Reminder.objects.create(tenant=t, subject="mine", due_at=due)
    # Build a second tenant + reminder; the caller's request should not see it.
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    Reminder.objects.create(tenant=tb, subject="other-tenant", due_at=due)
    r = client.get("/api/reminders/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    subjects = sorted(item["subject"] for item in r.data)
    assert subjects == ["mine"]


@pytest.mark.django_db
def test_create_reminder_via_api(authed_client):
    """POST /api/reminders/ creates a PENDING reminder in the caller's tenant."""
    client, _user, slug = authed_client
    r = client.post(
        "/api/reminders/",
        {
            "subject": "Manual ping",
            "due_at": "2026-12-31T00:00:00Z",
            "recipient_email": "x@y.io",
            "context": {"subject": "Manual ping"},
        },
        format="json",
        HTTP_X_TENANT_SLUG=slug,
    )
    assert r.status_code == 201, r.data
    assert r.data["status"] == "pending"
    assert r.data["subject"] == "Manual ping"


@pytest.mark.django_db
def test_cancel_reminder_action_marks_cancelled(authed_client):
    """POST /api/reminders/{id}/cancel/ flips status to cancelled."""
    from datetime import timedelta

    from django.utils import timezone

    from followups.models import Reminder

    client, user, slug = authed_client
    t = user.memberships.first().tenant
    rem = Reminder.objects.create(
        tenant=t,
        subject="to-cancel",
        due_at=timezone.now() + timedelta(days=1),
        recipient_email="x@y.io",
    )
    r = client.post(f"/api/reminders/{rem.id}/cancel/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200, r.data
    rem.refresh_from_db()
    assert rem.status == Reminder.Status.CANCELLED


@pytest.mark.django_db
def test_cancel_reminder_404_for_other_tenant(authed_client):
    """A reminder owned by another tenant must return 404, not 200/403."""
    from datetime import timedelta

    from django.utils import timezone

    from followups.models import Reminder
    from tenants import services as tsvc
    from users.models import User

    client, _user, slug = authed_client
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    other = Reminder.objects.create(
        tenant=tb,
        subject="other",
        due_at=timezone.now() + timedelta(days=1),
        recipient_email="b@b.io",
    )
    r = client.post(f"/api/reminders/{other.id}/cancel/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 404
