import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.formatting.structuring import (
    structure_document,
    verify_content_presence,
)
from backend.main import app
from backend.models.database import Report
from backend.models.schemas import DischargeExtraction
from backend.routers import discharge
from backend.routers.discharge import get_llm_provider
from knowledge_base.ingest import build_index


@pytest.fixture
def index_dir(tmp_path):
    target = tmp_path / "index"
    build_index(__import__("pathlib").Path("knowledge_base/guidelines"), target)
    return target


@pytest.fixture
def database() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_structure_document_keeps_original_text_and_labels_accepted_suggestions() -> None:
    source_text = (
        "Patient is 42 years old. Diagnosis is asthma. "
        "The patient was prescribed inhaler therapy. Follow-up in 7 days."
    )
    accepted = [
        type(
            "Suggestion",
            (),
            {"explanation": "Continue inhaler use and review symptoms after 1 week."},
        )()
    ]

    structured = structure_document(source_text, accepted)

    assert "Patient Information" in structured
    assert "Diagnosis" in structured
    assert "Follow-up" in structured
    assert "Added on review" in structured
    assert "Continue inhaler use" in structured
    assert "Patient is 42 years old." in structured
    assert "Diagnosis is asthma." in structured


def test_verify_content_presence_detects_missing_sentence() -> None:
    original = "Patient is stable. Needs follow-up in one week."
    structured = "Patient is stable."

    assert verify_content_presence(original, structured) is False


def test_export_route_formats_content_and_marks_exported(
    monkeypatch, index_dir, database: Session
) -> None:
    class FakeProvider:
        def extract_discharge(self, text: str) -> DischargeExtraction:
            return DischargeExtraction(diagnosis="Asthma")

    def override_get_db():
        yield database

    monkeypatch.setattr(
        discharge,
        "review_extraction",
        lambda extraction: __import__("backend.rag.workflow", fromlist=["review_extraction"]).review_extraction(extraction, index_dir),
    )
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_provider] = FakeProvider
    try:
        created = TestClient(app).post(
            "/reviews",
            files={"file": ("summary.txt", b"Patient is 42 years old. Diagnosis is asthma.", "text/plain")},
        )
        assert created.status_code == 200
        report_id = created.json()["report_id"]
        if created.json()["suggestions"]:
            suggestion_id = created.json()["suggestions"][0]["suggestion_id"]
            patch = TestClient(app).patch(
                f"/reviews/{report_id}/suggestions/{suggestion_id}",
                json={"status": "accepted"},
            )
            assert patch.status_code == 200

        exported = TestClient(app).post(f"/reviews/{report_id}/export", params={"format": "txt"})
        assert exported.status_code == 200
        body = exported.json()
        assert body["exported"] is True
        assert "Patient Information" in body["content"] or "Diagnosis" in body["content"]
        stored = database.get(Report, report_id)
        assert stored is not None
        assert any(log.decision == "exported" for log in stored.audit_logs)
    finally:
        app.dependency_overrides.clear()
