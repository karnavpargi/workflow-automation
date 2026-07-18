"""Onboarding models."""

from django.db import models


class Client(models.Model):
    """A client of a tenant (agency customer).

    Attributes:
        tenant: Owning tenant.
        name: Client display name.
        email: Primary contact email.
        created_at: UTC timestamp.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="clients"
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)


class OnboardingTemplate(models.Model):
    """Ordered steps to run for a new client of a tenant.

    Attributes:
        tenant: Owning tenant.
        name: Template name.
        is_default: Whether this is the default template.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="onboarding_templates",
    )
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(is_default=True),
                name="uniq_default_template_per_tenant",
            ),
        ]


class OnboardingStep(models.Model):
    """One step in an onboarding template.

    Attributes:
        template: Parent template.
        kind: welcome_email | doc_request | setup_task.
        order: Sort order.
        config: JSON config for the step.
        delay_seconds: Delay before running after start.
    """

    class Kind(models.TextChoices):
        """Step kinds."""

        WELCOME_EMAIL = "welcome_email", "Welcome email"
        DOC_REQUEST = "doc_request", "Document request"
        SETUP_TASK = "setup_task", "Setup task"

    template = models.ForeignKey(
        OnboardingTemplate, on_delete=models.CASCADE, related_name="steps"
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    order = models.PositiveIntegerField(default=0)
    config = models.JSONField(default=dict)
    delay_seconds = models.PositiveIntegerField(default=0)


class OnboardingRun(models.Model):
    """One execution of a template for a client.

    Attributes:
        tenant: Owning tenant.
        client: Target client.
        template: Template used.
        status: pending | running | done | failed.
    """

    class Status(models.TextChoices):
        """Run lifecycle."""

        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="runs")
    template = models.ForeignKey(OnboardingTemplate, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
