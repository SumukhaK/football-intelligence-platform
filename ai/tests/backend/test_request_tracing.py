"""One server span per request, and log lines that link to it (contract section 4)."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind

import backend.app.main as main
from shared.telemetry.json_formatter import JsonFormatter
from shared.telemetry.setup import FormatterArgs


class _JsonLines(logging.Handler):
    """Formats each record as it is logged, while its span is still current."""

    def __init__(self) -> None:
        super().__init__()
        self.setFormatter(JsonFormatter(**_formatter_args()))
        self.lines: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(json.loads(self.format(record)))


def _formatter_args() -> FormatterArgs:
    return {
        "service": "football-api",
        "api_version": "2.0.0",
        "revision": None,
        "gcp_project_id": "fip",
    }


@pytest.fixture()
def exporter(monkeypatch: pytest.MonkeyPatch) -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(main, "configure_tracing", lambda settings: provider)
    return exporter


@pytest.fixture()
def json_lines() -> Iterator[_JsonLines]:
    handler = _JsonLines()
    logging.getLogger().addHandler(handler)
    yield handler
    logging.getLogger().removeHandler(handler)


def _client() -> TestClient:
    return TestClient(main.create_app(), raise_server_exceptions=False)


def test_a_request_gets_a_server_span_named_by_its_route(
    exporter: InMemorySpanExporter,
) -> None:
    _client().get("/v2/teams/Arsenal/outlook?email=a@b.c")

    (span,) = exporter.get_finished_spans()
    assert span.name == "GET /v2/teams/{team}/outlook"
    assert span.kind is SpanKind.SERVER
    attributes = span.attributes or {}
    assert all("email" not in str(value) for value in attributes.values())
    assert attributes.get("net.peer.ip") != "testclient"


def test_health_is_not_traced(exporter: InMemorySpanExporter) -> None:
    _client().get("/health")
    assert exporter.get_finished_spans() == ()


def test_log_lines_inside_a_request_carry_its_trace(
    exporter: InMemorySpanExporter, json_lines: _JsonLines
) -> None:
    _client().get("/v2/teams/Arsenal/outlook")

    (span,) = exporter.get_finished_spans()
    trace_id = format(span.context.trace_id, "032x")
    (line,) = [x for x in json_lines.lines if x["event"] == "http.request"]
    assert line["trace_id"] == trace_id
    assert line["logging.googleapis.com/trace"] == f"projects/fip/traces/{trace_id}"
    assert line["logging.googleapis.com/spanId"] == format(span.context.span_id, "016x")


def test_tracing_is_off_by_default() -> None:
    assert _client().app.state.tracer_provider is None  # type: ignore[attr-defined]
