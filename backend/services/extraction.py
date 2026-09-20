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
    filename = upload.filename or ""
    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 5 MB upload limit.")
    text = _extract_text(filename, content)
    if not text:
        raise ValueError("The uploaded document contains no readable text.")
    return provider.extract_discharge(text)