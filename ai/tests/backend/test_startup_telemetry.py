"""Tests for component.load, data.freshness and fallback events at startup."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.startup_telemetry import (
    age_hours,
    load_component,
    log_fallback,
    log_freshness,
)

Events = Callable[[str], list[tuple[str, dict[str, Any]]]]
NOW = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)


class StepClock:
    """Each call moves time on by 1.5 seconds."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        self.now += 1.5
        return self.now


class History:
    """Match history holding two leagues."""

    def matches_through(self, competition: str) -> str:
        return {"Premier League": "2026-10-05", "Bundesliga": "2026-10-04"}[competition]


def test_a_component_that_loads_is_ok(events: Events) -> None:
    assert load_component("fixtures", lambda: "service", StepClock()) == "service"
    assert events("component.load") == [
        (
            "INFO",
            {
                "component": "fixtures",
                "status": "ok",
                "duration_ms": 1500,
                "reason": None,
            },
        )
    ]


def test_a_component_that_raises_failed_and_is_none(events: Events) -> None:
    def broken() -> str:
        raise FileNotFoundError("Model file not found at x.joblib")

    assert load_component("prediction_model", broken, StepClock()) is None
    ((severity, attributes),) = events("component.load")
    assert severity == "WARNING"
    assert attributes["status"] == "failed"
    assert attributes["reason"] == "Model file not found at x.joblib"


def test_age_hours_counts_from_the_start_of_the_day() -> None:
    assert age_hours("2026-10-05", NOW) == 108.0


def test_freshness_per_league(events: Events) -> None:
    log_freshness(History(), ["Premier League", "Bundesliga", "Serie A"], lambda: NOW)
    assert events("data.freshness") == [
        (
            "INFO",
            {
                "competition": "Premier League",
                "matches_through": "2026-10-05",
                "age_hours": 108.0,
            },
        ),
        (
            "INFO",
            {
                "competition": "Bundesliga",
                "matches_through": "2026-10-04",
                "age_hours": 132.0,
            },
        ),
        (
            "INFO",
            {"competition": "Serie A", "matches_through": None, "age_hours": None},
        ),
    ]


def test_freshness_without_history_is_null(events: Events) -> None:
    log_freshness(None, ["Ligue 1"], lambda: NOW)
    assert events("data.freshness") == [
        ("INFO", {"competition": "Ligue 1", "matches_through": None, "age_hours": None})
    ]


def test_fallback(events: Events) -> None:
    log_fallback("fresh_fixtures", "previous_fixtures", "fixtures_refresh_failed", "x")
    assert events("fallback") == [
        (
            "WARNING",
            {
                "from_path": "fresh_fixtures",
                "to_path": "previous_fixtures",
                "cause": "fixtures_refresh_failed",
            },
        )
    ]


def _start_without_data(tmp_path: Path) -> None:
    from backend.app.config import Settings
    from backend.app.main import create_app

    settings = Settings(
        model_path=tmp_path / "none.joblib",
        v1_model_path=tmp_path / "none_v1.joblib",
        registry_path=tmp_path / "registry.json",
        matches_dir=tmp_path / "matches",
        fixtures_dir=tmp_path / "fixtures",
        assistant_vector_store_path=tmp_path / "store",
        served_competitions=["Premier League"],
    )
    with patch("backend.app.config._settings", settings):
        with patch("backend.app.main.get_settings", return_value=settings):
            with TestClient(create_app()):
                pass


def test_startup_logs_every_component_once(tmp_path: Path, events: Events) -> None:
    _start_without_data(tmp_path)
    loads = events("component.load")
    assert sorted(a["component"] for _, a in loads) == sorted(
        [
            "match_history",
            "goals_model",
            "fixtures",
            "season_history",
            "season_outlook",
            "prediction_model",
            "explanation",
            "prediction_model_v1",
            "assistant",
        ]
    )
    assert {a["status"] for _, a in loads} == {"failed"}


def test_startup_without_history_falls_back(tmp_path: Path, events: Events) -> None:
    _start_without_data(tmp_path)
    assert [a["from_path"] for _, a in events("fallback")] == ["server_features"]
    assert events("data.freshness") == [
        (
            "INFO",
            {
                "competition": "Premier League",
                "matches_through": None,
                "age_hours": None,
            },
        )
    ]
