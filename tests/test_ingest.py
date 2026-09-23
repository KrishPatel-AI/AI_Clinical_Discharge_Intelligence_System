from pathlib import Path

import pytest

from knowledge_base.ingest import build_index, query_index


def test_build_index_is_idempotent_and_queryable(tmp_path: Path) -> None:
    guidelines_dir = Path("knowledge_base/guidelines")

    first_count = build_index(guidelines_dir, tmp_path / "index")
    second_count = build_index(guidelines_dir, tmp_path / "index")
    result = query_index("bronchial asthma diagnosis", tmp_path / "index")

    assert first_count > 0
    assert second_count == first_count
    assert result["documents"]
    assert any(
        metadata["diagnosis_slug"] == "asthma"
        and metadata["source_file"].endswith(".md")
        for metadata in result["metadatas"]
    )


def test_build_index_ingests_verified_markdown_diagnoses(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    count = build_index(Path("knowledge_base/guidelines"), index_dir)

    assert count > 0
    records = __import__("json").loads(
        (index_dir / "metadata.json").read_text(encoding="utf-8")
    )
    diagnoses = {record["metadata"]["diagnosis_slug"] for record in records}
    assert diagnoses == {"asthma", "diabetes", "high-blood-pressure"}
    assert all(record["metadata"]["source_file"].endswith(".md") for record in records)
    assert any(
        record["metadata"]["source_file"] == "1725952329_pulmonology_asthma.md"
        for record in records
    )
    assert all(record["metadata"]["source_url"] for record in records)
    assert not any(
        "ICMR_Guidelines_for_Management_of_Type_1_Diabetes.md"
        == record["metadata"]["source_file"]
        and "�" in record["document"]
        for record in records
    )


def test_build_index_rejects_empty_guideline_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No guideline Markdown or XML files"):
        build_index(tmp_path / "empty", tmp_path / "index")
