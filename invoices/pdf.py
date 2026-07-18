"""PDF generation for invoices using reportlab (free/OSS)."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_invoice_pdf(invoice) -> bytes:
    """Render an Invoice to PDF bytes.

    Args:
        invoice: Invoice model instance with related ``lines`` and ``client``.

    Returns:
        PDF content as bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Invoice {invoice.number}", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            f"Bill to: {invoice.client.name} ({invoice.client.email})",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            f"Due date: {invoice.due_date.isoformat()}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            f"From: {invoice.tenant.name}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    rows = [["Description", "Qty", "Unit price", "Total"]]
    for line in invoice.lines.all():
        rows.append(
            [
                line.description,
                str(line.quantity),
                f"${line.unit_price:,.2f}",
                f"${line.quantity * line.unit_price:,.2f}",
            ]
        )
    rows.append(["", "", "Total", f"${invoice.total:,.2f}"])
    table = Table(rows)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    return buffer.getvalue()
