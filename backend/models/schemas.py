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


class GuidelineMatch(BaseModel):
    """The guideline evidence selected for a diagnosis."""

    diagnosis: str
    diagnosis_slug: str
    source_url: str
    passage: str
    similarity: float = Field(ge=0.0, le=1.0)


class ComparisonItem(BaseModel):
    """Comparison result for one extracted discharge-summary section."""

    section: str
    status: str
    extracted_values: list[str] = Field(default_factory=list)
    guideline_passage: str


class Suggestion(BaseModel):
    """A review item grounded in the retrieved guideline passage."""

    section: str
    explanation: str
    guideline_passage: str
    source_url: str


class ReviewResponse(BaseModel):
    """Retrieval, comparison, and Phase 5 scoring result."""

    diagnosis: str
    status: str
    message: str
    guideline: GuidelineMatch | None = None
    comparisons: list[ComparisonItem] = Field(default_factory=list)
    completeness_score: int | None = Field(default=None, ge=0, le=100)
    suggestions: list[Suggestion] = Field(default_factory=list)