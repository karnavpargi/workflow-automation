"""Invoice Ninja self-hosted billing adapter (free/OSS)."""

import httpx

from integrations.base import BillingAdapter, IntegrationUnavailable


class InvoiceNinjaBillingAdapter(BillingAdapter):
    """Push invoices to Invoice Ninja's REST API.

    Args:
        credentials: ``base_url`` and ``token``.
    """

    def __init__(self, credentials: dict) -> None:
        """Store base_url and token; build httpx client with auth header.

        Args:
            credentials: Dict with base_url and token.
        """
        self.base_url = credentials["base_url"].rstrip("/")
        self.token = credentials["token"]
        self.client = httpx.Client(
            headers={"X-Api-Token": self.token, "Accept": "application/json"},
            timeout=10.0,
        )

    def push_invoice(self, invoice: dict) -> str:
        """Push an invoice to Invoice Ninja.

        Args:
            invoice: Invoice payload.

        Returns:
            Vendor-side invoice id.

        Raises:
            IntegrationUnavailable: on non-2xx response.
        """
        try:
            r = self.client.post(
                f"{self.base_url}/api/v1/invoices",
                json=invoice,
            )
            r.raise_for_status()
            data = r.json()
            return str(data.get("data", {}).get("id", ""))
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(str(exc)) from exc
