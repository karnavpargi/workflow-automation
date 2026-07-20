"""Follow-up reminder models.

A :class:`FollowupRule` describes a reusable reminder pattern (channel,
offset relative to due date, message template). A :class:`Reminder` is a
concrete scheduled instance pointing at a recipient and a fire time.
``FollowupRule`` deletion uses ``SET_NULL`` so a fired/missed reminder
record is preserved even if the originating rule is later removed.

The :class:`SuccessfulFollowup` model captures the LLM-drafted
message text of reminders that were approved and sent; the AI service
retrieves the most-recent N of these as positive RAG examples when
drafting a new follow-up.
"""

from django.db import models


class FollowupRule(models.Model):
    """Reusable rule describing when/how to remind.

    Attributes:
        tenant: Owning tenant.
        name: Human-readable rule name.
        channel: Delivery channel (``email`` | ``internal_task`` | ``both``).
        offset_days: Days relative to the due date (negative = before).
        template: Message body with ``{placeholders}`` filled from
            :attr:`Reminder.context`.
    """

    class Channel(models.TextChoices):
        """Delivery channels supported by the reminder engine."""

        EMAIL = "email", "Email"
        INTERNAL = "internal_task", "Internal task"
        BOTH = "both", "Both"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="followup_rules"
    )
    name = models.CharField(max_length=100)
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.EMAIL
    )
    offset_days = models.IntegerField(default=-7)
    template = models.TextField(default="Reminder: {subject} is due on {due_date}.")


class Reminder(models.Model):
    """A concrete reminder instance scheduled to fire at ``due_at``.

    Attributes:
        tenant: Owning tenant.
        rule: Optional rule that produced this reminder (``SET_NULL`` on
            rule delete so the historical reminder row survives).
        subject: Short subject line.
        due_at: When to fire. Indexed for the Beat scan.
        recipient_email: Email target (used when channel includes email).
        status: ``draft`` | ``pending`` | ``sent`` | ``cancelled``.
        context: JSON dict used to fill the rule template.
        draft_text: LLM-proposed message text awaiting HITL review.
        created_at: Row creation timestamp.
    """

    class Status(models.TextChoices):
        """Reminder lifecycle.

        ``DRAFT`` is set by the AI service when an LLM has proposed
        message text that still needs human-in-the-loop review. Admins
        approve the draft (flip to ``PENDING``) or reject (flip to
        ``CANCELLED``).
        """

        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        CANCELLED = "cancelled", "Cancelled"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="reminders"
    )
    rule = models.ForeignKey(
        FollowupRule,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reminders",
    )
    subject = models.CharField(max_length=200)
    due_at = models.DateTimeField(db_index=True)
    recipient_email = models.EmailField(blank=True, default="")
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    context = models.JSONField(default=dict)
    draft_text = models.TextField(
        blank=True,
        default="",
        help_text="LLM-proposed message text awaiting HITL review.",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class SuccessfulFollowup(models.Model):
    """An approved-and-sent follow-up; a positive RAG example.

    When a ``Reminder`` is approved (DRAFT -> PENDING) and eventually
    sent, its ``draft_text`` is captured here for retrieval. The AI
    service's ``FollowupDraftingAgent`` reads the most-recent N rows
    for the tenant and includes them in the LLM prompt as examples
    of "what worked before".

    Attributes:
        tenant: Owning tenant.
        reminder: The originating :class:`Reminder` (nullable so
            successful followups survive if the reminder is purged).
        draft_text: The message that was sent.
        sent_at: Timestamp the message was actually sent.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="successful_followups"
    )
    reminder = models.ForeignKey(
        Reminder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="successful_followups",
    )
    draft_text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Index on (tenant, -sent_at) for the "recent N" query."""

        indexes = [models.Index(fields=["tenant", "-sent_at"])]
