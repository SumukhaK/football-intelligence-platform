"""Shared fixtures for integration tests.

All fixtures here operate against real model artifacts.
Tests are skipped when the required artifacts are missing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_AI_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = _AI_ROOT / "models" / "latest" / "model.joblib"
REGISTRY_PATH = _AI_ROOT / "models" / "registry.json"

# Full 42-feature vector using realistic neutral values.
NEUTRAL_FEATURES: dict[str, float] = {
    "home_form_wins_last5": 0.4,
    "home_form_wins_last10": 0.4,
    "home_form_points_last5": 6.0,
    "home_form_points_last10": 12.0,
    "away_form_wins_last5": 0.3,
    "away_form_wins_last10": 0.35,
    "away_form_points_last5": 5.0,
    "away_form_points_last10": 10.0,
    "home_goals_scored_last5": 1.4,
    "home_goals_scored_last10": 1.4,
    "home_goals_conceded_last5": 1.2,
    "home_goals_conceded_last10": 1.2,
    "home_goal_diff_last5": 0.2,
    "home_goal_diff_last10": 0.2,
    "away_goals_scored_last5": 1.3,
    "away_goals_scored_last10": 1.3,
    "away_goals_conceded_last5": 1.3,
    "away_goals_conceded_last10": 1.3,
    "away_goal_diff_last5": 0.0,
    "away_goal_diff_last10": 0.0,
    "home_win_pct": 0.4,
    "home_ppg": 1.4,
    "away_win_pct": 0.33,
    "away_ppg": 1.2,
    "home_rest_days": 7.0,
    "away_rest_days": 7.0,
    "h2h_meetings": 5.0,
    "h2h_home_wins": 2.0,
    "h2h_away_wins": 2.0,
    "h2h_draws": 1.0,
    "home_league_position": 8.0,
    "away_league_position": 12.0,
    "home_league_points": 30.0,
    "away_league_points": 22.0,
    "home_matches_played": 20.0,
    "away_matches_played": 20.0,
    "home_elo_before": 1520.0,
    "away_elo_before": 1480.0,
    "home_avg_opp_elo_last5": 1500.0,
    "home_avg_opp_elo_last10": 1500.0,
    "away_avg_opp_elo_last5": 1500.0,
    "away_avg_opp_elo_last10": 1500.0,
}


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def model_path() -> Path:
    """Return the path to the real model artifact, or skip if missing."""
    if not MODEL_PATH.exists():
        pytest.skip(f"Model artifact not found: {MODEL_PATH}")
    return MODEL_PATH


@pytest.fixture(scope="session")
def registry_path() -> Path:
    """Return the path to the real model registry, or skip if missing."""
    if not REGISTRY_PATH.exists():
        pytest.skip(f"Registry not found: {REGISTRY_PATH}")
    return REGISTRY_PATH


@pytest.fixture(scope="session")
def real_predictor(model_path: Path):  # type: ignore[no-untyped-def]
    """Return a MatchPredictor loaded from the real model artifact."""
    from inference.predictor import MatchPredictor

    return MatchPredictor.from_path(model_path)


@pytest.fixture(scope="session")
def neutral_features() -> dict[str, float]:
    """Return the shared neutral feature vector."""
    return NEUTRAL_FEATURES


@pytest.fixture(scope="session")
def real_client(model_path: Path, registry_path: Path):  # type: ignore[no-untyped-def]
    """Return a TestClient backed by the real prediction and explanation services."""
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from backend.app.config import Settings
    from backend.app.main import create_app

    settings = Settings(
        model_path=model_path,
        registry_path=registry_path,
    )
    with patch("backend.app.config._settings", settings):
        with patch("backend.app.main.get_settings", return_value=settings):
            application = create_app()
            with TestClient(application, raise_server_exceptions=False) as c:
                yield c
