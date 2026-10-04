"""Central configuration boundary for environment-backed settings."""

import os


def get_llm_provider() -> str:
    """Return the configured provider name."""
    return os.getenv("LLM_PROVIDER", "ollama")


def get_ollama_base_url() -> str:
    """Return the configured Ollama service URL."""
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


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