"""Tests for Mattermost chat adapter."""

import httpx
import pytest
import respx

from integrations.base import IntegrationUnavailable
from integrations.chat.mattermost import MattermostChatAdapter


@respx.mock
def test_post_sends_webhook():
    """post() POSTs JSON to the configured webhook URL."""
    route = respx.post("http://mm/hooks/x").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    adapter = MattermostChatAdapter({"webhook_url": "http://mm/hooks/x"})
    adapter.post(channel="ops", text="hello")
    assert route.called


@respx.mock
def test_post_unavailable_raises():
    """5xx from Mattermost raises IntegrationUnavailable."""
    respx.post("http://mm/hooks/x").mock(return_value=httpx.Response(503))
    adapter = MattermostChatAdapter({"webhook_url": "http://mm/hooks/x"})
    with pytest.raises(IntegrationUnavailable):
        adapter.post(channel="ops", text="hello")
