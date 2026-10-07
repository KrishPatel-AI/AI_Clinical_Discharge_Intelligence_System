"""Run the fixed synthetic Ragas evaluation set against the review workflow."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
from typing import Any

from langchain_ollama import ChatOllama
from openai import AsyncOpenAI
from ragas.embeddings.base import embedding_factory
from ragas.llms.base import InstructorBaseRagasLLM
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecisionWithReference,
    Faithfulness,
)

from backend.config import (
    get_ollama_base_url,
    get_ollama_embedding_model,
    get_ollama_model,
)
from backend.models.schemas import DischargeExtraction
from backend.rag.workflow import review_extraction
from knowledge_base.ingest import DEFAULT_INDEX_DIR, build_index, query_index

EVAL_DIR = Path(__file__).parent
CASES_PATH = EVAL_DIR / "ragas_cases.json"
THRESHOLDS_PATH = EVAL_DIR / "ragas_thresholds.json"
CANDIDATE_LIMIT = 5


class OllamaStructuredEvaluator(InstructorBaseRagasLLM):
    """Adapt the local Ollama chat model to Ragas' structured-output contract."""

    def __init__(self, model_name: str) -> None:
        self.model = ChatOllama(model=model_name, temperature=0.0)

    def generate(self, prompt: str, response_model: Any) -> Any:
        return self.model.with_structured_output(response_model).invoke(prompt)

    async def agenerate(self, prompt: str, response_model: Any) -> Any:
        return await self.model.with_structured_output(response_model).ainvoke(prompt)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_review_rows(index_dir: Path) -> tuple[list[dict[str, Any]], int]:
    evaluation_data = _load_json(CASES_PATH)
    rows: list[dict[str, Any]] = []

    for case in evaluation_data["cases"]:
        extraction = DischargeExtraction.model_validate(case["extraction"])
        review = review_extraction(extraction, index_dir)
        if review.status != "matched" or review.guideline is None:
            raise AssertionError(f"Expected a matched review for {case['name']}.")

        suggestion_sections = [item.section for item in review.suggestions]
        if suggestion_sections != case["expected_suggestion_sections"]:
            raise AssertionError(
                f"Suggestion sections changed for {case['name']}: "
                f"{suggestion_sections}"
            )

        source_document = case["source_document"]
        user_input = (
            "Review this synthetic discharge summary for "
            f"{extraction.diagnosis} and identify missing sections for "
            f"doctor review: {source_document}"
        )
        response = (
            f"Review findings for {extraction.diagnosis}:\n"
            + "\n".join(
                [
                    f"- Suggestion for {suggestion.section.replace('_', ' ')}: "
                    f"{suggestion.explanation}"
                    for suggestion in review.suggestions
                ]
            )
        )
        candidate_result = query_index(
            extraction.diagnosis,
            index_dir=index_dir,
            limit=CANDIDATE_LIMIT,
        )
        candidate_passages = [str(doc) for doc in candidate_result["documents"]]

        rows.append(
            {
                "name": case["name"],
                "user_input": user_input,
                "response": response,
                "candidate_contexts": candidate_passages,
                "faithfulness_contexts": [
                    f"Original discharge summary: {source_document}",
                    review.guideline.passage,
                ],
                "reference": case["reference"],
            }
        )

    no_match = review_extraction(
        DischargeExtraction.model_validate(evaluation_data["no_match_case"]),
        index_dir,
    )
    if no_match.status != "no_match" or no_match.suggestions:
        raise AssertionError("No-match guardrail produced suggestions or a match.")
    print("No-match guardrail: passed")
    return rows, len(evaluation_data["cases"])


async def _score_rows(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    base_url = get_ollama_base_url().rstrip("/")
    client = AsyncOpenAI(api_key="ollama", base_url=f"{base_url}/v1")
    llm = OllamaStructuredEvaluator(get_ollama_model())
    embeddings = embedding_factory(
        provider="openai",
        model=get_ollama_embedding_model(),
        client=client,
        interface="modern",
    )
    metrics = {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "context_precision": ContextPrecisionWithReference(llm=llm),
    }
    scores: dict[str, list[float]] = {name: [] for name in metrics}
    for row in rows:
        for name, metric in metrics.items():
            metric_input: dict[str, Any] = {
                "user_input": row["user_input"],
            }
            if name == "faithfulness":
                metric_input["retrieved_contexts"] = row["faithfulness_contexts"]
            elif name == "context_precision":
                metric_input["retrieved_contexts"] = row["candidate_contexts"]
            if name != "context_precision":
                metric_input["response"] = row["response"]
            if name == "context_precision":
                metric_input["reference"] = row["reference"]
            result = await metric.ascore(**metric_input)
            scores[name].append(float(result.value))
    return scores


def main() -> None:
    """Build the current guideline index, run Ragas, and enforce score floors."""
    build_index(Path("knowledge_base/guidelines"), DEFAULT_INDEX_DIR)
    rows, expected_case_count = _build_review_rows(DEFAULT_INDEX_DIR)
    scores = asyncio.run(_score_rows(rows))
    thresholds = _load_json(THRESHOLDS_PATH)
    failures: list[str] = []

    if len(rows) != expected_case_count:
        raise AssertionError("Ragas did not evaluate every configured case.")

    for name, values in scores.items():
        if len(values) != expected_case_count or not all(
            math.isfinite(value) for value in values
        ):
            failures.append(f"{name}: missing or non-finite case score")
            continue
        mean_score = sum(values) / len(values)
        threshold = float(thresholds[name])
        print(f"{name}: {mean_score:.3f} (minimum {threshold:.3f})")
        for case, value in zip(rows, values):
            print(f"  {case['name']}: {value:.3f}")
            if value < threshold:
                failures.append(
                    f"{name} ({case['name']}): score {value:.3f} "
                    f"is below minimum {threshold:.3f}"
                )
        if mean_score < threshold:
            failures.append(
                f"{name}: score {mean_score:.3f} is below minimum {threshold:.3f}"
            )

    if failures:
        raise SystemExit("Ragas evaluation failed: " + "; ".join(failures))
    print(f"Ragas evaluation passed for {expected_case_count} synthetic cases.")


if __name__ == "__main__":
    main()