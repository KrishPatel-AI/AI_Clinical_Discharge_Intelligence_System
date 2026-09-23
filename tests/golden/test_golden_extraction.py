import json
from pathlib import Path

from backend.models.schemas import DischargeExtraction

CASES_PATH = Path(__file__).with_name("extraction_cases.json")


def test_golden_extraction_contract_is_stable() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    for case in cases:
        expected = DischargeExtraction.model_validate(case["expected"])
        first = expected.model_dump_json()
        second = DischargeExtraction.model_validate_json(first).model_dump_json()
        assert first == second, case["name"]
        assert case["document"]
