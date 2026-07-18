"""Workflow engine models: Event and TaskRecord."""

from django.db import models


class Event(models.Model):
    """A domain event emitted by the application.

    Attributes:
        tenant: Owning tenant.
        name: Dotted event name (e.g. ``client.created``).
        payload: JSON body of the event.
        created_at: UTC timestamp.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="events"
    )
    name = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class TaskRecord(models.Model):
    """Tracks one Celery task execution for an Event.

    Attributes:
        tenant: Owning tenant.
        event: Parent Event.
        task_name: Celery task name.
        idempotency_key: Unique key preventing duplicate work.
        status: pending | running | done | failed | dead.
        attempts: Number of attempts so far.
        last_error: Last error message (if any).
    """

    class Status(models.TextChoices):
        """Lifecycle states for a task record."""

        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"
        DEAD = "dead", "Dead"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="task_records"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="task_records",
        null=True,
        blank=True,
    )
    task_name = models.CharField(max_length=200)
    idempotency_key = models.CharField(max_length=300, unique=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
