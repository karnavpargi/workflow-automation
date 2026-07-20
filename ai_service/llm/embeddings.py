"""Embedding model factory, free-first.

Preference order:
  1. HuggingFace local ``BAAI/bge-small-en`` (free, no network).
  2. Ollama embeddings (free, self-hosted) if HF cannot load.
  3. OpenAI embeddings only when ``AI_ENABLE_OPENAI=1`` + key.
"""

from ai_service.config import settings
from ai_service.llm.factory import ollama_reachable


def get_embeddings():
    """Return the active embeddings model.

    Returns:
        A LangChain ``Embeddings`` instance.

    Raises:
        RuntimeError: if no provider is available.
    """
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=settings.embedding_model)
    except Exception:  # noqa: BLE001
        pass
    if ollama_reachable():
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    if settings.enable_openai and settings.openai_api_key:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(api_key=settings.openai_api_key)
    raise RuntimeError(
        "No embeddings provider available "
        "(install sentence-transformers, start Ollama, or enable OpenAI)"
    )
