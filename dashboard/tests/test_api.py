"""Tests for the dashboard summary endpoint."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def authed_client(db):
    """A signed-in admin user in a fresh tenant."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    c = APIClient()
    c.force_authenticate(user=u)
    return c, u, "a"


@pytest.mark.django_db
def test_dashboard_returns_zero_counts_for_empty_tenant(authed_client):
    """A fresh tenant sees all-zero counts."""
    client, _, slug = authed_client
    r = client.get("/api/dashboard/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    assert r.data == {
        "clients": 0,
        "open_invoices": 0,
        "due_followups": 0,
    }


@pytest.mark.django_db
def test_dashboard_counts_clients(authed_client):
    """Two clients → ``clients: 2``."""
    from onboarding.models import Client

    client, user, slug = authed_client
    t = user.memberships.first().tenant
    Client.objects.create(tenant=t, name="A Co", email="a@a.io")
    Client.objects.create(tenant=t, name="B Co", email="b@b.io")
    r = client.get("/api/dashboard/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    assert r.data["clients"] == 2


@pytest.mark.django_db
def test_dashboard_counts_only_issued_invoices(authed_client):
    """Draft + void invoices are excluded from the open count."""
    from datetime import date

    from invoices.models import Invoice
    from onboarding.models import Client

    client, user, slug = authed_client
    t = user.memberships.first().tenant
    c = Client.objects.create(tenant=t, name="A Co", email="a@a.io")
    Invoice.objects.create(
        tenant=t, client=c, number="D-1", due_date=date(2026, 12, 31), status="draft"
    )
    Invoice.objects.create(
        tenant=t, client=c, number="I-1", due_date=date(2026, 12, 31), status="issued"
    )
    Invoice.objects.create(
        tenant=t, client=c, number="V-1", due_date=date(2026, 12, 31), status="void"
    )
    r = client.get("/api/dashboard/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    assert r.data["open_invoices"] == 1


@pytest.mark.django_db
def test_dashboard_counts_pending_followups(authed_client):
    """Only PENDING reminders count toward ``due_followups``."""
    from datetime import timedelta

    from django.utils import timezone

    from followups.models import Reminder

    client, user, slug = authed_client
    t = user.memberships.first().tenant
    Reminder.objects.create(
        tenant=t,
        subject="pending",
        due_at=timezone.now() + timedelta(days=1),
        status=Reminder.Status.PENDING,
    )
    Reminder.objects.create(
        tenant=t,
        subject="sent",
        due_at=timezone.now() + timedelta(days=1),
        status=Reminder.Status.SENT,
    )
    r = client.get("/api/dashboard/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    assert r.data["due_followups"] == 1


@pytest.mark.django_db
def test_dashboard_isolates_per_tenant(authed_client):
    """A second tenant's clients are not counted in the first tenant's view."""
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    client, user, slug = authed_client
    t1 = user.memberships.first().tenant
    Client.objects.create(tenant=t1, name="A Co", email="a@a.io")

    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    t2 = tsvc.create_tenant(name="B", slug="b", admin=ub)
    Client.objects.create(tenant=t2, name="B Co", email="b@b.io")
    Client.objects.create(tenant=t2, name="C Co", email="c@c.io")

    r = client.get("/api/dashboard/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    assert r.data["clients"] == 1
