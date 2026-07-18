# ruff: noqa: I001, F401
"""Tests for Client, OnboardingTemplate, OnboardingStep, and OnboardingRun models."""

import pytest
from onboarding.models import (
    Client,
    OnboardingRun,
    OnboardingStep,
    OnboardingTemplate,
)


@pytest.mark.django_db
def test_create_client():
    """A client is created with name and email."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")
    assert c.id and c.name == "Acme" and c.email == "a@acme.io"
    assert t.clients.filter(pk=c.id).exists()


@pytest.mark.django_db
def test_default_template_is_unique_per_tenant():
    """A tenant can have at most one default OnboardingTemplate."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    OnboardingTemplate.objects.create(tenant=t, name="Default", is_default=True)
    with pytest.raises(Exception):  # noqa: B017
        OnboardingTemplate.objects.create(tenant=t, name="Second", is_default=True)


@pytest.mark.django_db
def test_run_status_defaults_to_pending():
    """A new OnboardingRun starts as pending."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")
    template = OnboardingTemplate.objects.create(tenant=t, name="Default")
    run = OnboardingRun.objects.create(tenant=t, client=c, template=template)
    assert run.status == OnboardingRun.Status.PENDING
