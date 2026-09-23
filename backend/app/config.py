from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://refunds_user:refunds_pass@postgres:5432/refunds_db"

    # LLM Configuration
    llm_provider: str = "openai/gpt-4o-mini"
    llm_fallback_provider: str | None = "ollama/llama3"
    openai_api_key: str | None = None
    ollama_api_base: str = "http://ollama:11434"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Logging
    log_level: str = "INFO"

    # PostgreSQL (used by docker-compose)
    postgres_user: str = "refunds_user"
    postgres_password: str = "refunds_pass"
    postgres_db: str = "refunds_db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
