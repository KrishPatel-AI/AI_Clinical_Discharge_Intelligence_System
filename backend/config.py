"""Central configuration boundary for environment-backed settings."""

import os


def get_llm_provider() -> str:
    """Return the configured provider name."""
    return os.getenv("LLM_PROVIDER", "ollama")


def get_ollama_base_url() -> str:
    """Return the configured Ollama service URL."""
    url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    if "localhost" in url:
        url = url.replace("localhost", "127.0.0.1")
    return url


def get_ollama_model() -> str:
    """Return the configured local Ollama model."""
    return os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def get_ollama_embedding_model() -> str:
    """Return the pinned local embedding model used only by Ragas evaluation."""
    return os.getenv("OLLAMA_EVAL_EMBEDDING_MODEL", "nomic-embed-text:v1.5")


def get_ollama_temperature() -> float:
    """Return the deterministic sampling temperature for judgment tasks."""
    return 0.0


def get_llm_validation_retries() -> int:
    """Return the bounded number of retries after invalid structured output."""
    return 2


def get_database_url() -> str:
    """Return the configured SQLAlchemy database URL."""
    return os.getenv("DATABASE_URL", "sqlite:///./clinical_discharge.db")


def is_langfuse_configured() -> bool:
    """Return whether both Langfuse project credentials are configured."""
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )


def get_allowed_origins() -> list[str]:
    """Return configured CORS allowed origins."""
    raw = os.getenv("ALLOWED_ORIGINS", "*")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]