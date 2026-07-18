"""Workflow handlers for the onboarding app.

The ``client.created`` event triggers the onboarding flow:
1. Look up the tenant's default ``OnboardingTemplate``.
2. Create an ``OnboardingRun`` for the client.
3. Schedule each step via Celery with the step's ``delay_seconds``.

The step runners (``welcome_email``, ``doc_request``, ``setup_task``) live in
``onboarding.step_runners``.
"""

import logging

from django.db import transaction

from onboarding import step_runners
from onboarding.models import OnboardingRun
from workflows import registry

logger = logging.getLogger(__name__)


def start_onboarding(event):  # noqa: ANN001
    """Run the default onboarding template for a newly-created client.

    Resolves the tenant's default ``OnboardingTemplate``, creates an
    ``OnboardingRun``, and dispatches each step as a Celery task with
    the step's ``delay_seconds`` as the countdown.

    Args:
        event: The Event instance. Payload should contain ``client_id``,
            ``email``, and ``name``.

    Returns:
        The created ``OnboardingRun`` or ``None`` if the event cannot be
        processed (missing ``client_id`` or no default template).
    """
    client_id = event.payload.get("client_id")
    if not client_id:
        logger.warning("client.created event missing client_id; skipping onboarding")
        return None
    client = event.tenant.clients.get(pk=client_id)
    template = event.tenant.onboarding_templates.filter(is_default=True).first()
    if template is None:
        logger.info(
            "No default onboarding template for tenant %s; skipping",
            event.tenant.slug,
        )
        return None
    with transaction.atomic():
        run = OnboardingRun.objects.create(
            tenant=event.tenant,
            client=client,
            template=template,
        )
        for step in template.steps.all().order_by("order"):
            step_runners.run_step.apply_async(
                args=[step.id, run.id],
                countdown=step.delay_seconds,
            )
    return run


registry.register("client.created", start_onboarding)
