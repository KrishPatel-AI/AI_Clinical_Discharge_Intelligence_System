from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import DischargeExtraction, ReviewResponse
from backend.rag.workflow import review_extraction
from backend.routers import discharge
from backend.routers.discharge import get_llm_provider
from knowledge_base.ingest import build_index


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    target = tmp_path / "index"
    build_index(Path("knowledge_base/guidelines"), target)
    return target


def test_review_retrieves_guideline_and_compares_sections(index_dir: Path) -> None:
    result = review_extraction(
        DischargeExtraction(
            diagnosis="Asthma",
            medications=["Example inhaler"],
            follow_up_requirements=["Follow up with the doctor"],
            warning_signs=["Worsening breathing"],
        ),
        index_dir,
    )

    assert result.status == "matched"
    assert result.guideline is not None
    assert result.guideline.diagnosis_slug == "asthma"
    assert result.comparisons
    assert {item.status for item in result.comparisons} <= {"matched", "gap"}
    assert result.completeness_score is not None
    assert 0 <= result.completeness_score <= 100
    assert result.suggestions
    assert all(
        suggestion.guideline_passage and suggestion.source_url
        for suggestion in result.suggestions
    )


def test_review_scores_complete_summary_without_suggestions(index_dir: Path) -> None:
    result = review_extraction(
        DischargeExtraction(
            diagnosis="Asthma",
            medications=["Asthma"],
            follow_up_requirements=["Asthma"],
            warning_signs=["Asthma"],
        ),
        index_dir,
    )

    assert result.status == "matched"
    assert result.completeness_score == 100
    assert result.suggestions == []


def test_review_reports_no_match_without_comparisons(index_dir: Path) -> None:
    result = review_extraction(
        DischargeExtraction(diagnosis="Rare neurological disorder"), index_dir
    )

    assert result.status == "no_match"
    assert result.guideline is None
    assert result.comparisons == []
    assert result.completeness_score is None
    assert result.suggestions == []
    assert "No matching guideline" in result.message


def test_review_endpoint_returns_workflow_result(
    monkeypatch: pytest.MonkeyPatch, index_dir: Path
) -> None:
    class FakeProvider:
        def extract_discharge(self, text: str) -> DischargeExtraction:
            return DischargeExtraction(diagnosis="Asthma")

    monkeypatch.setattr(
        discharge,
        "review_extraction",
        lambda extraction: review_extraction(extraction, index_dir),
    )

    app.dependency_overrides[get_llm_provider] = FakeProvider
    try:
        response = TestClient(app).post(
            "/discharge/review",
            files={"file": ("summary.txt", b"Synthetic case", "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    result = ReviewResponse.model_validate(response.json())
    assert result.status == "matched"
    assert result.completeness_score is not None
    assert result.suggestions
    assert all(
        suggestion.guideline_passage and suggestion.source_url
        for suggestion in result.suggestions
    )


def test_review_endpoint_rejects_unsupported_upload() -> None:
    class FakeProvider:
        def extract_discharge(self, text: str) -> DischargeExtraction:
            return DischargeExtraction(diagnosis="Asthma")

    app.dependency_overrides[get_llm_provider] = FakeProvider
    try:
        response = TestClient(app).post(
            "/discharge/review",
            files={"file": ("summary.exe", BytesIO(b"Synthetic case"), "application/octet-stream")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400