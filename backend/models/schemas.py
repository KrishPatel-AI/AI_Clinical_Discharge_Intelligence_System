"""Pydantic contracts shared by extraction and API layers."""

from pydantic import BaseModel, Field


class DischargeExtraction(BaseModel):
    """Structured fields extracted from a discharge summary."""

    diagnosis: str = Field(min_length=1)
    medications: list[str] = Field(default_factory=list)
    follow_up_requirements: list[str] = Field(default_factory=list)
    warning_signs: list[str] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    """Response returned after a validated document is processed."""

    filename: str
    content_type: str | None
    extraction: DischargeExtraction