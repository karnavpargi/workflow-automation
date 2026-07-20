"""Tests for the document extraction + pgvector-ingest agent.

``unstructured`` partitioning and the PGVector store are both mocked
so the test exercises the agent wiring without touching real services.
"""

from unittest.mock import MagicMock, patch

import pytest  # noqa: F401


def test_extract_text_from_pdf_uses_unstructured_partition():
    """``extract_text`` delegates to ``unstructured.partition.auto``."""
    from ai_service.agents import document_extract

    with patch("ai_service.agents.document_extract._partition") as partition:
        partition.return_value = [MagicMock(text="hello world")]
        out = document_extract.extract_text(b"%PDF-1.4", content_type="application/pdf")
    assert out == "hello world"
    partition.assert_called_once()


def test_chunk_text_splits_long_text():
    """Long text is split into roughly-equal chunks honoring word boundaries."""
    from ai_service.agents.document_extract import chunk_text

    text = " ".join(f"word{i}" for i in range(100))
    chunks = chunk_text(text, chunk_size=10)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 11 for c in chunks)
    assert " ".join(chunks) == text


def test_chunk_text_handles_short_text():
    """Text shorter than the chunk size is returned as a single chunk."""
    from ai_service.agents.document_extract import chunk_text

    assert chunk_text("hi", chunk_size=100) == ["hi"]


def test_ingest_chunks_writes_to_pgvector(monkeypatch):
    """``ingest_chunks`` builds a PGVector store and adds documents."""
    from ai_service.agents import document_extract

    fake_store = MagicMock()
    fake_class = MagicMock(return_value=fake_store)
    fake_embeddings = MagicMock()
    with patch("ai_service.agents.document_extract.PGVector", fake_class):
        document_extract.ingest_chunks(
            tenant_id=42,
            chunks=["chunk one", "chunk two"],
            embeddings=fake_embeddings,
            collection="docs",
        )
    fake_class.assert_called_once()
    fake_store.add_texts.assert_called_once()
    args, kwargs = fake_store.add_texts.call_args
    assert args[0] == ["chunk one", "chunk two"]


def test_extract_document_endpoint_returns_extracted_fields():
    """POST /agents/extract-document returns the parsed chunks + text."""
    from fastapi.testclient import TestClient

    from ai_service.main import app

    client = TestClient(app)

    with (
        patch(
            "ai_service.agents.document_extract.extract_text",
            return_value="Some document text.",
        ),
        patch(
            "ai_service.agents.document_extract.chunk_text",
            return_value=["Some document text."],
        ),
        patch(
            "ai_service.agents.document_extract.ingest_chunks",
            return_value=None,
        ),
        patch(
            "ai_service.llm.embeddings.get_embeddings",
            return_value=MagicMock(),
        ),
    ):
        r = client.post(
            "/agents/extract-document",
            json={
                "content_b64": "U29tZSBkb2N1bWVudCB0ZXh0Lg==",
                "content_type": "text/plain",
            },
        )

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["text"] == "Some document text."
    assert body["chunks"] == ["Some document text."]
