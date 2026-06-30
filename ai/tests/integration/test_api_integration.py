"""Integration tests for all five FastAPI endpoints with real services.

Uses the real prediction and explainability models (not mocks).
The assistant endpoint is tested for its graceful 503 response when
Ollama is not available (which is always the case in CI).
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from tests.integration.conftest import NEUTRAL_FEATURES

# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_health_returns_200(real_client: Any) -> None:
    """GET /health returns 200."""
    response = real_client.get("/health")
    assert response.status_code == 200


@pytest.mark.integration
def test_health_model_loaded(real_client: Any) -> None:
    """GET /health reports model_loaded=true when real model is present."""
    data = real_client.get("/health").json()
    assert data["model_loaded"] is True
    assert data["status"] == "ok"


@pytest.mark.integration
def test_health_response_fields(real_client: Any) -> None:
    """GET /health returns all required fields."""
    data = real_client.get("/health").json()
    for field in (
        "status",
        "model_loaded",
        "explainability_available",
        "assistant_available",
        "version",
    ):
        assert field in data, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# GET /model
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_model_returns_200(real_client: Any) -> None:
    """GET /model returns 200 when registry is present."""
    response = real_client.get("/model")
    assert response.status_code == 200


@pytest.mark.integration
def test_model_response_fields(real_client: Any) -> None:
    """GET /model returns version, metrics, and timestamp."""
    data = real_client.get("/model").json()
    for field in ("model_version", "dataset_version", "training_timestamp", "metrics"):
        assert field in data, f"Missing field: {field}"


@pytest.mark.integration
def test_model_metrics_are_numeric(real_client: Any) -> None:
    """GET /model metrics values are all floats."""
    data = real_client.get("/model").json()
    for key, value in data.get("metrics", {}).items():
        assert isinstance(value, float), f"Metric {key} is not float: {value!r}"


# ---------------------------------------------------------------------------
# POST /predict
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_predict_returns_200(real_client: Any) -> None:
    """POST /predict returns 200 with real model and valid features."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    response = real_client.post("/predict", json=payload)
    assert response.status_code == 200


@pytest.mark.integration
def test_predict_outcome_valid(real_client: Any) -> None:
    """POST /predict returns H, D, or A."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    data = real_client.post("/predict", json=payload).json()
    assert data["predicted_result"] in ("H", "D", "A")


@pytest.mark.integration
def test_predict_probabilities_sum_to_one(real_client: Any) -> None:
    """POST /predict probabilities sum to approximately 1.0."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    data = real_client.post("/predict", json=payload).json()
    total = (
        data["probability_home"] + data["probability_draw"] + data["probability_away"]
    )
    assert abs(total - 1.0) < 0.001, f"Probabilities sum to {total}"


@pytest.mark.integration
def test_predict_latency_under_500ms(real_client: Any) -> None:
    """POST /predict responds in under 500 ms."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    start = time.perf_counter()
    real_client.post("/predict", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 500, f"Prediction API took {elapsed_ms:.1f} ms (limit 500 ms)"


@pytest.mark.integration
def test_predict_422_missing_team(real_client: Any) -> None:
    """POST /predict returns 422 when a required field is absent."""
    payload = {"away_team": "Chelsea", "features": NEUTRAL_FEATURES}
    response = real_client.post("/predict", json=payload)
    assert response.status_code == 422


@pytest.mark.integration
def test_predict_422_empty_team(real_client: Any) -> None:
    """POST /predict returns 422 when home_team is an empty string."""
    payload = {"home_team": "", "away_team": "Chelsea", "features": NEUTRAL_FEATURES}
    response = real_client.post("/predict", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /explain
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_explain_returns_200(real_client: Any) -> None:
    """POST /explain returns 200 with real model and valid features."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    response = real_client.post("/explain", json=payload)
    assert response.status_code == 200


@pytest.mark.integration
def test_explain_has_feature_contributions(real_client: Any) -> None:
    """POST /explain response includes non-empty feature contribution lists."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    data = real_client.post("/explain", json=payload).json()
    assert len(data["top_positive_features"]) > 0
    assert len(data["top_negative_features"]) > 0
    assert len(data["all_contributions"]) == 42


@pytest.mark.integration
def test_explain_consistent_with_predict(real_client: Any) -> None:
    """POST /explain predicted_result matches POST /predict for the same features."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    predict_result = real_client.post("/predict", json=payload).json()[
        "predicted_result"
    ]
    explain_result = real_client.post("/explain", json=payload).json()[
        "predicted_result"
    ]
    assert (
        predict_result == explain_result
    ), f"/predict returned {predict_result!r} but /explain returned {explain_result!r}"


@pytest.mark.integration
def test_explain_latency_under_3s(real_client: Any) -> None:
    """POST /explain responds in under 3 seconds."""
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": NEUTRAL_FEATURES,
    }
    start = time.perf_counter()
    real_client.post("/explain", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 3000, f"Explain API took {elapsed_ms:.1f} ms (limit 3000 ms)"


# ---------------------------------------------------------------------------
# POST /assistant/chat
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_assistant_graceful_when_ollama_unavailable(real_client: Any) -> None:
    """POST /assistant/chat returns 503 when Ollama is not running.

    In CI (and any environment without Ollama), the assistant service
    will fail to load and the endpoint must return 503 — not 500.
    """
    response = real_client.post(
        "/assistant/chat",
        json={"message": "What is the model accuracy?"},
    )
    # 200 if Ollama is running locally; 503 if not.
    assert response.status_code in (
        200,
        503,
    ), f"Unexpected status {response.status_code} from /assistant/chat"
    if response.status_code == 503:
        data = response.json()
        assert (
            "error" in data or "detail" in data
        ), "503 response must include error detail"
