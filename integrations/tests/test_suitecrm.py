"""Tests for SuiteCRM CRM adapter."""

import httpx
import pytest
import respx

from integrations.base import IntegrationUnavailable
from integrations.crm.suitecrm import SuiteCrmAdapter


@respx.mock
def test_upsert_contact_creates_and_returns_id():
    """upsert_contact() posts to /module/Contacts and returns the vendor id."""
    respx.post("http://crm/Api/V8/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    respx.post("http://crm/Api/V8/module/Contacts").mock(
        return_value=httpx.Response(200, json={"data": {"id": "c_42"}})
    )
    adapter = SuiteCrmAdapter(
        {
            "base_url": "http://crm",
            "client_id": "id",
            "client_secret": "secret",
        }
    )
    vid = adapter.upsert_contact({"email": "x@y.io", "name": "X"})
    assert vid == "c_42"
    # Token was fetched exactly once
    token_route = next(r for r in respx.routes if "oauth/token" in str(r))
    assert token_route.call_count == 1


@respx.mock
def test_upsert_contact_unavailable_raises():
    """Non-2xx from Contacts endpoint raises IntegrationUnavailable."""
    respx.post("http://crm/Api/V8/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    respx.post("http://crm/Api/V8/module/Contacts").mock(
        return_value=httpx.Response(503)
    )
    adapter = SuiteCrmAdapter(
        {
            "base_url": "http://crm",
            "client_id": "id",
            "client_secret": "secret",
        }
    )
    with pytest.raises(IntegrationUnavailable):
        adapter.upsert_contact({"email": "x@y.io", "name": "X"})
