from io import BytesIO

import pytest
from docx import Document
from fastapi.testclient import TestClient
from pypdf import PdfReader
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


def test_preview_returns_source_text_without_recording_export(
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

        preview = TestClient(app).get(
            f"/reviews/{report_id}/preview", params={"format": "txt"}
        )
        assert preview.status_code == 200
        body = preview.json()
        assert body["exported"] is False
        assert body["content"] == "Patient is 42 years old. Diagnosis is asthma."
        assert "Patient Information" not in body["content"]
        assert "Added on review" not in body["content"]
        stored = database.get(Report, report_id)
        assert stored is not None
        assert not any(log.decision == "exported" for log in stored.audit_logs)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("output_format", "media_type"),
    [
        ("txt", "text/plain"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("pdf", "application/pdf"),
    ],
)
def test_export_returns_downloadable_file_and_records_export(
    monkeypatch,
    index_dir,
    database: Session,
    output_format: str,
    media_type: str,
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
        client = TestClient(app)
        created = client.post(
            "/reviews",
            files={"file": ("summary.txt", b"Patient is 42 years old. Diagnosis is asthma.", "text/plain")},
        )
        assert created.status_code == 200
        report_id = created.json()["report_id"]
        suggestions = created.json()["suggestions"]
        if suggestions:
            accepted = client.patch(
                f"/reviews/{report_id}/suggestions/{suggestions[0]['suggestion_id']}",
                json={"status": "accepted"},
            )
            assert accepted.status_code == 200

        exported = client.post(
            f"/reviews/{report_id}/export", params={"format": output_format}
        )
        assert exported.status_code == 200
        assert exported.headers["content-type"].startswith(media_type)
        assert exported.headers["content-disposition"].endswith(
            f'"review-{report_id}.{output_format}"'
        )

        if output_format == "txt":
            content = exported.content.decode("utf-8")
        elif output_format == "docx":
            document = Document(BytesIO(exported.content))
            content = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            content = "\n".join(
                page.extract_text() or "" for page in PdfReader(BytesIO(exported.content)).pages
            )

        assert "Patient Information" in content or "Diagnosis" in content
        assert "Patient is 42 years old." in content
        assert ("Added on review" in content) == bool(suggestions)
        stored = database.get(Report, report_id)
        assert stored is not None
        assert any(log.decision == "exported" for log in stored.audit_logs)
    finally:
        app.dependency_overrides.clear()
