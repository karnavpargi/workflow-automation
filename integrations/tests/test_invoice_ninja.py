"""Tests for Invoice Ninja billing adapter."""

import httpx
import respx

from integrations.billing.invoice_ninja import InvoiceNinjaBillingAdapter


@respx.mock
def test_push_invoice_returns_vendor_id():
    """push_invoice posts and returns vendor id."""
    respx.post("http://in/api/v1/invoices").mock(
        return_value=httpx.Response(200, json={"data": {"id": "inv_1"}})
    )
    adapter = InvoiceNinjaBillingAdapter(
        {
            "base_url": "http://in",
            "token": "tok",
        }
    )
    vid = adapter.push_invoice({"amount": 100, "client_id": "c1"})
    assert vid == "inv_1"
