"""Guideline document inspection and serving services."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

DEFAULT_GUIDELINES_DIR = (
    Path(__file__).resolve().parent.parent.parent / "knowledge_base" / "guidelines"
)


def find_guideline_directory(
    diagnosis_or_slug: str, guidelines_dir: Path = DEFAULT_GUIDELINES_DIR
) -> Path | None:
    """Locate the guideline directory matching a diagnosis slug, name, or synonym."""
    if not guidelines_dir.exists():
        return None

    normalized_input = diagnosis_or_slug.strip().lower().replace(" ", "-")

    direct_dir = guidelines_dir / normalized_input
    if direct_dir.is_dir():
        return direct_dir

    raw_dir = guidelines_dir / diagnosis_or_slug.strip()
    if raw_dir.is_dir():
        return raw_dir

    target_tokens = set(diagnosis_or_slug.lower().replace("-", " ").split())

    best_match: Path | None = None
    best_overlap = 0

    for candidate in sorted(guidelines_dir.iterdir()):
        if not candidate.is_dir():
            continue
        metadata_file = candidate / "metadata.json"
        if not metadata_file.exists():
            continue
        try:
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        diag_name = str(data.get("diagnosis", "")).lower()
        synonyms = [str(s).lower() for s in data.get("synonyms", [])]

        if diagnosis_or_slug.lower() == diag_name or diagnosis_or_slug.lower() in synonyms:
            return candidate

        candidate_tokens = set(diag_name.replace("-", " ").split())
        for syn in synonyms:
            candidate_tokens.update(syn.replace("-", " ").split())

        overlap = len(target_tokens & candidate_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = candidate

    return best_match


def get_guideline_metadata(
    diagnosis_or_slug: str, guidelines_dir: Path = DEFAULT_GUIDELINES_DIR
) -> dict[str, Any] | None:
    """Return the parsed metadata.json for the matching diagnosis."""
    folder = find_guideline_directory(diagnosis_or_slug, guidelines_dir)
    if folder is None:
        return None
    metadata_file = folder / "metadata.json"
    if not metadata_file.exists():
        return None
    try:
        data = json.loads(metadata_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        data["diagnosis_slug"] = folder.name
        return dict(data)
    except (json.JSONDecodeError, OSError):
        return None


def resolve_guideline_document(
    diagnosis_or_slug: str,
    source_url: str = "",
    filename: str | None = None,
    guidelines_dir: Path = DEFAULT_GUIDELINES_DIR,
) -> tuple[Path, dict[str, Any]] | None:
    """Find the specific guideline document file and its metadata record."""
    folder = find_guideline_directory(diagnosis_or_slug, guidelines_dir)
    if folder is None:
        return None

    metadata = get_guideline_metadata(folder.name, guidelines_dir) or {}
    documents: list[dict[str, Any]] = metadata.get("documents", [])

    if filename:
        if ".." in filename or "/" in filename or "\\" in filename:
            return None
        clean_filename = Path(filename).name
        target_path = (folder / clean_filename).resolve()
        try:
            target_path.relative_to(folder.resolve())
        except ValueError:
            return None
        if target_path.is_file():
            matching_doc = next(
                (d for d in documents if d.get("filename") == clean_filename),
                {"filename": clean_filename, "title": clean_filename},
            )
            return target_path, matching_doc
        return None

    if source_url:
        for doc in documents:
            if doc.get("source_url") == source_url:
                doc_file = folder / str(doc.get("filename", ""))
                if doc_file.is_file():
                    return doc_file, doc

    for doc in documents:
        doc_filename = str(doc.get("filename", ""))
        if doc_filename.lower().endswith(".pdf"):
            doc_file = folder / doc_filename
            if doc_file.is_file():
                return doc_file, doc

    for doc in documents:
        doc_file = folder / str(doc.get("filename", ""))
        if doc_file.is_file():
            return doc_file, doc

    for ext in ["*.pdf", "*.docx", "*.md"]:
        for file in sorted(folder.glob(ext)):
            if file.is_file():
                return file, {"filename": file.name, "title": file.stem}

    return None


def resolve_guideline_info(
    diagnosis_or_slug: str,
    source_url: str = "",
    guidelines_dir: Path = DEFAULT_GUIDELINES_DIR,
) -> dict[str, str | None]:
    """Return presentation and linking metadata for the guideline document."""
    res = resolve_guideline_document(
        diagnosis_or_slug, source_url=source_url, guidelines_dir=guidelines_dir
    )
    if not res:
        return {
            "diagnosis_slug": None,
            "document_title": None,
            "document_filename": None,
            "source_name": None,
            "guideline_document_url": None,
        }
    path, doc = res
    folder_name = path.parent.name
    doc_title = str(doc.get("title") or path.stem)
    doc_filename = path.name
    source_name = doc.get("source_name")
    encoded_filename = quote(doc_filename)
    document_url = f"/guidelines/{folder_name}/document?filename={encoded_filename}"

    return {
        "diagnosis_slug": folder_name,
        "document_title": doc_title,
        "document_filename": doc_filename,
        "source_name": str(source_name) if source_name else None,
        "guideline_document_url": document_url,
    }
