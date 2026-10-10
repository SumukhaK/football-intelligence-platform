"""Tests for tracer provider setup."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

import pytest
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.sampling import ParentBased

import shared.telemetry.tracing as tracing
from shared.telemetry.tracing import (
    TraceExporter,
    configure_tracing,
    scrub_server_span,
    shutdown_tracing,
)


@dataclass(frozen=True)
class _Settings:
    trace_exporter: TraceExporter = "otlp"
    otlp_endpoint: str = "http://collector:4318/v1/traces"
    trace_sample_ratio: float = 1.0
    gcp_project_id: str | None = None
    api_version: str = "2.0.0"
    revision: str | None = None


class _FakeExporter(SpanExporter):
    """Records how it was built; never sends anything."""

    built: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, kind: str, **kwargs: Any) -> None:
        _FakeExporter.built.append((kind, kwargs))

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        return SpanExportResult.SUCCESS


@pytest.fixture(autouse=True)
def _fake_exporters(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    _FakeExporter.built = []
    monkeypatch.setattr(
        tracing, "OTLPSpanExporter", lambda **kw: _FakeExporter("otlp", **kw)
    )
    monkeypatch.setattr(
        tracing, "CloudTraceSpanExporter", lambda **kw: _FakeExporter("gcp", **kw)
    )
    yield


def _configure(settings: _Settings) -> TracerProvider | None:
    installed: list[TracerProvider] = []
    provider = configure_tracing(settings, install=installed.append)
    assert installed == ([provider] if provider else [])
    return provider


def test_none_turns_tracing_off() -> None:
    assert _configure(_Settings(trace_exporter="none")) is None
    assert _FakeExporter.built == []


def test_otlp_exports_to_the_configured_endpoint() -> None:
    provider = _configure(_Settings())
    assert _FakeExporter.built == [
        ("otlp", {"endpoint": "http://collector:4318/v1/traces"})
    ]
    shutdown_tracing(provider)


def test_gcp_exports_to_the_project() -> None:
    provider = _configure(_Settings(trace_exporter="gcp", gcp_project_id="fip"))
    assert _FakeExporter.built == [("gcp", {"project_id": "fip"})]
    shutdown_tracing(provider)


def test_gcp_without_a_project_fails_at_startup() -> None:
    with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
        _configure(_Settings(trace_exporter="gcp"))


def test_the_sample_ratio_is_applied_under_the_parent_decision() -> None:
    provider = _configure(_Settings(trace_sample_ratio=0.25))
    assert provider is not None
    assert isinstance(provider.sampler, ParentBased)
    assert "0.25" in provider.sampler.get_description()
    shutdown_tracing(provider)


def test_the_resource_names_the_service() -> None:
    provider = _configure(_Settings(revision="rev-7"))
    assert provider is not None
    attributes = provider.resource.attributes
    assert attributes["service.name"] == "football-api"
    assert attributes["service.version"] == "2.0.0"
    assert attributes["service.instance.id"] == "rev-7"
    shutdown_tracing(provider)


def test_shutdown_without_a_provider_does_nothing() -> None:
    shutdown_tracing(None)


class _Span:
    """Just enough of a recording span for the request hook."""

    def __init__(self, attributes: dict[str, Any]) -> None:
        self.attributes = attributes

    def is_recording(self) -> bool:
        return True

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value


def test_the_request_hook_drops_the_query_and_hashes_the_client() -> None:
    span = _Span(
        {
            "http.url": "http://api/v2/teams?email=a@b.c",
            "url.full": "http://api/x?token=1",
            "url.query": "token=1",
            "net.peer.ip": "10.0.0.1",
            "client.address": "10.0.0.1",
        }
    )
    scrub_server_span("salt")(span, {})  # type: ignore[arg-type]
    assert span.attributes["http.url"] == "http://api/v2/teams"
    assert span.attributes["url.full"] == "http://api/x"
    assert span.attributes["url.query"] == ""
    assert span.attributes["net.peer.ip"] != "10.0.0.1"
    assert len(span.attributes["client.address"]) == 16
