"""Discharge-summary upload routes."""

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from backend.config import get_ollama_base_url, get_ollama_model
from backend.db import get_db
from backend.formatting.export import create_export
from backend.formatting.structuring import structure_document, verify_content_presence
from backend.llm.provider import LLMProvider, OllamaProvider
from backend.models.database import Report
from backend.models.schemas import (
    DecisionRequest,
    ExtractionResponse,
    PersistedReportResponse,
    PreviewResponse,
    ReviewHistoryResponse,
    ReviewResponse,
    SuggestionStatusRequest,
)
from backend.observability.tracing import observation
from backend.rag.workflow import review_extraction
from backend.services.extraction import extract_upload, extract_upload_document
from backend.services.persistence import (
    create_report,
    find_report,
    list_reports,
    record_decision,
    record_export,
    to_persisted_response,
    update_suggestion_status,
)

router = APIRouter(prefix="/discharge", tags=["discharge"])
reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])


def get_llm_provider() -> LLMProvider:
    return OllamaProvider(get_ollama_base_url(), get_ollama_model())


FILE_UPLOAD = File(...)
PROVIDER_DEPENDENCY = Depends(get_llm_provider)
DB_DEPENDENCY = Depends(get_db)


@router.post("/extract", response_model=ExtractionResponse)
async def extract_discharge(
    file: UploadFile = FILE_UPLOAD, provider: LLMProvider = PROVIDER_DEPENDENCY
) -> ExtractionResponse:
    try:
        extraction = await extract_upload(file, provider)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return ExtractionResponse(
        filename=file.filename or "unknown",
        content_type=file.content_type,
        extraction=extraction,
    )


