"""Step runners for the onboarding flow.

Each ``OnboardingStep.kind`` is mapped to a handler that performs the
step's action. ``run_step`` is a Celery task that dispatches the right
handler for a given step + run pair.
"""

import logging

from celery import shared_task
from django.db.models import F

from integrations.models import IntegrationConfig
from onboarding.models import OnboardingRun, OnboardingStep
from workflows.models import TaskRecord

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_step(self, step_id: int, run_id: int) -> None:
    """Dispatch one ``OnboardingStep`` to its handler.

    Retries with exponential backoff (60s, 120s, 240s) up to
    ``max_retries`` times. After the final attempt, the exception is
    re-raised so the failure is recorded in the Celery result backend;
    the run is not transitioned to ``FAILED`` here because there is no
    step_id↔run_id mapping in storage beyond the in-flight Celery
    messages.

    Args:
        self: Bound Celery task (for retry).
        step_id: PK of the ``OnboardingStep`` to run.
        run_id: PK of the owning ``OnboardingRun``.
    """
    step = OnboardingStep.objects.select_related("template", "template__tenant").get(
        pk=step_id
    )
    OnboardingRun.objects.get(pk=run_id)
    handler = _STEP_HANDLERS.get(step.kind)
    if handler is None:
        logger.warning("Unknown step kind: %s", step.kind)
        return
    try:
        handler(step, run_id)
    except Exception as exc:  # noqa: BLE001
        if self.request.retries >= self.max_retries:
            logger.exception(
                "Step %s permanently failed after %d retries",
                step_id,
                self.request.retries,
            )
            raise
        countdown = 60 * (2**self.request.retries)
        raise self.retry(exc=exc, countdown=countdown) from exc
    _mark_step_complete(run_id)


def _welcome_email(step: OnboardingStep, run_id: int) -> None:
    """Send a welcome email to the client.

    Args:
        step: The OnboardingStep being run (unused, kept for symmetry).
        run_id: PK of the OnboardingRun.
    """
    from integrations.email.django_smtp import DjangoSmtpEmailAdapter

    run = OnboardingRun.objects.select_related("tenant", "client").get(pk=run_id)
    try:
        cfg = IntegrationConfig.objects.get(
            tenant=run.tenant,
            kind=IntegrationConfig.Kind.EMAIL,
            is_active=True,
        )
        adapter = DjangoSmtpEmailAdapter(cfg.credentials)
    except IntegrationConfig.DoesNotExist as exc:
        logger.warning(
            "No active email adapter for tenant %s: %s", run.tenant.slug, exc
        )
        return
    adapter.send(
        to=[run.client.email],
        subject=f"Welcome to {run.tenant.name}!",
        body=f"Hi {run.client.name},\n\nWelcome aboard!",
    )


def _doc_request(step: OnboardingStep, run_id: int) -> None:
    """Create a per-client document folder in Nextcloud and email the link.

    Args:
        step: The OnboardingStep being run.
        run_id: PK of the OnboardingRun.
    """
    from integrations.email.django_smtp import DjangoSmtpEmailAdapter
    from integrations.storage.nextcloud import NextcloudStorageAdapter

    run = OnboardingRun.objects.select_related("tenant", "client").get(pk=run_id)
    try:
        storage_cfg = IntegrationConfig.objects.get(
            tenant=run.tenant,
            kind=IntegrationConfig.Kind.STORAGE,
            vendor="nextcloud",
            is_active=True,
        )
        storage = NextcloudStorageAdapter(storage_cfg.credentials)
    except IntegrationConfig.DoesNotExist as exc:
        logger.warning(
            "No active Nextcloud storage for tenant %s: %s", run.tenant.slug, exc
        )
        return
    path = f"clients/{run.client.id}/docs"
    try:
        storage.put(path, b"", "application/x-directory")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Doc folder may already exist: %s", exc)
    try:
        email_cfg = IntegrationConfig.objects.get(
            tenant=run.tenant,
            kind=IntegrationConfig.Kind.EMAIL,
            is_active=True,
        )
        email = DjangoSmtpEmailAdapter(email_cfg.credentials)
    except IntegrationConfig.DoesNotExist as exc:
        logger.warning(
            "No active email adapter for tenant %s: %s", run.tenant.slug, exc
        )
        return
    email.send(
        to=[run.client.email],
        subject="Please upload your documents",
        body=f"Upload here: {storage.get_url(path)}",
    )


def _setup_task(step: OnboardingStep, run_id: int) -> None:
    """Create an internal ``TaskRecord`` for staff to set up the client.

    Args:
        step: The OnboardingStep being run.
        run_id: PK of the OnboardingRun.
    """
    run = OnboardingRun.objects.select_related("tenant").get(pk=run_id)
    TaskRecord.objects.create(
        tenant=run.tenant,
        event=None,
        task_name=f"onboarding.setup:{run.id}",
        idempotency_key=f"onboarding.setup:{run.id}:step:{step.id}",
        status=TaskRecord.Status.PENDING,
    )


_STEP_HANDLERS = {
    OnboardingStep.Kind.WELCOME_EMAIL: _welcome_email,
    OnboardingStep.Kind.DOC_REQUEST: _doc_request,
    OnboardingStep.Kind.SETUP_TASK: _setup_task,
}


def _mark_step_complete(run_id: int) -> None:
    """Increment a run's ``completed_steps`` counter and finalize the run.

    When ``completed_steps`` reaches ``total_steps`` the run's status
    transitions to ``DONE``. Uses ``F()`` for the atomic increment so
    concurrent step completions do not lose updates.

    Args:
        run_id: PK of the ``OnboardingRun`` to update.
    """
    OnboardingRun.objects.filter(pk=run_id).update(
        completed_steps=F("completed_steps") + 1
    )
    run = OnboardingRun.objects.get(pk=run_id)
    if run.total_steps > 0 and run.completed_steps >= run.total_steps:
        run.status = OnboardingRun.Status.DONE
        run.save(update_fields=["status"])
