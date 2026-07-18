"""Issue an invoice end-to-end."""

from django.db import transaction

from audit.services import log as audit_log
from integrations.models import IntegrationConfig
from integrations.services import get_adapter
from invoices.models import Invoice
from invoices.pdf import render_invoice_pdf


def issue_invoice(*, invoice: Invoice) -> Invoice:
    """Render PDF, store, push to billing, email client, audit, notify.

    Args:
        invoice: Draft invoice to issue.

    Returns:
        Updated Invoice (status=issued).
    """
    with transaction.atomic():
        pdf = render_invoice_pdf(invoice)
        storage = get_adapter(
            invoice.tenant, IntegrationConfig.Kind.STORAGE, vendor="minio"
        )
        path = storage.put(
            f"invoices/{invoice.tenant_id}/{invoice.number}.pdf",
            pdf,
            "application/pdf",
        )
        billing = get_adapter(invoice.tenant, IntegrationConfig.Kind.BILLING)
        vendor_id = billing.push_invoice(
            {
                "number": invoice.number,
                "client_email": invoice.client.email,
                "total": str(invoice.total),
                "due_date": invoice.due_date.isoformat(),
            }
        )
        email = get_adapter(invoice.tenant, IntegrationConfig.Kind.EMAIL)
        email.send(
            to=[invoice.client.email],
            subject=f"Invoice {invoice.number}",
            body=f"Please find invoice {invoice.number} attached.",
            attachments=[(f"{invoice.number}.pdf", pdf, "application/pdf")],
        )
        try:
            chat = get_adapter(invoice.tenant, IntegrationConfig.Kind.CHAT)
            chat.post("ops", f"Invoice issued: {invoice.number}")
        except Exception:  # noqa: BLE001
            pass  # chat is optional
        invoice.status = Invoice.Status.ISSUED
        invoice.vendor_id = vendor_id
        invoice.pdf_path = path
        invoice.save()
        audit_log(
            tenant=invoice.tenant,
            actor=None,
            event="invoice.issued",
            payload={"invoice_id": invoice.id, "number": invoice.number},
        )
        # schedule follow-up 7 days before due (Plan 6)
        from followups.services import schedule_invoice_reminder

        schedule_invoice_reminder(invoice)
    return invoice
