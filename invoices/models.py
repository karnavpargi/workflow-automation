"""Invoice models."""

from decimal import Decimal

from django.db import models


class Invoice(models.Model):
    """A tenant invoice for a client.

    Attributes:
        tenant: Owning tenant.
        client: Target client.
        number: Unique invoice number per tenant.
        status: draft | issued | paid | void.
        due_date: Payment due date.
        total: Total amount, auto-computed from line items on save.
        vendor_id: Invoice Ninja id after push.
        pdf_path: MinIO path of generated PDF.
    """

    class Status(models.TextChoices):
        """Invoice lifecycle."""

        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="invoices"
    )
    client = models.ForeignKey(
        "onboarding.Client", on_delete=models.PROTECT, related_name="invoices"
    )
    number = models.CharField(max_length=40)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    due_date = models.DateField()
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vendor_id = models.CharField(max_length=100, blank=True, default="")
    pdf_path = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "number"], name="uniq_tenant_invoice_number"
            ),
        ]

    def save(self, *args, **kwargs):
        """Recompute ``total`` from line items on every save after creation.

        LineItems FK the Invoice, so the Invoice must be saved before any
        line can be added. Once ``self.pk`` is set, we can sum the lines
        and keep ``total`` consistent.
        """
        if self.pk:
            self.total = sum(
                (line.quantity * line.unit_price for line in self.lines.all()),
                start=Decimal("0.00"),
            )
        super().save(*args, **kwargs)


class LineItem(models.Model):
    """One line on an invoice."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)


class RecurringSchedule(models.Model):
    """Schedule that generates invoices on a cadence.

    Attributes:
        tenant: Owning tenant.
        client: Target client.
        template_lines: JSON list of line dicts.
        cadence: monthly | weekly.
        next_run: Next date to issue; defaults to today on create.
        is_active: Whether schedule is live.
    """

    class Cadence(models.TextChoices):
        """Supported cadences."""

        MONTHLY = "monthly", "Monthly"
        WEEKLY = "weekly", "Weekly"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="recurring_schedules"
    )
    client = models.ForeignKey(
        "onboarding.Client",
        on_delete=models.PROTECT,
        related_name="recurring_schedules",
    )
    template_lines = models.JSONField(default=list)
    cadence = models.CharField(max_length=10, choices=Cadence.choices)
    next_run = models.DateField()
    is_active = models.BooleanField(default=True)
    consecutive_failures = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        """Default ``next_run`` to today if not set on create."""
        from django.utils import timezone

        if not self.next_run:
            self.next_run = timezone.now().date()
        super().save(*args, **kwargs)
