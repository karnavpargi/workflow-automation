"""Django SMTP email adapter stub; replaced in Task 3."""

from integrations.base import EmailAdapter


class DjangoSmtpEmailAdapter(EmailAdapter):
    """Stub from Task 2; real implementation in Task 3."""

    def __init__(self, credentials: dict) -> None:
        self.credentials = credentials

    def send(self, *, to, subject, body, attachments=None) -> None:
        """Stub; does nothing."""
        return None
