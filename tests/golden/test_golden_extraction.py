import json
import os
from pathlib import Path

import pytest

from backend.config import get_ollama_base_url, get_ollama_model
from backend.llm.provider import OllamaProvider
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


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_GOLDEN") != "1",
    reason="set RUN_LIVE_GOLDEN=1 to run the pinned local Ollama golden checks",
)
def test_live_ollama_extraction_matches_and_repeats_golden_cases() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    provider = OllamaProvider(get_ollama_base_url(), get_ollama_model())

    for case in cases:
        expected = DischargeExtraction.model_validate(case["expected"])
        first = provider.extract_discharge(case["document"])
        second = provider.extract_discharge(case["document"])

        assert first == expected, case["name"]
        assert second == expected, case["name"]
        assert first == second, case["name"]
