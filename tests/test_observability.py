from contextlib import contextmanager
from typing import Any

import pytest

from backend.observability import tracing


def test_observation_is_noop_without_langfuse_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tracing, "is_langfuse_configured", lambda: False)
    monkeypatch.setattr(
        tracing,
        "get_client",
        lambda: pytest.fail("Langfuse client should not initialize without credentials"),
    )

    with tracing.observation("test-stage") as span:
        assert span.trace_id is None
        assert span.observation_id is None
        span.update({"success": True})


def test_observation_resumes_trace_with_parent_and_safe_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSpan:
        output: dict[str, Any] | None = None

        def update(self, *, output: dict[str, Any]) -> None:
            self.output = output

    class FakeClient:
        def __init__(self) -> None:
            self.span = FakeSpan()
            self.arguments: dict[str, Any] = {}

        def start_as_current_observation(self, **kwargs: Any) -> Any:
            self.arguments = kwargs

            @contextmanager
            def active_span():
                yield self.span

            return active_span()

        def get_current_trace_id(self) -> str:
            return "a" * 32

        def get_current_observation_id(self) -> str:
            return "b" * 16

    client = FakeClient()
    monkeypatch.setattr(tracing, "is_langfuse_configured", lambda: True)
    monkeypatch.setattr(tracing, "get_client", lambda: client)

    with tracing.observation(
        "export-reviewed-document",
        input_data={"format": "txt"},
        trace_id="c" * 32,
        parent_observation_id="d" * 16,
    ) as span:
        span.update({"export_recorded": True})

    assert client.arguments["trace_context"] == {
        "trace_id": "c" * 32,
        "parent_span_id": "d" * 16,
    }
    assert client.arguments["input"] == {"format": "txt"}
    assert client.span.output == {"export_recorded": True}
    assert span.trace_id == "a" * 32
    assert span.observation_id == "b" * 16
