"""Run a synthetic review-to-export and verify its hosted Langfuse trace."""

from __future__ import annotations

import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from langfuse import get_client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import (
    get_ollama_base_url,
    get_ollama_model,
    is_langfuse_configured,
)
from backend.db import Base, get_db
from backend.llm.provider import OllamaProvider
from backend.main import app
from backend.models.database import Report
from backend.models.schemas import DischargeExtraction
from backend.rag.workflow import review_extraction as run_review
from backend.routers import discharge
from backend.routers.discharge import get_llm_provider
from knowledge_base.ingest import build_index

REQUIRED_OBSERVATIONS = {
    "review-discharge-document",
    "extract-discharge-document",
    "extract-structured-fields",
    "retrieve-guideline",
    "compare-discharge-sections",
    "score-completeness",
    "export-reviewed-document",
    "structure-reviewed-document",
    "verify-original-content-presence",
}


def main() -> None:
    if not is_langfuse_configured():
        raise SystemExit(
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to verify a real trace."
        )

    started_at = datetime.now(UTC)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    database = session_factory()
    original_review = discharge.review_extraction

    def override_get_db():
        yield database

    with tempfile.TemporaryDirectory(prefix="clinical-eval-") as temp_dir:
        index_dir = Path(temp_dir) / "index"
        build_index(Path("knowledge_base/guidelines"), index_dir)

        def review_with_test_index(extraction: DischargeExtraction):
            return run_review(extraction, index_dir)

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_llm_provider] = lambda: OllamaProvider(
            get_ollama_base_url(), get_ollama_model()
        )
        discharge.review_extraction = review_with_test_index
        try:
            with TestClient(app) as client:
                created = client.post(
                    "/reviews",
                    files={
                        "file": (
                            "synthetic-summary.txt",
                            (
                                "Synthetic case. Patient is 42 years old. "
                                "Diagnosis: Asthma. Medication: Salbutamol inhaler. "
                                "Follow-up: Review in 7 days. "
                                "Warning signs: Worsening breathing."
                            ),
                            "text/plain",
                        )
                    },
                )
                if created.status_code != 200:
                    raise RuntimeError(
                        f"Synthetic review failed: HTTP {created.status_code}"
                    )
                report_id = int(created.json()["report_id"])
                exported = client.post(
                    f"/reviews/{report_id}/export", params={"format": "txt"}
                )
                if exported.status_code != 200:
                    raise RuntimeError(
                        f"Synthetic export failed: HTTP {exported.status_code}"
                    )

            report = database.get(Report, report_id)
            if report is None or not report.langfuse_trace_id:
                raise AssertionError("The report did not persist a Langfuse trace ID.")

            langfuse = get_client()
            langfuse.flush()
            deadline = time.monotonic() + 45
            observations = []
            while time.monotonic() < deadline:
                page = langfuse.api.observations.get_many(
                    trace_id=report.langfuse_trace_id,
                    fields="core,basic",
                    limit=100,
                    from_start_time=started_at - timedelta(minutes=1),
                    to_start_time=datetime.now(UTC) + timedelta(minutes=1),
                )
                observations = page.data
                names = {item.name for item in observations if item.name}
                if REQUIRED_OBSERVATIONS <= names:
                    print(f"Verified Langfuse trace: {report.langfuse_trace_id}")
                    print("Verified observations: " + ", ".join(sorted(names)))
                    return
                time.sleep(2)

            names = {item.name for item in observations if item.name}
            missing = sorted(REQUIRED_OBSERVATIONS - names)
            raise AssertionError(
                "Langfuse trace is missing required observations: "
                + ", ".join(missing)
            )
        finally:
            app.dependency_overrides.clear()
            discharge.review_extraction = original_review
            database.close()
            engine.dispose()


if __name__ == "__main__":
    main()
