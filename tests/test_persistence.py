from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import Base, get_db
from backend.main import app
from backend.models.database import Report
from backend.models.schemas import DischargeExtraction
from backend.rag.workflow import review_extraction as run_review
from backend.routers import discharge
from backend.routers.discharge import get_llm_provider
from knowledge_base.ingest import build_index


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    target = tmp_path / "index"
    build_index(Path("knowledge_base/guidelines"), target)
    return target


@pytest.fixture
def database() -> Generator[Session, None, None]:
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


def test_review_decision_cycle_is_persisted_and_retrievable(
    monkeypatch: pytest.MonkeyPatch,
    index_dir: Path,
    database: Session,
) -> None:
    class FakeProvider:
        def extract_discharge(self, text: str) -> DischargeExtraction:
            return DischargeExtraction(diagnosis="Asthma")

    def override_get_db() -> Generator[Session, None, None]:
        yield database

    monkeypatch.setattr(
        discharge,
        "review_extraction",
        lambda extraction: run_review(extraction, index_dir),
    )
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_provider] = FakeProvider
    try:
        client = TestClient(app)
        review_response = client.post(
            "/discharge/review",
            files={"file": ("summary.txt", b"Synthetic case", "text/plain")},
        )
        assert review_response.status_code == 200
        review = review_response.json()
        assert review["report_id"] is not None
        assert review["suggestions"]

        report_id = review["report_id"]
        suggestion_id = review["suggestions"][0]["suggestion_id"]
        retrieved = client.get(f"/discharge/reports/{report_id}")
        assert retrieved.status_code == 200
        assert retrieved.json()["id"] == report_id
        assert retrieved.json()["audit_logs"] == []

        decision = client.post(
            f"/discharge/reports/{report_id}/suggestions/{suggestion_id}/decision",
            json={"decision": "accepted"},
        )
        assert decision.status_code == 200
        body = decision.json()
        selected = next(
            item for item in body["suggestions"] if item["id"] == suggestion_id
        )
        assert selected["decision"] == "accepted"
        assert selected["decided_at"]
        assert body["audit_logs"]
        assert body["audit_logs"][0]["decision"] == "accepted"

        persisted = database.get(Report, report_id)
        assert persisted is not None
        assert persisted.suggestions[0].decision == "accepted"
    finally:
        app.dependency_overrides.clear()


def test_report_and_decision_routes_reject_missing_records() -> None:
    client = TestClient(app)

    assert client.get("/discharge/reports/999999").status_code == 404
    response = client.post(
        "/discharge/reports/999999/suggestions/999999/decision",
        json={"decision": "accepted"},
    )
    assert response.status_code == 404
