"""Tests for the backend's daily data refresh (ADR 013)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.services.live_refresh_service import (
    LiveRefreshService,
    is_due,
    last_scheduled,
    next_run,
)

NOW = datetime(2026, 9, 29, 9, 30, tzinfo=UTC)


def test_next_run_later_today() -> None:
    assert next_run(NOW, 18) == datetime(2026, 9, 29, 18, tzinfo=UTC)


def test_next_run_tomorrow_once_the_hour_has_passed() -> None:
    assert next_run(NOW, 6) == datetime(2026, 9, 30, 6, tzinfo=UTC)
    exactly = datetime(2026, 9, 29, 6, tzinfo=UTC)
    assert next_run(exactly, 6) == datetime(2026, 9, 30, 6, tzinfo=UTC)


def test_last_scheduled() -> None:
    assert last_scheduled(NOW, 6) == datetime(2026, 9, 29, 6, tzinfo=UTC)
    assert last_scheduled(NOW, 18) == datetime(2026, 9, 28, 18, tzinfo=UTC)


@pytest.mark.parametrize(
    ("built", "due"),
    [
        (None, True),
        (datetime(2026, 9, 28, 17, tzinfo=UTC), True),
        (datetime(2026, 9, 29, 7, tzinfo=UTC), False),
    ],
)
def test_is_due(built: datetime | None, due: bool) -> None:
    assert is_due(built, NOW, 6) is due


def test_success_reloads_and_records_the_dataset() -> None:
    reloads: list[str] = []
    service = LiveRefreshService(
        refresh=lambda: Path("match_results_live_v20260929_060000.csv"),
        reload=lambda: reloads.append("reloaded"),
        clock=lambda: NOW,
    )
    outcome = service.run_once()
    assert reloads == ["reloaded"]
    assert outcome.error is None
    assert outcome.dataset == Path("match_results_live_v20260929_060000.csv")
    assert service.last_outcome == outcome


def test_failed_download_keeps_the_old_data() -> None:
    reloads: list[str] = []

    def fail() -> Path:
        raise ConnectionError("football-data.co.uk unreachable")

    service = LiveRefreshService(fail, lambda: reloads.append("x"), lambda: NOW)
    outcome = service.run_once()
    assert reloads == []
    assert outcome.error == "football-data.co.uk unreachable"
    assert outcome.dataset is None


def test_run_daily_refreshes_at_startup_when_due() -> None:
    calls: list[int] = []

    def refresh() -> Path:
        calls.append(1)
        return Path("x.csv")

    service = LiveRefreshService(refresh, reload=lambda: None, clock=lambda: NOW)

    async def run_briefly() -> None:
        task = asyncio.create_task(service.run_daily(hour=6, due_now=True))
        await asyncio.sleep(0.2)
        task.cancel()

    asyncio.run(run_briefly())
    assert calls == [1]


def test_health_reports_the_last_refresh() -> None:
    app = create_app()
    service = LiveRefreshService(lambda: Path("x.csv"), lambda: None, lambda: NOW)
    service.run_once()
    app.state.live_refresh_service = service
    body = TestClient(app).get("/health").json()
    assert body["last_refresh_at"] == NOW.isoformat()
    assert body["last_refresh_error"] is None


def test_startup_never_refreshes_in_tests(tmp_path: Path) -> None:
    """The autouse guard stops the lifespan from starting a real refresh."""
    before = sorted(Path("../datasets/processed/football_data").glob("*live*.csv"))
    with TestClient(create_app()) as client:
        client.get("/health")
        assert getattr(client.app.state, "live_refresh_service", None) is None  # type: ignore[attr-defined]
    after = sorted(Path("../datasets/processed/football_data").glob("*live*.csv"))
    assert before == after


def test_refresh_can_be_turned_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.app.config import Settings

    monkeypatch.setenv("LIVE_REFRESH_HOUR", "off")
    assert Settings().live_refresh_hour is None
    monkeypatch.setenv("LIVE_REFRESH_HOUR", "18")
    assert Settings().live_refresh_hour == 18
