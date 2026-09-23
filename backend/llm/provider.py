"""LLM provider abstraction and local Ollama adapter."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol
from urllib.parse import urlparse

from backend.config import get_llm_validation_retries, get_ollama_temperature
from backend.llm.prompts import EXTRACTION_PROMPT
from backend.models.schemas import DischargeExtraction


class LLMProvider(Protocol):
    """Stable interface used by extraction business logic."""

    def extract_discharge(self, text: str) -> DischargeExtraction:
        """Extract structured discharge fields from document text."""
        ...


class OllamaProvider:
    """Provider adapter for the local Ollama HTTP API."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 120.0,
        validation_retries: int | None = None,
    ) -> None:
        parsed_url = urlparse(base_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("Ollama base URL must use http or https")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.temperature = get_ollama_temperature()
        self.validation_retries = (
            get_llm_validation_retries()
            if validation_retries is None
            else validation_retries
        )

    def extract_discharge(self, text: str) -> DischargeExtraction:
        prompt = EXTRACTION_PROMPT.format(document_text=text)
        for attempt in range(self.validation_retries + 1):
            request_body = json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": self.temperature},
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=request_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:  # nosec B310
                    payload = json.loads(response.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as error:
                raise RuntimeError("Unable to connect to the configured Ollama service") from error
            except json.JSONDecodeError as error:
                raise RuntimeError("Ollama returned an invalid response") from error
            raw_response = payload.get("response")
            if not isinstance(raw_response, str):
                raise TypeError("Ollama response did not contain generated text")
            try:
                return DischargeExtraction.model_validate(json.loads(raw_response))
            except (json.JSONDecodeError, ValueError) as error:
                if attempt == self.validation_retries:
                    raise RuntimeError(
                        "Ollama output did not match the extraction schema after "
                        f"{self.validation_retries + 1} attempts"
                    ) from error
        raise RuntimeError("Ollama extraction failed unexpectedly")