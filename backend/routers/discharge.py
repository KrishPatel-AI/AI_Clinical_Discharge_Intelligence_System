"""Discharge-summary upload routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.config import get_ollama_base_url, get_ollama_model
from backend.db import get_db
from backend.llm.provider import LLMProvider, OllamaProvider
from backend.models.schemas import (
    DecisionRequest,
    ExtractionResponse,
    PersistedReportResponse,
    ReviewResponse,
)
from backend.rag.workflow import review_extraction
from backend.services.extraction import extract_upload
from backend.services.persistence import (
    create_report,
    find_report,
    record_decision,
    to_persisted_response,
)

router = APIRouter(prefix="/discharge", tags=["discharge"])


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
        extraction = await extract_upload(file, provider)
        review = review_extraction(extraction)
        report = create_report(db, file.filename or "unknown", review)
        suggestions = [
            suggestion.model_copy(update={"suggestion_id": persisted.id})
            for suggestion, persisted in zip(review.suggestions, report.suggestions)
        ]
        return review.model_copy(
            update={"report_id": report.id, "suggestions": suggestions}
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


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