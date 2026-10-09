"""Every event the tests made the code emit matches the telemetry contract.

``session_events`` in ``tests/conftest.py`` collects events from every test
that ran before this one; the backend and assistant tests run first. This test
also makes a few requests itself, so it checks real events when run alone.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

EVENTS_JSON = (
    Path(__file__).resolve().parents[4]
    / "docs"
    / "observability"
    / "telemetry-events.json"
)


def _contract() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    return data


def test_emitted_events_follow_the_contract(
    session_events: list[logging.LogRecord],
) -> None:
    from backend.app.main import create_app

    client = TestClient(create_app(), raise_server_exceptions=False)
    client.get("/v2/health")
    client.post("/v2/assistant/chat", json={"message": "Who wins the league?"})
    contract = _contract()
    forbidden = set(contract["forbidden_attribute_names"])
    seen: set[str] = set()
    for record in session_events:
        name = record.__dict__["event"]
        attributes = record.__dict__["attributes"]
        spec = contract["events"][name]
        required, optional = set(spec["required"]), set(spec["optional"])
        assert required <= set(attributes), (name, attributes)
        assert set(attributes) <= required | optional, (name, attributes)
        assert not forbidden & set(attributes), (name, attributes)
        seen.add(name)
    assert "http.request" in seen
