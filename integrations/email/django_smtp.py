"""Email adapter backed by Django's email backend (SMTP / locmem)."""

from django.core.mail import EmailMessage

from integrations.base import EmailAdapter


class DjangoSmtpEmailAdapter(EmailAdapter):
    """Send email via Django's configured EMAIL_BACKEND.

    Args:
        credentials: Unused for now; reserved for per-tenant SMTP.
    """

    def __init__(self, credentials: dict) -> None:
        """Store credentials (future per-tenant SMTP).

        Args:
            credentials: Vendor credentials dict.
        """
        self.credentials = credentials

    def send(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> None:
        """Send an email via Django.

        Args:
            to: Recipients.
            subject: Subject line.
            body: Body text.
            attachments: Optional (filename, bytes, content_type) list.
        """
        msg = EmailMessage(subject=subject, body=body, to=to)
        for name, data, ctype in attachments or []:
            msg.attach(name, data, ctype)
        msg.send(fail_silently=False)
