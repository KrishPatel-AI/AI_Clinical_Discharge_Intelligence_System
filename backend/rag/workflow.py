"""LangGraph retrieval and section comparison workflow."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from backend.models.schemas import (
    ComparisonItem,
    DischargeExtraction,
    GuidelineMatch,
    ReviewResponse,
)
from knowledge_base.ingest import DEFAULT_INDEX_DIR, query_index

MIN_RETRIEVAL_SIMILARITY = 0.2
RETRIEVAL_LIMIT = 5


class ReviewState(TypedDict, total=False):
    extraction: DischargeExtraction
    index_dir: Path
    match: GuidelineMatch | None
    comparisons: list[ComparisonItem]
    result: ReviewResponse


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) >= 4}


def _retrieve(state: ReviewState) -> dict[str, GuidelineMatch | None]:
    extraction = state["extraction"]
    result = query_index(
        extraction.diagnosis,
        index_dir=state.get("index_dir", DEFAULT_INDEX_DIR),
        limit=RETRIEVAL_LIMIT,
    )
    if not result["distances"] or float(result["distances"][0]) < MIN_RETRIEVAL_SIMILARITY:
        return {"match": None}
    metadata = result["metadatas"][0]
    return {
        "match": GuidelineMatch(
            diagnosis=str(metadata["diagnosis"]),
            diagnosis_slug=str(metadata["diagnosis_slug"]),
            source_url=str(metadata["source_url"]),
            passage=str(result["documents"][0]),
            similarity=float(result["distances"][0]),
        )
    }


def _compare(state: ReviewState) -> dict[str, Any]:
    match = state.get("match")
    extraction = state["extraction"]
    if match is None:
        return {
            "comparisons": [],
            "result": ReviewResponse(
                diagnosis=extraction.diagnosis,
                status="no_match",
                message="No matching guideline found for this diagnosis.",
            ),
        }

    sections = {
        "diagnosis": [extraction.diagnosis],
        "medications": extraction.medications,
        "follow_up_requirements": extraction.follow_up_requirements,
        "warning_signs": extraction.warning_signs,
    }
    passage_tokens = _tokens(match.passage)
    comparisons: list[ComparisonItem] = []
    for section, values in sections.items():
        value_tokens = set().union(*(_tokens(value) for value in values)) if values else set()
        status = "matched" if values and value_tokens & passage_tokens else "gap"
        comparisons.append(
            ComparisonItem(
                section=section,
                status=status,
                extracted_values=values,
                guideline_passage=match.passage,
            )
        )
    return {
        "comparisons": comparisons,
        "result": ReviewResponse(
            diagnosis=extraction.diagnosis,
            status="matched",
            message="Guideline retrieved and discharge sections compared.",
            guideline=match,
            comparisons=comparisons,
        ),
    }


def _build_graph() -> Any:
    graph = StateGraph(ReviewState)
    graph.add_node("retrieve", _retrieve)
    graph.add_node("compare", _compare)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "compare")
    graph.add_edge("compare", END)
    return graph.compile()


REVIEW_GRAPH = _build_graph()


def review_extraction(
    extraction: DischargeExtraction,
    index_dir: Path = DEFAULT_INDEX_DIR,
) -> ReviewResponse:
    """Retrieve evidence and compare it with an extracted discharge summary."""
    state = cast(
        ReviewState,
        REVIEW_GRAPH.invoke({"extraction": extraction, "index_dir": index_dir}),
    )
    return state["result"]