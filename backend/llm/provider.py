"""Provider interface placeholder for future LLM integrations."""

from typing import Protocol


class LLMProvider(Protocol):
    """Stable interface that business logic will use for LLM calls."""

    def generate(self, prompt: str) -> str:
        """Generate a response from a prompt."""
        ...