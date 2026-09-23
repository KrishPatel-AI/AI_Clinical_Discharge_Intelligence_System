"""Persistence services for review reports and doctor decisions."""

from datetime import UTC, datetime
from typing import Literal, cast

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.models.database import AuditLog, Report, SuggestionRecord, User
from backend.models.schemas import (
    AuditLogResponse,
    PersistedReportResponse,
    PersistedSuggestion,
    ReviewHistoryResponse,
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


def create_report(
    db: Session, filename: str, review: ReviewResponse, source_text: str = ""
) -> Report:
    """Persist a generated review and all of its grounded suggestions."""
    report = Report(
        user=_get_or_create_user(db),
        filename=filename,
        diagnosis=review.diagnosis,
        status=review.status,
        message=review.message,
        source_text=source_text,
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


def update_suggestion_status(
    db: Session, report_id: int, suggestion_id: int, status: str
) -> Report | None:
    """Apply one live status update and append a corresponding audit record."""
    decision = {"pending": None, "accepted": "accepted", "rejected": "ignored"}[status]
    report = find_report(db, report_id)
    if report is None:
        return None
    suggestion = next(
        (item for item in report.suggestions if item.id == suggestion_id), None
    )
    if suggestion is None:
        return None
    suggestion.decision = decision
    suggestion.decided_at = None if decision is None else datetime.now(UTC)
    if decision is not None:
        report.audit_logs.append(
            AuditLog(
                suggestion_id=suggestion.id,
                decision=decision,
                decided_at=suggestion.decided_at,
            )
        )
    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session,
    search: str | None,
    status: str | None,
    sort: str,
    group_by: str | None,
    offset: int,
    limit: int,
) -> ReviewHistoryResponse:
    """Return server-filtered, ordered, and paginated review history."""
    statement = select(Report)
    count_statement = select(func.count(Report.id))
    if search:
        pattern = f"%{search}%"
        condition = or_(
            Report.filename.ilike(pattern),
            Report.diagnosis.ilike(pattern),
            Report.message.ilike(pattern),
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if status:
        statement = statement.where(Report.status == status)
        count_statement = count_statement.where(Report.status == status)
    if sort == "oldest":
        statement = statement.order_by(Report.created_at.asc())
    elif sort == "score":
        statement = statement.order_by(Report.completeness_score.desc())
    else:
        statement = statement.order_by(Report.created_at.desc())
    total = int(db.scalar(count_statement) or 0)
    reports = list(db.scalars(statement.offset(offset).limit(limit)).all())
    groups: dict[str, list[int]] | None = None
    if group_by in {"diagnosis", "status"}:
        groups = {}
        for report in reports:
            key = report.diagnosis if group_by == "diagnosis" else report.status
            groups.setdefault(key, []).append(report.id)
    return ReviewHistoryResponse(
        reviews=[to_persisted_response(report) for report in reports],
        total=total,
        offset=offset,
        limit=limit,
        groups=groups,
    )


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
            status=(
                "accepted"
                if suggestion.decision == "accepted"
                else "rejected"
                if suggestion.decision == "ignored"
                else "pending"
            ),
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
