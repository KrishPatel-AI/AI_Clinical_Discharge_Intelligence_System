"""Tests for clinical guideline document resolution and serving."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.guidelines import (
    find_guideline_directory,
    get_guideline_metadata,
    resolve_guideline_document,
    resolve_guideline_info,
)

client = TestClient(app)


def test_find_guideline_directory_matches_slug_and_name() -> None:
    folder = find_guideline_directory("asthma")
    assert folder is not None
    assert folder.name == "asthma"

    folder_name = find_guideline_directory("Asthma")
    assert folder_name is not None
    assert folder_name.name == "asthma"

    diabetes_folder = find_guideline_directory("Diabetes mellitus")
    assert diabetes_folder is not None
    assert diabetes_folder.name == "diabetes"

    hbp_folder = find_guideline_directory("Hypertension")
    assert hbp_folder is not None
    assert hbp_folder.name == "high-blood-pressure"


def test_get_guideline_metadata_returns_valid_structure() -> None:
    meta = get_guideline_metadata("asthma")
    assert meta is not None
    assert meta["diagnosis_slug"] == "asthma"
    assert "documents" in meta
    assert len(meta["documents"]) >= 2
    assert any(doc["filename"].endswith(".pdf") for doc in meta["documents"])


def test_resolve_guideline_document_returns_actual_file() -> None:
    result = resolve_guideline_document("asthma")
    assert result is not None
    file_path, doc_meta = result
    assert file_path.is_file()
    assert file_path.suffix.lower() == ".pdf"
    assert doc_meta.get("filename") is not None


def test_resolve_guideline_info_provides_usable_url() -> None:
    info = resolve_guideline_info("asthma")
    assert info["diagnosis_slug"] == "asthma"
    assert info["document_title"] is not None
    assert info["guideline_document_url"] is not None
    assert info["guideline_document_url"].startswith("/guidelines/asthma/document")


def test_guidelines_endpoint_lists_all_knowledge_base_guidelines() -> None:
    response = client.get("/guidelines")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    slugs = [item["diagnosis_slug"] for item in data]
    assert "asthma" in slugs
    assert "diabetes" in slugs
    assert "high-blood-pressure" in slugs


def test_guideline_metadata_endpoint_returns_data_or_404() -> None:
    response = client.get("/guidelines/asthma/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["diagnosis"] == "Asthma"
    assert "documents" in data

    missing = client.get("/guidelines/non-existent-disease/metadata")
    assert missing.status_code == 404


def test_guideline_document_endpoint_serves_pdf_file() -> None:
    response = client.get("/guidelines/asthma/document")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "filename=" in response.headers.get("content-disposition", "")
    assert len(response.content) > 1000

    diabetes_response = client.get("/guidelines/diabetes/document")
    assert diabetes_response.status_code == 200
    assert diabetes_response.headers["content-type"] == "application/pdf"

    hbp_response = client.get("/guidelines/high-blood-pressure/document")
    assert hbp_response.status_code == 200
    assert hbp_response.headers["content-type"] == "application/pdf"


def test_guideline_document_rejects_path_traversal() -> None:
    response = client.get("/guidelines/asthma/document?filename=../../main.py")
    assert response.status_code == 404
