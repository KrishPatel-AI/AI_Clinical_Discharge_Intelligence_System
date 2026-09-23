"""Pydantic contracts shared by extraction and API layers."""

from typing import Literal

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
    suggestion_id: int | None = None
    decision: Literal["accepted", "ignored"] | None = None


class ReviewResponse(BaseModel):
    """Retrieval, comparison, and Phase 5 scoring result."""

    diagnosis: str
    status: str
    message: str
    guideline: GuidelineMatch | None = None
    comparisons: list[ComparisonItem] = Field(default_factory=list)
    completeness_score: int | None = Field(default=None, ge=0, le=100)
    suggestions: list[Suggestion] = Field(default_factory=list)
    report_id: int | None = None


class DecisionRequest(BaseModel):
    """A doctor's explicit decision about one generated suggestion."""

    decision: Literal["accepted", "ignored"]


class SuggestionStatusRequest(BaseModel):
    """A live review status update for one suggestion."""

    status: Literal["pending", "accepted", "rejected"]


class AuditLogResponse(BaseModel):
    """One persisted doctor decision."""

    id: int
    suggestion_id: int
    decision: Literal["accepted", "ignored"]
    decided_at: str


class PersistedSuggestion(BaseModel):
    """A suggestion and its current review decision."""

    id: int
    section: str
    explanation: str
    guideline_passage: str
    source_url: str
    status: Literal["pending", "accepted", "rejected"] = "pending"
    decision: Literal["accepted", "ignored"] | None = None
    decided_at: str | None = None


class PersistedReportResponse(BaseModel):
    """A report with all suggestions and their audit history."""

    id: int
    filename: str
    diagnosis: str
    status: str
    message: str
    completeness_score: int | None = Field(default=None, ge=0, le=100)
    created_at: str
    suggestions: list[PersistedSuggestion] = Field(default_factory=list)
    audit_logs: list[AuditLogResponse] = Field(default_factory=list)


class PreviewResponse(BaseModel):
    """Preview-safe current document representation."""

    report_id: int
    format: Literal["pdf", "docx", "txt"]
    content: str
    exported: bool = False


class ReviewHistoryResponse(BaseModel):
    """Server-filtered review history for frontend consumption."""

    reviews: list[PersistedReportResponse] = Field(default_factory=list)
    total: int
    offset: int
    limit: int
    groups: dict[str, list[int]] | None = None