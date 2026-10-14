"""Spans recorded by the daily refresh (telemetry contract section 4)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import StatusCode

from backend.app.services.live_refresh_service import LiveRefreshService

NOW = datetime(2026, 9, 29, 9, 30, tzinfo=UTC)


def test_a_refresh_records_download_then_reload(spans: InMemorySpanExporter) -> None:
    LiveRefreshService(lambda: Path("x.csv"), lambda: None, lambda: NOW).run_once()

    download, reload, run = spans.get_finished_spans()
    assert [download.name, reload.name, run.name] == [
        "refresh.download",
        "refresh.reload",
        "refresh.run",
    ]
    assert download.parent is not None and reload.parent is not None
    assert download.parent.span_id == run.context.span_id
    assert reload.parent.span_id == run.context.span_id


def test_a_failed_download_is_recorded(spans: InMemorySpanExporter) -> None:
    def fail() -> Path:
        raise RuntimeError("network down")

    outcome = LiveRefreshService(fail, lambda: None, lambda: NOW).run_once()

    assert outcome.error == "network down"
    names = [s.name for s in spans.get_finished_spans()]
    assert names == ["refresh.download", "refresh.run"]
    download = spans.get_finished_spans()[0]
    assert download.status.status_code is StatusCode.ERROR
    assert download.events[0].name == "exception"
