from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from typing import Any


def setup_tracing() -> Any:
    from inference_catalyst_tracing import setup

    tracing = setup()
    suppress_openai_agents_backend_exporter()
    return tracing


def suppress_openai_agents_backend_exporter() -> None:
    """Keep Agents SDK spans local to Catalyst tracing, not OpenAI's trace backend."""
    try:
        from agents.tracing import get_trace_provider, set_trace_processors
        from agents.tracing.processors import BatchTraceProcessor
    except Exception:
        return

    try:
        provider = get_trace_provider()
        multi_processor = getattr(provider, "_multi_processor", None)
        processors = list(getattr(multi_processor, "_processors", ()) or ())
        filtered = [
            processor for processor in processors if not isinstance(processor, BatchTraceProcessor)
        ]
        if len(filtered) != len(processors):
            set_trace_processors(filtered)
    except Exception:
        return


@contextmanager
def maybe_manual_span(
    tracing: Any | None,
    name: str,
    span_kind_name: str,
    input_payload: dict[str, Any] | None = None,
) -> Iterator[Any]:
    if tracing is None:
        with nullcontext() as span:
            yield span
        return

    from inference_catalyst_tracing import SpanKindValues, manual_span

    span_kind = getattr(SpanKindValues, span_kind_name)
    with manual_span(
        tracing.tracer,
        name=name,
        span_kind=span_kind,
        input=input_payload or {},
    ) as span:
        yield span
