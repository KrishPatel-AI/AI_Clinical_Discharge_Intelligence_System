from io import BytesIO

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import DischargeExtraction
from backend.routers.discharge import get_llm_provider
from backend.services.extraction import extract_upload


class FakeProvider:
    def extract_discharge(self, text: str) -> DischargeExtraction:
        assert "Synthetic case" in text
        return DischargeExtraction(
            diagnosis="Synthetic diagnosis",
            medications=["Example medicine"],
            follow_up_requirements=["Follow up in seven days"],
            warning_signs=["Seek care for worsening symptoms"],
        )


@pytest.mark.anyio
async def test_extract_upload_accepts_text_and_returns_schema() -> None:
    upload = UploadFile(filename="summary.txt", file=BytesIO(b"Synthetic case\nNo real patient data."))

    result = await extract_upload(upload, FakeProvider())

    assert result.diagnosis == "Synthetic diagnosis"
    assert result.medications == ["Example medicine"]


@pytest.mark.anyio
async def test_extract_upload_rejects_unsupported_type() -> None:
    upload = UploadFile(filename="summary.exe", file=BytesIO(b"Synthetic case"))

    with pytest.raises(ValueError, match="Unsupported file type"):
        await extract_upload(upload, FakeProvider())


def test_extract_endpoint_returns_structured_response() -> None:
    app.dependency_overrides[get_llm_provider] = FakeProvider
    client = TestClient(app)

    try:
        response = client.post(
            "/discharge/extract",
            files={"file": ("summary.txt", b"Synthetic case", "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["extraction"]["diagnosis"] == "Synthetic diagnosis"