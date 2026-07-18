"""Tests for Nextcloud WebDAV storage adapter."""

import httpx
import pytest
import respx

from integrations.base import IntegrationUnavailable
from integrations.storage.nextcloud import NextcloudStorageAdapter


@respx.mock
def test_put_returns_path():
    """put() uploads via WebDAV PUT and returns the path."""
    respx.put("https://nc.example.com/remote.php/dav/files/u/invoices/1.pdf").mock(
        return_value=httpx.Response(201)
    )
    adapter = NextcloudStorageAdapter(
        {
            "base_url": "https://nc.example.com",
            "username": "u",
            "password": "p",
        }
    )
    path = adapter.put("invoices/1.pdf", b"%PDF", "application/pdf")
    assert path == "invoices/1.pdf"


@respx.mock
def test_put_unavailable_raises():
    """5xx from Nextcloud raises IntegrationUnavailable."""
    respx.put("https://nc.example.com/remote.php/dav/files/u/invoices/1.pdf").mock(
        return_value=httpx.Response(503)
    )
    adapter = NextcloudStorageAdapter(
        {
            "base_url": "https://nc.example.com",
            "username": "u",
            "password": "p",
        }
    )
    with pytest.raises(IntegrationUnavailable):
        adapter.put("invoices/1.pdf", b"%PDF", "application/pdf")


@respx.mock
def test_get_url():
    """get_url() returns the WebDAV URL (client must auth)."""
    adapter = NextcloudStorageAdapter(
        {
            "base_url": "https://nc.example.com",
            "username": "u",
            "password": "p",
        }
    )
    url = adapter.get_url("invoices/1.pdf")
    assert url == "https://nc.example.com/remote.php/dav/files/u/invoices/1.pdf"
