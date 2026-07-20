"""Tests for the optional LangSmith tracing setup."""

import os


def test_configure_langsmith_off_by_default(monkeypatch):
    """Without ``AI_ENABLE_LANGSMITH=1`` the env vars are unset."""
    from ai_service.llm import langsmith

    monkeypatch.setattr(langsmith.settings, "enable_langsmith", False)
    monkeypatch.setattr(langsmith.settings, "langsmith_api_key", "lsv-test")
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)

    status = langsmith.configure_langsmith()
    assert status == {"enabled": False, "reason": "opt-in flag off"}
    assert "LANGCHAIN_TRACING_V2" not in os.environ
    assert "LANGCHAIN_API_KEY" not in os.environ


def test_configure_langsmith_off_when_key_missing(monkeypatch):
    """If the opt-in flag is on but no key is set, tracing stays off."""
    from ai_service.llm import langsmith

    monkeypatch.setattr(langsmith.settings, "enable_langsmith", True)
    monkeypatch.setattr(langsmith.settings, "langsmith_api_key", "")
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)

    status = langsmith.configure_langsmith()
    assert status == {"enabled": False, "reason": "missing AI_LANGSMITH_API_KEY"}
    assert "LANGCHAIN_TRACING_V2" not in os.environ


def test_configure_langsmith_on_when_opted_in_with_key(monkeypatch):
    """With opt-in + key, ``LANGCHAIN_TRACING_V2=true`` + the key are set."""
    from ai_service.llm import langsmith

    monkeypatch.setattr(langsmith.settings, "enable_langsmith", True)
    monkeypatch.setattr(langsmith.settings, "langsmith_api_key", "lsv-test")
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)

    status = langsmith.configure_langsmith()
    assert status["enabled"] is True
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_API_KEY"] == "lsv-test"

    # Cleanup so we don't pollute other tests.
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    os.environ.pop("LANGCHAIN_API_KEY", None)