@router.post("/review", response_model=ReviewResponse)
async def review_discharge(
    file: UploadFile = FILE_UPLOAD,
    provider: LLMProvider = PROVIDER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ReviewResponse:
    """Extract, review, and persist a discharge summary report."""
    try:
        return await _create_review(file, provider, db)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


async def _create_review(
    file: UploadFile, provider: LLMProvider, db: Session
) -> ReviewResponse:
    with observation(
        "review-discharge-document",
        input_data={"file_type": Path(file.filename or "").suffix.lower()},
    ) as trace:
        source_text, extraction = await extract_upload_document(file, provider)
        try:
            review = review_extraction(
                extraction, source_text=source_text, provider=provider
            )
        except TypeError:
            review = review_extraction(extraction)
        report = create_report(
            db,
            file.filename or "unknown",
            review,
            source_text,
            langfuse_trace_id=trace.trace_id,
            langfuse_parent_observation_id=trace.observation_id,
        )
        suggestions = [
            suggestion.model_copy(update={"suggestion_id": persisted.id})
            for suggestion, persisted in zip(review.suggestions, report.suggestions)
        ]
        trace.update(
            {
                "review_status": review.status,
                "comparison_count": len(review.comparisons),
                "suggestion_count": len(review.suggestions),
            }
        )
        return review.model_copy(
            update={
                "report_id": report.id,
                "suggestions": suggestions,
                "source_text": source_text,
            }
        )


@reviews_router.post("", response_model=ReviewResponse)
async def create_review(
    file: UploadFile = FILE_UPLOAD,
    provider: LLMProvider = PROVIDER_DEPENDENCY,
    db: Session = DB_DEPENDENCY,
) -> ReviewResponse:
    """Create and persist a review for the live frontend API."""
    try:
        return await _create_review(file, provider, db)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@reviews_router.get("/{report_id}", response_model=PersistedReportResponse)
def get_review(report_id: int, db: Session = DB_DEPENDENCY) -> PersistedReportResponse:
    report = find_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return to_persisted_response(report)


@reviews_router.patch(
    "/{report_id}/suggestions/{suggestion_id}",
    response_model=PersistedReportResponse,
)
def patch_suggestion_status(
    report_id: int,
    suggestion_id: int,
    request: SuggestionStatusRequest,
    db: Session = DB_DEPENDENCY,
) -> PersistedReportResponse:
    report = update_suggestion_status(db, report_id, suggestion_id, request.status)
    if report is None:
        raise HTTPException(status_code=404, detail="Review or suggestion not found.")
    return to_persisted_response(report)


def _structured_report_content(report: Report) -> str:
    accepted_suggestions = [
        suggestion
        for suggestion in report.suggestions
        if suggestion.decision == "accepted"
    ]
    with observation(
        "structure-reviewed-document",
        as_type="chain",
        input_data={
            "source_character_count": len(report.source_text),
            "accepted_suggestion_count": len(accepted_suggestions),
        },
    ) as trace:
        structured = structure_document(report.source_text, accepted_suggestions)
        with observation(
            "verify-original-content-presence",
            input_data={"source_character_count": len(report.source_text)},
        ) as verification:
            content_is_preserved = verify_content_presence(
                report.source_text, structured
            )
            verification.update({"content_preserved": content_is_preserved})
        if not content_is_preserved:
            trace.update({"content_preserved": False})
            raise HTTPException(
                status_code=500,
                detail="Structured document dropped original content; verification failed.",
            )
        trace.update(
            {
                "content_preserved": True,
                "structured_character_count": len(structured),
            }
        )
        return structured


@reviews_router.get("/{report_id}/preview", response_model=PreviewResponse)
def preview_review(
    report_id: int,
    format: Literal["pdf", "docx", "txt"] = Query(...),
    db: Session = DB_DEPENDENCY,
) -> PreviewResponse:
    report = find_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    content = _structured_report_content(report)
    return PreviewResponse(
        report_id=report.id,
        format=format,
        content=content,
        exported=False,
    )


@reviews_router.post("/{report_id}/export")
def export_review(
    report_id: int,
    format: Literal["pdf", "docx", "txt"] = Query(...),
    db: Session = DB_DEPENDENCY,
) -> Response:
    report = find_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Review not found.")

    with observation(
        "export-reviewed-document",
        input_data={"format": format, "report_status": report.status},
        trace_id=report.langfuse_trace_id,
        parent_observation_id=report.langfuse_parent_observation_id,
    ) as trace:
        structured = _structured_report_content(report)
        artifact = create_export(structured, format)

        export = record_export(db, report_id)
        if export is None:
            raise HTTPException(status_code=404, detail="Review not found.")

        trace.update(
            {
                "export_recorded": True,
                "format": format,
                "artifact_byte_count": len(artifact.content),
            }
        )
        return Response(
            content=artifact.content,
            media_type=artifact.media_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="review-{report.id}.{artifact.extension}"'
                )
            },
        )


@reviews_router.get("", response_model=ReviewHistoryResponse)
def review_history(
    search: str | None = None,
    status: str | None = None,
    sort: str = Query("newest", pattern="^(newest|oldest|score)$"),
    group_by: str | None = Query(None, pattern="^(diagnosis|status)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = DB_DEPENDENCY,
) -> ReviewHistoryResponse:
    return list_reports(db, search, status, sort, group_by, offset, limit)


@router.get("/reports/{report_id}", response_model=PersistedReportResponse)
def get_report(report_id: int, db: Session = DB_DEPENDENCY) -> PersistedReportResponse:
    """Retrieve a persisted report with its decisions and audit history."""
    report = find_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return to_persisted_response(report)


@router.post(
    "/reports/{report_id}/suggestions/{suggestion_id}/decision",
    response_model=PersistedReportResponse,
)
def decide_suggestion(
    report_id: int,
    suggestion_id: int,
    request: DecisionRequest,
    db: Session = DB_DEPENDENCY,
) -> PersistedReportResponse:
    """Persist one explicit doctor decision and return the updated report."""
    report = record_decision(db, report_id, suggestion_id, request.decision)
    if report is None:
        raise HTTPException(status_code=404, detail="Report or suggestion not found.")
    return to_persisted_response(report)