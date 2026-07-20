"""Document extraction + pgvector ingestion.

The pipeline:
  1. ``extract_text`` parses raw bytes via ``unstructured.partition.auto``.
  2. ``chunk_text`` splits the text into word-bounded chunks.
  3. ``ingest_chunks`` writes them into a tenant-scoped PGVector collection.

Free/OSS only: ``unstructured`` + ``PyMuPDF`` (the latter is a transitive
dep of ``unstructured`` for PDF parsing) + ``langchain-postgres``.
"""

from collections.abc import Iterable

from langchain_postgres import PGVector

from ai_service.db import vector_store_url


def _partition(content: bytes, content_type: str) -> list[object]:
    """Run ``unstructured.partition.auto`` and return the elements.

    Args:
        content: Raw file bytes.
        content_type: MIME type (e.g. ``application/pdf``, ``text/plain``).

    Returns:
        List of unstructured elements (each has a ``.text`` attribute).
    """
    from unstructured.partition.auto import partition

    return partition(file=content, content_type=content_type)  # type: ignore[arg-type]


def extract_text(content: bytes, content_type: str) -> str:
    """Extract plain text from a document.

    Args:
        content: Raw file bytes.
        content_type: MIME type of the upload.

    Returns:
        Concatenated text from the parsed elements.
    """
    elements = _partition(content, content_type)
    return "\n\n".join(str(getattr(e, "text", "")) for e in elements).strip()


def chunk_text(text: str, *, chunk_size: int = 500) -> list[str]:
    """Split ``text`` into word-bounded chunks no larger than ``chunk_size`` words.

    Args:
        text: The full text.
        chunk_size: Maximum words per chunk.

    Returns:
        A list of chunks; the concatenation equals ``text`` modulo whitespace.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text] if text else []
    return [
        " ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)
    ]


def _collection_name(tenant_id: int, base: str) -> str:
    """Build a tenant-scoped PGVector collection name.

    Args:
        tenant_id: Owning tenant PK.
        base: Base collection name (e.g. ``"docs"``).

    Returns:
        A name like ``"tenant_42_docs"``.
    """
    return f"tenant_{tenant_id}_{base}"


def ingest_chunks(
    *,
    tenant_id: int,
    chunks: Iterable[str],
    embeddings,
    collection: str = "docs",
) -> None:
    """Write ``chunks`` into a tenant-scoped PGVector collection.

    Args:
        tenant_id: Owning tenant PK.
        chunks: Iterable of text chunks to embed and store.
        embeddings: A LangChain ``Embeddings`` instance.
        collection: Base collection name (default ``docs``).
    """
    store = PGVector(
        embeddings=embeddings,
        collection_name=_collection_name(tenant_id, collection),
        connection=vector_store_url(),
        use_jsonb=True,
    )
    store.add_texts(list(chunks))
