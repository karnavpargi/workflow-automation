"""Tests for MinIO storage adapter."""

from unittest.mock import MagicMock, patch

from integrations.storage.minio_client import MinioStorageAdapter


def test_put_returns_path():
    """put() uploads bytes and returns the object path."""
    with patch("integrations.storage.minio_client.Minio") as MockMinio:
        client = MagicMock()
        MockMinio.return_value = client
        adapter = MinioStorageAdapter(
            {
                "endpoint": "localhost:9000",
                "access_key": "minio",
                "secret_key": "minio123",
                "bucket": "wa",
                "secure": False,
            }
        )
        path = adapter.put("invoices/1.pdf", b"%PDF", "application/pdf")
        assert path == "invoices/1.pdf"
        client.put_object.assert_called_once()
