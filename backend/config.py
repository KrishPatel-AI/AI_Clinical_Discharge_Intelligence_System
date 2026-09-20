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


def get_database_url() -> str:
    """Return the configured SQLAlchemy database URL."""
    return os.getenv("DATABASE_URL", "sqlite:///./clinical_discharge.db")