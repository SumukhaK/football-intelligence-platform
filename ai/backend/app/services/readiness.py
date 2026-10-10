"""Which startup components the API cannot serve without (ADR 025)."""

from __future__ import annotations

from typing import Any

# Component name, as in ``component.load`` events, to the app.state attribute
# it fills. The assistant is left out: chat answers 503 on its own, and a
# provider outage must never take predictions out of service.
REQUIRED_COMPONENTS = {
    "prediction_model": "prediction_service",
    "explanation": "explanation_service",
    "match_history": "fixture_feature_service",
    "goals_model": "insights_service",
    "fixtures": "fixtures_service",
    "season_outlook": "outlook_service",
}


def missing_components(state: Any) -> list[str]:
    """Names of the required components that did not load; empty when ready."""
    return [
        name
        for name, attr in REQUIRED_COMPONENTS.items()
        if getattr(state, attr, None) is None
    ]
