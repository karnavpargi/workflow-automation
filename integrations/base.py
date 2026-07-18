"""Abstract adapter interfaces and typed integration exceptions.

Every vendor adapter implements one of these interfaces so the rest of
the platform never depends on vendor-specific HTTP details.
"""

from abc import ABC, abstractmethod
from typing import Any


class IntegrationUnavailable(Exception):
    """Vendor is down or unreachable; retryable."""


class IntegrationAuthFailed(Exception):
    """Credentials rejected; not retryable without config change."""


class IntegrationRateLimited(Exception):
    """Vendor rate limit hit; retryable after backoff."""


class CrmAdapter(ABC):
    """CRM operations against SuiteCRM (or compatible)."""

    @abstractmethod
    def upsert_contact(self, contact: dict[str, Any]) -> str:
        """Create or update a contact; return vendor id.

        Args:
            contact: Contact fields (email, name, ...).

        Returns:
            Vendor-side contact id.
        """


class BillingAdapter(ABC):
    """Billing operations against Invoice Ninja."""

    @abstractmethod
    def push_invoice(self, invoice: dict[str, Any]) -> str:
        """Push an invoice and return vendor id.

        Args:
            invoice: Invoice payload.

        Returns:
            Vendor-side invoice id.
        """


class StorageAdapter(ABC):
    """Document / object storage operations."""

    @abstractmethod
    def put(self, path: str, data: bytes, content_type: str) -> str:
        """Store bytes at path; return URL or path.

        Args:
            path: Object path.
            data: File bytes.
            content_type: MIME type.

        Returns:
            Accessible path or URL.
        """

    @abstractmethod
    def get_url(self, path: str, expires_seconds: int = 3600) -> str:
        """Return a time-limited URL for the object.

        Args:
            path: Object path.
            expires_seconds: Link lifetime.

        Returns:
            Signed or temporary URL.
        """


class ChatAdapter(ABC):
    """Chat notifications (Mattermost)."""

    @abstractmethod
    def post(self, channel: str, text: str) -> None:
        """Post a message to a channel.

        Args:
            channel: Channel name (embedded in text if webhook is fixed).
            text: Message body.
        """


class EmailAdapter(ABC):
    """Outbound email."""

    @abstractmethod
    def send(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> None:
        """Send an email.

        Args:
            to: Recipient addresses.
            subject: Subject line.
            body: Plain-text or HTML body.
            attachments: Optional list of (filename, bytes, content_type).
        """
