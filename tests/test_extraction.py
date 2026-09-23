import json
from io import BytesIO
from pathlib import Path
from typing import Self

import pytest
from docx import Document
from fastapi import UploadFile
from fastapi.testclient import TestClient

from backend.llm.provider import OllamaProvider
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


class TextCheckingProvider:
    def __init__(self, expected_text: str) -> None:
        self.expected_text = expected_text

    def extract_discharge(self, text: str) -> DischargeExtraction:
        assert self.expected_text in text
        return DischargeExtraction(diagnosis="Verified diagnosis")


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


@pytest.mark.anyio
async def test_extract_upload_uses_real_docx_text_extraction() -> None:
    document = Document()
    document.add_paragraph("DOCX clinical content")
    output = BytesIO()
    document.save(output)
    output.seek(0)

    result = await extract_upload(
        UploadFile(filename="summary.docx", file=output),
        TextCheckingProvider("DOCX clinical content"),
    )

    assert result.diagnosis == "Verified diagnosis"


@pytest.mark.anyio
async def test_extract_upload_uses_real_pdf_text_extraction() -> None:
    pdf_path = next(
        Path("knowledge_base/guidelines/asthma").glob(
            "Guidelines for diagnosis and management of bronchial asthma.pdf"
        )
    )
    result = await extract_upload(
        UploadFile(filename=pdf_path.name, file=BytesIO(pdf_path.read_bytes())),
        TextCheckingProvider("bronchial asthma"),
    )

    assert result.diagnosis == "Verified diagnosis"


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


def test_ollama_provider_sends_zero_temperature_and_retries_invalid_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        {"response": "not json"},
        {
            "response": json.dumps(
                {
                    "diagnosis": "Asthma",
                    "medications": [],
                    "follow_up_requirements": [],
                    "warning_signs": [],
                }
            )
        },
    ]
    requests: list[dict[str, object]] = []

    class FakeResponse:
        def __init__(self, payload: dict[str, str]) -> None:
            self.payload = payload

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(self.payload).encode("utf-8")

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        requests.append(json.loads(request.data.decode("utf-8")))  # type: ignore[attr-defined]
        return FakeResponse(responses.pop(0))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = OllamaProvider("http://localhost:11434", "llama3.2:3b").extract_discharge(
        "Synthetic case"
    )

    assert result.diagnosis == "Asthma"
    assert len(requests) == 2
    assert all(request["options"] == {"temperature": 0.0} for request in requests)


def test_ollama_provider_fails_after_bounded_validation_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"response":"not json"}'

    attempts = 0

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        nonlocal attempts
        attempts += 1
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    provider = OllamaProvider("http://localhost:11434", "llama3.2:3b")

    with pytest.raises(RuntimeError, match="after 3 attempts"):
        provider.extract_discharge("Synthetic case")
    assert attempts == 3