"""LLM factory: free-first chat-model provider cascade.

Default is Ollama (self-hosted, free). OpenAI is opt-in only.
"""

import httpx

from ai_service.config import settings


def ollama_reachable() -> bool:
    """Return True if the configured Ollama server responds to ``/api/tags``.

    Returns:
        Reachability flag.
    """
    try:
        r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def get_chat_model():
    """Return the active chat model.

    Preference order:
      1. Ollama (free, self-hosted) if reachable.
      2. OpenAI only if ``AI_ENABLE_OPENAI=1`` and a key is set.

    Returns:
        A LangChain ``BaseChatModel`` instance.

    Raises:
        RuntimeError: if no provider is available.
    """
    if ollama_reachable():
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    if settings.enable_openai and settings.openai_api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",
        )
    raise RuntimeError(
        "No LLM provider available (start Ollama or set AI_ENABLE_OPENAI=1)"
    )
