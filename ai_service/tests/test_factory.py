"""Tests for the LLM provider factory."""

import pytest

from ai_service.llm import factory


def test_ollama_reachable_true_when_server_returns_200(monkeypatch):
    """``ollama_reachable`` returns True on 200 from ``/api/tags``."""
    import httpx

    class _Resp:
        status_code = 200

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: _Resp())
    assert factory.ollama_reachable() is True


def test_ollama_reachable_false_on_http_error(monkeypatch):
    """``ollama_reachable`` returns False on transport errors."""
    import httpx

    def _raise(*a, **kw):
        raise httpx.HTTPError("nope")

    monkeypatch.setattr(httpx, "get", _raise)
    assert factory.ollama_reachable() is False


def test_ollama_reachable_false_on_non_200(monkeypatch):
    """``ollama_reachable`` returns False on non-200 status."""
    import httpx

    class _Resp:
        status_code = 500

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: _Resp())
    assert factory.ollama_reachable() is False


def test_get_chat_model_returns_chat_ollama_when_reachable(monkeypatch):
    """When Ollama is reachable the factory returns a ``ChatOllama``."""
    monkeypatch.setattr(factory, "ollama_reachable", lambda: True)

    from langchain_ollama import ChatOllama

    model = factory.get_chat_model()
    assert isinstance(model, ChatOllama)
    assert model.model == factory.settings.ollama_model


def test_get_chat_model_falls_back_to_openai_when_opted_in(monkeypatch):
    """When Ollama is down and OpenAI is opted in, returns ``ChatOpenAI``."""
    monkeypatch.setattr(factory, "ollama_reachable", lambda: False)
    monkeypatch.setattr(factory.settings, "enable_openai", True)
    monkeypatch.setattr(factory.settings, "openai_api_key", "sk-test")

    from langchain_openai import ChatOpenAI

    model = factory.get_chat_model()
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-4o-mini"


def test_get_chat_model_raises_when_no_provider(monkeypatch):
    """Without Ollama or OpenAI, ``get_chat_model`` raises ``RuntimeError``."""
    monkeypatch.setattr(factory, "ollama_reachable", lambda: False)
    monkeypatch.setattr(factory.settings, "enable_openai", False)
    with pytest.raises(RuntimeError, match="No LLM provider"):
        factory.get_chat_model()
