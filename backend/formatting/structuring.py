"""Layout-only document structuring for export-time formatting."""

from __future__ import annotations

import re
from collections.abc import Iterable

from backend.models.schemas import PersistedSuggestion

SECTION_ORDER = (
    "Patient Information",
    "Diagnosis",
    "Hospital Course",
    "Medications",
    "Advice",
    "Follow-up",
    "Added on review",
)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _split_sentences(text: str) -> list[str]:
    if not text.strip():
        return []
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [piece.strip() for piece in pieces if piece and piece.strip()]


def _assign_section(sentence: str) -> str:
    lower = sentence.lower()
    if any(keyword in lower for keyword in ["patient", "name", "age", "sex", "dob", "mrn", "admission", "discharge"]):
        return "Patient Information"
    if any(keyword in lower for keyword in ["diagnosis", "diagnosed", "condition", "provisional", "asthma", "diabetes", "hypertension"]):
        return "Diagnosis"
    if any(keyword in lower for keyword in ["medication", "medicine", "tablet", "capsule", "inhaler", "dose", "dosage", "drug", "prescribed", "prescription"]):
        return "Medications"
    if any(keyword in lower for keyword in ["follow up", "follow-up", "review", "revisit", "appointment", "checkup", "next visit", "reassess"]):
        return "Follow-up"
    if any(keyword in lower for keyword in ["advice", "advise", "counsel", "precaution", "avoid", "monitor", "maintain", "hydration", "rest", "instructions"]):
        return "Advice"
    if any(keyword in lower for keyword in ["history", "progress", "symptoms", "improved", "observed", "course", "admitted", "hospital", "management", "treatment", "today"]):
        return "Hospital Course"
    return "Hospital Course"


def structure_document(
    source_text: str,
    accepted_suggestions: Iterable[PersistedSuggestion] | Iterable[object],
) -> str:
    """Re-label and reorder original document text without altering clinical facts."""
    sections: dict[str, list[str]] = {name: [] for name in SECTION_ORDER}

    for sentence in _split_sentences(source_text):
        sections[_assign_section(sentence)].append(sentence)

    accepted = list(accepted_suggestions)
    if accepted:
        items = []
        for s in accepted:
            suggested = getattr(s, "suggested_text", "")
            explanation = getattr(s, "explanation", "") or (
                s.explanation if hasattr(s, "explanation") else str(s)
            )
            if suggested and explanation and suggested != explanation:
                items.append(f"{suggested} - {explanation}")
            elif suggested:
                items.append(suggested)
            elif explanation:
                items.append(explanation)
            else:
                items.append(str(s))
        sections["Added on review"] = items

    render: list[str] = []
    for section_name in SECTION_ORDER:
        items = sections.get(section_name, [])
        if not items:
            continue
        render.append(f"{section_name}\n{'-' * len(section_name)}")
        for item in items:
            render.append(f"- {item}")
        render.append("")

    structured = "\n".join(render).strip()
    return structured or source_text.strip()


def verify_content_presence(original_text: str, structured_output: str) -> bool:
    """Return True only when every original sentence remains present in the structured output."""
    original_sentences = _split_sentences(original_text)
    if not original_sentences:
        return True

    normalized_output = _normalize_text(structured_output)
    for sentence in original_sentences:
        normalized_sentence = _normalize_text(sentence)
        if normalized_sentence not in normalized_output:
            return False
    return True
