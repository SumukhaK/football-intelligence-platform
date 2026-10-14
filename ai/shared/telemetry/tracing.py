"""OpenTelemetry traces: provider, exporter choice and the backend tracer (ADR 024)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, Protocol

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from shared.telemetry.privacy import hash_ref

TraceExporter = Literal["none", "otlp", "gcp"]
TRACER_NAME = "football.backend"
SERVICE_NAME = "football-api"
# Attributes the FastAPI instrumentation sets that the privacy rules forbid.
_URL_KEYS = ("http.url", "url.full")
_CLIENT_KEYS = ("net.peer.ip", "client.address")


class TracingSettings(Protocol):
    """The settings tracing reads; the backend's Settings satisfies it."""

    @property
    def trace_exporter(self) -> TraceExporter:
        """Where spans go: nowhere, an OTLP collector or Cloud Trace."""

    @property
    def otlp_endpoint(self) -> str:
        """The OTLP/HTTP traces endpoint of the local collector."""

    @property
    def trace_sample_ratio(self) -> float:
        """The share of new traces to record, 0 to 1."""

    @property
    def gcp_project_id(self) -> str | None:
        """The Cloud Trace project; required for the gcp exporter."""

    @property
    def api_version(self) -> str:
        """Logged as ``service.version``."""

    @property
    def revision(self) -> str | None:
        """Cloud Run's revision, logged as ``service.instance.id``."""


def _exporter(settings: TracingSettings) -> SpanExporter:
    if settings.trace_exporter == "otlp":
        return OTLPSpanExporter(endpoint=settings.otlp_endpoint)
    if not settings.gcp_project_id:
        raise ValueError("TRACE_EXPORTER=gcp needs GCP_PROJECT_ID to be set.")
    return CloudTraceSpanExporter(project_id=settings.gcp_project_id)


def _resource(settings: TracingSettings) -> Resource:
    attributes = {"service.name": SERVICE_NAME, "service.version": settings.api_version}
    if settings.revision:
        attributes["service.instance.id"] = settings.revision
    return Resource.create(attributes)


def configure_tracing(
    settings: TracingSettings,
    install: Callable[[TracerProvider], None] = trace.set_tracer_provider,
) -> TracerProvider | None:
    """Build and install the tracer provider; None when tracing is off."""
    if settings.trace_exporter == "none":
        return None
    # A lower ratio only thins traces: every request still has its http.request
    # log line, and errors still reach logs and Error Reporting in full.
    sampler = ParentBased(TraceIdRatioBased(settings.trace_sample_ratio))
    provider = TracerProvider(sampler=sampler, resource=_resource(settings))
    provider.add_span_processor(BatchSpanProcessor(_exporter(settings)))
    install(provider)
    return provider


def shutdown_tracing(provider: TracerProvider | None) -> None:
    """Flush and stop the provider, so spans of the last requests are sent."""
    if provider is not None:
        provider.shutdown()


def tracer() -> trace.Tracer:
    """Return the backend's tracer, from the installed provider."""
    return trace.get_tracer(TRACER_NAME)


def scrub_server_span(salt: str) -> Callable[[trace.Span, dict[str, Any]], None]:
    """Return a request hook that drops the query string and hashes the client IP."""

    def hook(span: trace.Span, scope: dict[str, Any]) -> None:
        attributes = getattr(span, "attributes", None)
        if not span.is_recording() or attributes is None:
            return
        for key in _URL_KEYS:
            if key in attributes:
                span.set_attribute(key, str(attributes[key]).split("?", 1)[0])
        if "url.query" in attributes:
            span.set_attribute("url.query", "")
        for key in _CLIENT_KEYS:
            if key in attributes:
                span.set_attribute(key, hash_ref(str(attributes[key]), salt))

    return hook
