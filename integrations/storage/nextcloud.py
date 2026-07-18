"""Nextcloud WebDAV storage adapter."""

import httpx

from integrations.base import IntegrationUnavailable, StorageAdapter


class NextcloudStorageAdapter(StorageAdapter):
    """WebDAV-based storage against Nextcloud.

    Args:
        credentials: ``base_url`` (e.g. ``https://nextcloud.example.com``),
            ``username``, ``password`` (app password).
    """

    def __init__(self, credentials: dict) -> None:
        """Build the WebDAV base URL and httpx client.

        Args:
            credentials: Connection dict.
        """
        self.base_url = credentials["base_url"].rstrip("/")
        self.username = credentials["username"]
        self.password = credentials["password"]
        self.dav_root = f"{self.base_url}/remote.php/dav/files/{self.username}"
        self.client = httpx.Client(
            auth=(self.username, self.password),
            timeout=10.0,
        )

    def put(self, path: str, data: bytes, content_type: str) -> str:
        """Upload bytes to Nextcloud via WebDAV PUT.

        Args:
            path: Object path (relative to user root).
            data: File bytes.
            content_type: MIME type.

        Returns:
            The object path.

        Raises:
            IntegrationUnavailable: on non-2xx response.
        """
        url = f"{self.dav_root}/{path.lstrip('/')}"
        try:
            r = self.client.put(
                url, content=data, headers={"Content-Type": content_type}
            )
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(str(exc)) from exc
        return path

    def get_url(self, path: str, expires_seconds: int = 3600) -> str:
        """Return the WebDAV URL (client must send auth header).

        Args:
            path: Object path.
            expires_seconds: Unused for WebDAV (kept for interface compat).

        Returns:
            The full WebDAV URL.
        """
        return f"{self.dav_root}/{path.lstrip('/')}"
