"""Mattermost webhook chat adapter."""

import httpx

from integrations.base import ChatAdapter, IntegrationUnavailable


class MattermostChatAdapter(ChatAdapter):
    """Post messages via an incoming webhook.

    Args:
        credentials: Must include ``webhook_url``.
    """

    def __init__(self, credentials: dict) -> None:
        """Store webhook URL.

        Args:
            credentials: Dict with webhook_url.
        """
        self.webhook_url = credentials["webhook_url"]

    def post(self, channel: str, text: str) -> None:
        """Post a message.

        Args:
            channel: Channel name (embedded in text if webhook is fixed).
            text: Message body.

        Raises:
            IntegrationUnavailable: on non-2xx response.
        """
        try:
            r = httpx.post(
                self.webhook_url,
                json={"channel": channel, "text": text},
                timeout=10.0,
            )
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(str(exc)) from exc
