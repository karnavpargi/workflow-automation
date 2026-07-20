"""Tests for the AI service settings module."""


def test_settings_loads_defaults_when_no_env(monkeypatch):
    """Settings has safe defaults for every field."""
    from ai_service.config import Settings

    s = Settings(_env_file=None)
    assert s.ollama_model == "llama3.1"
    assert s.embedding_model == "BAAI/bge-small-en"
    assert s.enable_openai is False
    assert s.enable_langsmith is False
    assert s.openai_api_key == ""


def test_settings_reads_ai_prefixed_env(monkeypatch):
    """``AI_*`` environment variables populate the fields."""
    monkeypatch.setenv("AI_OLLAMA_MODEL", "qwen2.5")
    monkeypatch.setenv("AI_ENABLE_OPENAI", "1")
    monkeypatch.setenv("AI_OPENAI_API_KEY", "sk-test")
    from ai_service.config import Settings

    s = Settings(_env_file=None)
    assert s.ollama_model == "qwen2.5"
    assert s.enable_openai is True
    assert s.openai_api_key == "sk-test"


def test_settings_module_level_singleton_exists():
    """A module-level ``settings`` instance is importable for app code."""
    from ai_service import config

    assert config.settings is not None
    assert isinstance(config.settings.ollama_base_url, str)
