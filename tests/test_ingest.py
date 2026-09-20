from pathlib import Path

import pytest

from knowledge_base.ingest import build_index, query_index


def test_build_index_is_idempotent_and_queryable(tmp_path: Path) -> None:
    guidelines_dir = Path("knowledge_base/guidelines")

    first_count = build_index(guidelines_dir, tmp_path / "index")
    second_count = build_index(guidelines_dir, tmp_path / "index")
    result = query_index("asthma symptoms", tmp_path / "index")

    assert first_count > 0
    assert second_count == first_count
    assert result["documents"]
    assert any(metadata["diagnosis"] == "Asthma" for metadata in result["metadatas"])


def test_build_index_rejects_empty_guideline_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No guideline XML files"):
        build_index(tmp_path / "empty", tmp_path / "index")
