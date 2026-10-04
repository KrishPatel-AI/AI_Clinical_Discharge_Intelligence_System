"""Privacy-preserving Langfuse observation helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal, cast

from langfuse import get_client

from backend.config import is_langfuse_configured

ObservationType = Literal["span", "generation", "retriever", "chain"]


@dataclass(frozen=True)
class Observation:
    """Active observation reference and identifiers for persistence/correlation."""

    trace_id: str | None = None
    observation_id: str | None = None
    _span: Any | None = None

    def update(self, output: dict[str, Any]) -> None:
        """Record non-sensitive stage metadata when tracing is enabled."""
        if self._span is not None:
            self._span.update(output=output)


@contextmanager
def observation(
    name: str,
    *,
    input_data: dict[str, Any] | None = None,
    as_type: ObservationType = "span",
    trace_id: str | None = None,
    parent_observation_id: str | None = None,
) -> Iterator[Observation]:
    """Create an observation, or behave as a no-op without Langfuse credentials.

    Callers must pass metadata only. Raw documents, extracted clinical fields,
    guideline passages, and model prompts/responses must not be sent to Langfuse.
    """
    if not is_langfuse_configured():
        yield Observation()
        return

    client = get_client()
    trace_context: dict[str, str] = {}
    if trace_id is not None:
        trace_context["trace_id"] = trace_id
    if parent_observation_id is not None:
        trace_context["parent_span_id"] = parent_observation_id

    with cast(Any, client).start_as_current_observation(
        name=name,
        as_type=as_type,
        input=input_data,
        trace_context=trace_context or None,
    ) as span:
        yield Observation(
            trace_id=client.get_current_trace_id(),
            observation_id=client.get_current_observation_id(),
            _span=span,
        )
