"""File validation, text extraction, and provider orchestration."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

from backend.llm.provider import LLMProvider
from backend.models.schemas import DischargeExtraction
from backend.observability.tracing import observation

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def _sanitize_text(text: str) -> str:
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    return "\n".join(line.strip() for line in cleaned.splitlines()).strip()


def _extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension == ".txt":
        return _sanitize_text(content.decode("utf-8"))
    if extension == ".pdf":
        reader = PdfReader(BytesIO(content))
        return _sanitize_text("\n".join(page.extract_text() or "" for page in reader.pages))
    if extension == ".docx":
        document = Document(BytesIO(content))
        return _sanitize_text("\n".join(paragraph.text for paragraph in document.paragraphs))
    raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")


async def extract_upload(upload: UploadFile, provider: LLMProvider) -> DischargeExtraction:
    """Validate an upload, extract text, and call the configured provider."""
    _, extraction = await extract_upload_document(upload, provider)
    return extraction


async def extract_upload_document(
    upload: UploadFile, provider: LLMProvider
) -> tuple[str, DischargeExtraction]:
    """Return sanitized source text and its structured extraction."""
    filename = upload.filename or ""
    file_type = Path(filename).suffix.lower()
    with observation(
        "extract-discharge-document",
        input_data={"file_type": file_type, "max_upload_bytes": MAX_UPLOAD_BYTES},
    ) as trace:
        if file_type not in SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")
        content = await upload.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError("File exceeds the 5 MB upload limit.")
        text = _extract_text(filename, content)
        if not text:
            raise ValueError("The uploaded document contains no readable text.")
        extraction = provider.extract_discharge(text)
        trace.update(
            {
                "success": True,
                "source_character_count": len(text),
                "medication_count": len(extraction.medications),
                "follow_up_count": len(extraction.follow_up_requirements),
                "warning_sign_count": len(extraction.warning_signs),
            }
        )
        return text, extraction