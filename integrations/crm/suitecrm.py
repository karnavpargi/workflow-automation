"""SuiteCRM self-hosted CRM adapter (free/OSS)."""

import httpx

from integrations.base import CrmAdapter, IntegrationUnavailable


class SuiteCrmAdapter(CrmAdapter):
    """SuiteCRM v8 REST API adapter.

    Args:
        credentials: ``base_url``, ``client_id``, ``client_secret``.
    """

    def __init__(self, credentials: dict) -> None:
        self.base_url = credentials["base_url"].rstrip("/")
        self.client_id = credentials["client_id"]
        self.client_secret = credentials["client_secret"]
        self._token: str | None = None
        self.client = httpx.Client(timeout=10.0)

    def _get_token(self) -> str:
        """Fetch OAuth2 access token via client credentials grant.

        Returns:
            Access token string.
        """
        r = self.client.post(
            f"{self.base_url}/Api/V8/oauth/token",
            json={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        r.raise_for_status()
        return r.json()["access_token"]

    def upsert_contact(self, contact: dict) -> str:
        """Create or update a contact; return vendor id.

        Args:
            contact: Contact fields (email, name, ...).

        Returns:
            Vendor-side contact id.

        Raises:
            IntegrationUnavailable: on non-2xx response.
        """
        if self._token is None:
            self._token = self._get_token()
        try:
            r = self.client.post(
                f"{self.base_url}/Api/V8/module/Contacts",
                json={"data": contact},
                headers={"Authorization": f"Bearer {self._token}"},
            )
            r.raise_for_status()
            return str(r.json()["data"]["id"])
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(str(exc)) from exc
