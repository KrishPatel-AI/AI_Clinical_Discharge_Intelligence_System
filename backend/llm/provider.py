"""LLM provider abstraction and local Ollama adapter."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Protocol
from urllib.parse import urlparse

from backend.config import get_llm_validation_retries, get_ollama_temperature
from backend.llm.prompts import EXTRACTION_PROMPT, RECOMMENDATION_PROMPT
from backend.models.schemas import DischargeExtraction
from backend.observability.tracing import observation


class LLMProvider(Protocol):
    """Stable interface used by extraction business logic."""

    def extract_discharge(self, text: str) -> DischargeExtraction:
        """Extract structured discharge fields from document text."""
        ...

    def generate_recommendation(
        self,
        section: str,
        document_text: str,
        guideline_passage: str,
        diagnosis: str,
    ) -> dict[str, str]:
        """Generate an actionable clinical recommendation for an identified gap."""
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
        with observation(
            "extract-structured-fields",
            as_type="generation",
            input_data={
                "model": self.model,
                "temperature": self.temperature,
                "document_character_count": len(text),
            },
        ) as trace:
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
                    raise RuntimeError(
                        "Unable to connect to the configured Ollama service"
                    ) from error
                except json.JSONDecodeError as error:
                    raise RuntimeError("Ollama returned an invalid response") from error
                raw_response = payload.get("response")
                if not isinstance(raw_response, str):
                    raise TypeError("Ollama response did not contain generated text")
                try:
                    extraction = DischargeExtraction.model_validate(
                        json.loads(raw_response)
                    )
                    trace.update(
                        {
                            "schema_valid": True,
                            "attempt_count": attempt + 1,
                            "medication_count": len(extraction.medications),
                            "follow_up_count": len(extraction.follow_up_requirements),
                            "warning_sign_count": len(extraction.warning_signs),
                        }
                    )
                    return extraction
                except (json.JSONDecodeError, ValueError) as error:
                    if attempt == self.validation_retries:
                        raise RuntimeError(
                            "Ollama output did not match the extraction schema after "
                            f"{self.validation_retries + 1} attempts"
                        ) from error
        raise RuntimeError("Ollama extraction failed unexpectedly")

    def generate_recommendation(
        self,
        section: str,
        document_text: str,
        guideline_passage: str,
        diagnosis: str,
    ) -> dict[str, str]:
        prompt = RECOMMENDATION_PROMPT.format(
            section=section,
            document_text=document_text[:2000],
            guideline_passage=guideline_passage[:1200],
        )
        with observation(
            "generate-actionable-recommendation",
            as_type="generation",
            input_data={
                "model": self.model,
                "section": section,
                "diagnosis": diagnosis,
            },
        ) as trace:
            try:
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
                with urllib.request.urlopen(request, timeout=self.timeout) as response:  # nosec B310
                    payload = json.loads(response.read().decode("utf-8"))
                raw_response = payload.get("response", "")
                data = json.loads(raw_response) if isinstance(raw_response, str) else {}
                action = str(data.get("action", "add")).lower()
                if action not in {"add", "modify", "remove"}:
                    action = "add"
                target_text = str(data.get("target_text", "")).strip()
                suggested_text = str(data.get("suggested_text", "")).strip()
                explanation = str(data.get("explanation", "")).strip()

                if not suggested_text or not explanation:
                    raise ValueError("Incomplete recommendation output from LLM")

                if target_text and target_text not in document_text:
                    matched_sentence = next(
                        (
                            line.strip()
                            for line in document_text.splitlines()
                            if line.strip()
                            and (
                                section.replace("_", " ") in line.lower()
                                or any(
                                    w.lower() in line.lower()
                                    for w in target_text.split()[:3]
                                    if len(w) > 3
                                )
                            )
                        ),
                        "",
                    )
                    target_text = matched_sentence or target_text

                res = {
                    "action": action,
                    "target_text": target_text,
                    "suggested_text": suggested_text,
                    "explanation": explanation,
                }
                trace.update({"action": action, "has_target": bool(target_text)})
                return res
            except (
                urllib.error.URLError,
                TimeoutError,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                TypeError,
            ) as error:
                fallback = deterministic_guideline_recommendation(
                    section, document_text, guideline_passage, diagnosis
                )
                trace.update({"fallback_used": True, "error": str(error)})
                return fallback


def deterministic_guideline_recommendation(
    section: str,
    document_text: str,
    guideline_passage: str,
    diagnosis: str,
) -> dict[str, str]:
    """Produce a deterministic, clinically grounded recommendation when LLM is unavailable."""
    clean_section = section.replace("_", " ").lower()

    lines = [line.strip() for line in document_text.splitlines() if line.strip()]
    target_line = ""
    for line in lines:
        if clean_section in line.lower() or any(
            k in line.lower() for k in ["rx", "medication", "follow", "advice", "warning"]
        ):
            target_line = line
            break
    if not target_line and lines:
        target_line = lines[0]

    passage_sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", guideline_passage)
        if s.strip() and len(s.strip()) > 15
    ]
    relevant_sentence = (
        passage_sentences[0] if passage_sentences else guideline_passage[:150]
    )
    for s in passage_sentences:
        if any(
            term in s.lower()
            for term in [clean_section, "daily", "prescribe", "dose", "review", "emergency"]
        ):
            relevant_sentence = s
            break

    if "medication" in clean_section:
        has_existing_meds = any(
            "med" in line.lower() or "rx" in line.lower() for line in lines
        )
        action = "modify" if has_existing_meds else "add"
        return {
            "action": action,
            "target_text": target_line or "Medications",
            "suggested_text": f"Prescribe guideline-directed therapy: {relevant_sentence}",
            "explanation": f"Clinical guideline requires evidence-based medication regimen for {diagnosis}; update discharge medications accordingly.",
        }
    elif "follow" in clean_section:
        return {
            "action": "add",
            "target_text": target_line or "Follow-up",
            "suggested_text": f"Schedule follow-up review within 7-14 days: {relevant_sentence}",
            "explanation": f"Scheduled follow-up is critical for monitoring {diagnosis} stabilization and preventing hospital readmission.",
        }
    elif "warning" in clean_section:
        return {
            "action": "add",
            "target_text": target_line or "Advice",
            "suggested_text": f"Counsel patient on urgent warning signs: {relevant_sentence}",
            "explanation": "Patient must receive explicit instructions on red-flag warning signs requiring immediate emergency medical evaluation.",
        }
    else:
        return {
            "action": "add",
            "target_text": target_line or section,
            "suggested_text": f"Incorporate guideline requirements: {relevant_sentence}",
            "explanation": f"Document lacks complete coverage of {clean_section} as specified in the clinical guideline.",
        }