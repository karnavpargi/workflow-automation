"""Tests for the embeddings cascade (HF -> Ollama -> OpenAI)."""

from unittest.mock import MagicMock, patch

from ai_service.llm import embeddings


def test_get_embeddings_prefers_huggingface_when_available(monkeypatch):
    """HuggingFaceEmbeddings is tried first; on success it is returned."""
    fake_hf = MagicMock(name="HuggingFaceEmbeddings")
    monkeypatch.setattr(embeddings, "ollama_reachable", lambda: False)
    monkeypatch.setattr(embeddings.settings, "enable_openai", False)
    with patch(
        "langchain_community.embeddings.HuggingFaceEmbeddings",
        return_value=fake_hf,
    ) as hf_cls:
        out = embeddings.get_embeddings()
    hf_cls.assert_called_once_with(model_name=embeddings.settings.embedding_model)
    assert out is fake_hf


def test_get_embeddings_falls_back_to_ollama_when_hf_fails(monkeypatch):
    """If HuggingFace raises, the factory tries OllamaEmbeddings next."""
    fake_ollama = MagicMock(name="OllamaEmbeddings")
    monkeypatch.setattr(embeddings, "ollama_reachable", lambda: True)
    monkeypatch.setattr(embeddings.settings, "enable_openai", False)
    with (
        patch(
            "langchain_community.embeddings.HuggingFaceEmbeddings",
            side_effect=RuntimeError("no torch"),
        ),
        patch(
            "langchain_ollama.OllamaEmbeddings",
            return_value=fake_ollama,
        ) as ollama_cls,
    ):
        out = embeddings.get_embeddings()
    ollama_cls.assert_called_once()
    assert out is fake_ollama


def test_get_embeddings_falls_back_to_openai_when_others_fail(monkeypatch):
    """If HF and Ollama both fail, the factory uses OpenAI when opted in."""
    fake_openai = MagicMock(name="OpenAIEmbeddings")
    monkeypatch.setattr(embeddings, "ollama_reachable", lambda: False)
    monkeypatch.setattr(embeddings.settings, "enable_openai", True)
    monkeypatch.setattr(embeddings.settings, "openai_api_key", "sk-test")
    with (
        patch(
            "langchain_community.embeddings.HuggingFaceEmbeddings",
            side_effect=RuntimeError("no torch"),
        ),
        patch(
            "langchain_openai.OpenAIEmbeddings",
            return_value=fake_openai,
        ) as openai_cls,
    ):
        out = embeddings.get_embeddings()
    openai_cls.assert_called_once_with(api_key="sk-test")
    assert out is fake_openai


def test_get_embeddings_raises_when_no_provider(monkeypatch):
    """If nothing works, the factory raises ``RuntimeError``."""
    monkeypatch.setattr(embeddings, "ollama_reachable", lambda: False)
    monkeypatch.setattr(embeddings.settings, "enable_openai", False)
    with patch(
        "langchain_community.embeddings.HuggingFaceEmbeddings",
        side_effect=RuntimeError("no torch"),
    ):
        import pytest as _pytest

        with _pytest.raises(RuntimeError, match="No embeddings provider"):
            embeddings.get_embeddings()
