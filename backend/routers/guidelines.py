"""FastAPI router for clinical guideline documents and evidence metadata."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.services.guidelines import (
    DEFAULT_GUIDELINES_DIR,
    get_guideline_metadata,
    resolve_guideline_document,
)

router = APIRouter(prefix="/guidelines", tags=["guidelines"])


@router.get("")
def list_guidelines() -> list[dict[str, Any]]:
    """List available clinical guidelines in the knowledge base."""
    guidelines: list[dict[str, Any]] = []
    if not DEFAULT_GUIDELINES_DIR.exists():
        return guidelines

    for folder in sorted(DEFAULT_GUIDELINES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        metadata = get_guideline_metadata(folder.name)
        if metadata:
            guidelines.append(
                {
                    "diagnosis": metadata.get("diagnosis", folder.name),
                    "diagnosis_slug": folder.name,
                    "synonyms": metadata.get("synonyms", []),
                    "document_count": len(metadata.get("documents", [])),
                }
            )
    return guidelines


@router.get("/{diagnosis_slug}/metadata")
def guideline_metadata(diagnosis_slug: str) -> dict[str, Any]:
    """Return the authoritative metadata record for a diagnosis."""
    metadata = get_guideline_metadata(diagnosis_slug)
    if not metadata:
        raise HTTPException(
            status_code=404,
            detail=f"Guideline metadata not found for diagnosis '{diagnosis_slug}'.",
        )
    return metadata


@router.get("/{diagnosis_slug}/document")
def get_guideline_document(
    diagnosis_slug: str,
    filename: str | None = Query(None, description="Specific document filename to retrieve"),
    source_url: str | None = Query(None, description="Source URL associated with the chunk"),
) -> FileResponse:
    """Serve the original guideline document file (PDF/DOCX/MD) for clinical review."""
    result = resolve_guideline_document(
        diagnosis_slug,
        source_url=source_url or "",
        filename=filename,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Guideline document not found for '{diagnosis_slug}'.",
        )

    file_path, _ = result
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        media_type = "application/pdf"
    elif suffix in {".doc", ".docx"}:
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    elif suffix in {".md", ".txt"}:
        media_type = "text/plain; charset=utf-8"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
        headers={"Content-Disposition": f'inline; filename="{file_path.name}"'},
    )
