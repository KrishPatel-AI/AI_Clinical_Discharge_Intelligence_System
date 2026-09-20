"""Persistence services for review reports and doctor decisions."""

from datetime import UTC, datetime
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.database import AuditLog, Report, SuggestionRecord, User
from backend.models.schemas import (
    AuditLogResponse,
    PersistedReportResponse,
    PersistedSuggestion,
    ReviewResponse,
)

DEFAULT_USERNAME = "local-doctor"
Decision = Literal["accepted", "ignored"]


def _get_or_create_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == DEFAULT_USERNAME))
    if user is None:
        user = User(username=DEFAULT_USERNAME)
        db.add(user)
        db.flush()
    return user


def create_report(db: Session, filename: str, review: ReviewResponse) -> Report:
    """Persist a generated review and all of its grounded suggestions."""
    report = Report(
        user=_get_or_create_user(db),
        filename=filename,
        diagnosis=review.diagnosis,
        status=review.status,
        message=review.message,
        completeness_score=review.completeness_score,
        suggestions=[
            SuggestionRecord(
                section=suggestion.section,
                explanation=suggestion.explanation,
                guideline_passage=suggestion.guideline_passage,
                source_url=suggestion.source_url,
            )
            for suggestion in review.suggestions
        ],
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def find_report(db: Session, report_id: int) -> Report | None:
    """Return one report with its suggestions and audit records."""
    return db.scalar(select(Report).where(Report.id == report_id))


def record_decision(
    db: Session, report_id: int, suggestion_id: int, decision: str
) -> Report | None:
    """Record a decision and return the updated report, or None if not found."""
    report = find_report(db, report_id)
    if report is None:
        return None
    suggestion = next(
        (item for item in report.suggestions if item.id == suggestion_id), None
    )
    if suggestion is None:
        return None

    decided_at = datetime.now(UTC)
    suggestion.decision = decision
    suggestion.decided_at = decided_at
    report.audit_logs.append(
        AuditLog(
            suggestion_id=suggestion.id,
            decision=decision,
            decided_at=decided_at,
        )
    )
    db.commit()
    db.refresh(report)
    return report


def to_persisted_response(report: Report) -> PersistedReportResponse:
    """Convert an ORM report to the stable API response contract."""
    audit_logs = [
        AuditLogResponse(
            id=log.id,
            suggestion_id=log.suggestion_id,
            decision=cast(Decision, log.decision),
            decided_at=log.decided_at.isoformat(),
        )
        for log in report.audit_logs
    ]
    suggestions = [
        PersistedSuggestion(
            id=suggestion.id,
            section=suggestion.section,
            explanation=suggestion.explanation,
            guideline_passage=suggestion.guideline_passage,
            source_url=suggestion.source_url,
            decision=(
                cast(Decision, suggestion.decision)
                if suggestion.decision is not None
                else None
            ),
            decided_at=(
                suggestion.decided_at.isoformat()
                if suggestion.decided_at is not None
                else None
            ),
        )
        for suggestion in report.suggestions
    ]
    return PersistedReportResponse(
        id=report.id,
        filename=report.filename,
        diagnosis=report.diagnosis,
        status=report.status,
        message=report.message,
        completeness_score=report.completeness_score,
        created_at=report.created_at.isoformat(),
        suggestions=suggestions,
        audit_logs=audit_logs,
    )
