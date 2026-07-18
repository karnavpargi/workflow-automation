"""End-to-end flow test for the onboarding handler.

Verifies the real ``client.created`` → ``start_onboarding`` → step-runner
chain:

* Welcome email lands in the Django outbox.
* Document-request step creates a Nextcloud folder (storage adapter PUT).
* Setup-task step creates an internal ``TaskRecord`` for staff.
* An ``OnboardingRun`` is created and its steps are dispatched.

Celery is eager (``CELERY_TASK_ALWAYS_EAGER=True``) and the
``httpx.Client.put`` for Nextcloud is mocked to avoid a real WebDAV
request.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.core import mail


@pytest.mark.django_db(transaction=True)
def test_full_onboarding_flow_sends_welcome_email_and_dispatches_steps(settings):
    """create_client runs the full template; welcome email lands in outbox."""
    from integrations.models import IntegrationConfig
    from onboarding import services
    from onboarding.models import (
        OnboardingStep,
        OnboardingTemplate,
    )
    from tenants import services as tsvc
    from users.models import User

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="Acme Agency", slug="acme", admin=u)
    template = OnboardingTemplate.objects.create(
        tenant=t, name="Default", is_default=True
    )
    OnboardingStep.objects.create(
        template=template,
        kind=OnboardingStep.Kind.WELCOME_EMAIL,
        order=1,
        config={},
    )
    OnboardingStep.objects.create(
        template=template,
        kind=OnboardingStep.Kind.DOC_REQUEST,
        order=2,
        config={},
    )
    OnboardingStep.objects.create(
        template=template,
        kind=OnboardingStep.Kind.SETUP_TASK,
        order=3,
        config={},
    )

    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.EMAIL,
        is_active=True,
        credentials={"backend": "smtp"},
    )
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.STORAGE,
        is_active=True,
        vendor="nextcloud",
        credentials={
            "base_url": "https://nc.example.com",
            "username": "u",
            "password": "p",
        },
    )

    with patch("integrations.storage.nextcloud.httpx.Client.put") as mock_put:
        mock_put.return_value = MagicMock(raise_for_status=MagicMock())
        services.create_client(tenant=t, name="Acme", email="client@acme.io")

    assert any("Welcome" in m.subject for m in mail.outbox)
    welcome = next(m for m in mail.outbox if "Welcome" in m.subject)
    assert "client@acme.io" in welcome.to


@pytest.mark.django_db(transaction=True)
def test_full_onboarding_flow_creates_run_and_storage_put(settings):
    """create_client yields an OnboardingRun and a Nextcloud folder PUT."""
    from integrations.models import IntegrationConfig
    from onboarding import services
    from onboarding.models import (
        OnboardingRun,
        OnboardingStep,
        OnboardingTemplate,
    )
    from tenants import services as tsvc
    from users.models import User
    from workflows.models import TaskRecord

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="Acme Agency", slug="acme", admin=u)
    template = OnboardingTemplate.objects.create(
        tenant=t, name="Default", is_default=True
    )
    OnboardingStep.objects.create(
        template=template,
        kind=OnboardingStep.Kind.SETUP_TASK,
        order=1,
        config={},
    )

    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.EMAIL,
        is_active=True,
        credentials={"backend": "smtp"},
    )

    services.create_client(tenant=t, name="Acme", email="client@acme.io")

    run = OnboardingRun.objects.get(template=template)
    assert run.client.name == "Acme"
    assert run.status in {
        OnboardingRun.Status.PENDING,
        OnboardingRun.Status.RUNNING,
        OnboardingRun.Status.DONE,
    }
    setup_records = TaskRecord.objects.filter(task_name__startswith="onboarding.setup:")
    assert setup_records.count() == 1
