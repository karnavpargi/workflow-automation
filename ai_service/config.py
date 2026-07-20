"""AI service configuration loaded from environment.

The ``AI_`` prefix is applied to every setting so they can be set in a
shared ``.env`` file alongside the Django ``DJANGO_*`` variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the AI microservice.

    Attributes:
        jwt_secret: Shared with ``SECRET_KEY`` in Django settings so the
            same JWT minted by ``djangorestframework-simplejwt`` verifies here.
        database_url: Postgres DSN with the ``pgvector`` extension.
        ollama_base_url: Ollama server URL.
        ollama_model: Default chat model name (e.g. ``llama3.1``).
        embedding_model: HuggingFace embedding model (default
            ``BAAI/bge-small-en``).
        enable_openai: Opt-in flag for the paid OpenAI provider.
        openai_api_key: Only consulted when ``enable_openai`` is True.
        enable_langsmith: Opt-in flag for the LangSmith Developer (free) tier.
        langsmith_api_key: Only consulted when ``enable_langsmith`` is True.
    """

    jwt_secret: str = "dev-insecure-key"
    database_url: str = "postgresql://wa:wa@localhost:5432/wa"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1"
    embedding_model: str = "BAAI/bge-small-en"
    enable_openai: bool = False
    openai_api_key: str = ""
    enable_langsmith: bool = False
    langsmith_api_key: str = ""

    model_config = SettingsConfigDict(
        env_prefix="AI_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
