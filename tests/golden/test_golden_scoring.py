import json
from pathlib import Path

from backend.models.schemas import DischargeExtraction, ReviewResponse
from backend.rag.workflow import review_extraction
from knowledge_base.ingest import build_index

CASES_PATH = Path(__file__).with_name("scoring_cases.json")


def test_golden_scoring_is_repeatable_and_guarded(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    build_index(Path("knowledge_base/guidelines"), index_dir)
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    for case in cases:
        extraction = DischargeExtraction.model_validate(case["extraction"])
        first = review_extraction(extraction, index_dir)
        second = review_extraction(extraction, index_dir)
        first_json = ReviewResponse.model_validate(first).model_dump_json()
        second_json = ReviewResponse.model_validate(second).model_dump_json()

        assert first_json == second_json, case["name"]
        assert first.completeness_score == case["expected_score"]
        assert [item.section for item in first.suggestions] == case[
            "expected_suggestion_sections"
        ]
        assert all(
            suggestion.guideline_passage and suggestion.source_url
            for suggestion in first.suggestions
        )
