"""Tests for onboarding services."""

import pytest

from onboarding import services
from workflows.models import TaskRecord


@pytest.mark.django_db(transaction=True)
def test_create_client_creates_client_and_emits_event():
    """create_client writes a Client and emits a client.created event."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = services.create_client(tenant=t, name="Acme", email="a@acme.io")
    assert c.id and t.clients.filter(pk=c.id).exists()
    assert TaskRecord.objects.filter(event__name="client.created").count() == 1
