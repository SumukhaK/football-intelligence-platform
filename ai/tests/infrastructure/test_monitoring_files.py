"""Checks on the cloud metric and alert definitions (M6)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
MONITORING = ROOT / "infrastructure" / "monitoring"
EVENTS = ROOT / "docs" / "observability" / "telemetry-events.json"
METRIC_FILES = sorted((MONITORING / "metrics").glob("*.yaml"))
ALERT_FILES = sorted((MONITORING / "alerts").glob("*.json"))
_EVENT = re.compile(r'jsonPayload\.event="([^"]+)"')
_FILTER_METRIC = re.compile(r"logging\.googleapis\.com/user/(\w+)")
_PROMQL_METRIC = re.compile(r"logging_googleapis_com:user_(\w+?)(?:_bucket)?\{")
_PROJECT_OR_EMAIL = re.compile(
    r"projects/[a-z][a-z0-9-]{4,}|[\w.+-]+@[\w-]+\.[\w.]+|notificationChannels/\d"
)


def _metric(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text("utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _alert(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text("utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _known_events() -> set[str]:
    catalogue = json.loads(EVENTS.read_text("utf-8"))
    return set(catalogue["events"])


def _referenced_metrics(alert: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for condition in alert["conditions"]:
        threshold = condition.get("conditionThreshold", {}).get("filter", "")
        promql = condition.get("conditionPrometheusQueryLanguage", {}).get("query", "")
        names |= set(_FILTER_METRIC.findall(threshold))
        names |= set(_PROMQL_METRIC.findall(promql))
    return names


def test_there_are_metrics_and_alerts() -> None:
    assert len(METRIC_FILES) == 9
    assert len(ALERT_FILES) == 7


@pytest.mark.parametrize("path", METRIC_FILES, ids=lambda p: p.stem)
def test_metric_is_complete_and_named_after_its_file(path: Path) -> None:
    metric = _metric(path)
    assert {"name", "filter", "description"} <= metric.keys()
    assert metric["name"] == path.stem


@pytest.mark.parametrize("path", METRIC_FILES, ids=lambda p: p.stem)
def test_metric_filter_names_a_contract_event(path: Path) -> None:
    events = _EVENT.findall(_metric(path)["filter"])
    assert events, "the filter must select an event"
    assert set(events) <= _known_events()


@pytest.mark.parametrize("path", METRIC_FILES, ids=lambda p: p.stem)
def test_metric_labels_all_have_extractors(path: Path) -> None:
    metric = _metric(path)
    labels = {label["key"] for label in metric["metricDescriptor"].get("labels", [])}
    assert labels == set(metric.get("labelExtractors", {}))


@pytest.mark.parametrize("path", ALERT_FILES, ids=lambda p: p.stem)
def test_alert_is_documented_and_has_a_condition(path: Path) -> None:
    alert = _alert(path)
    assert alert["displayName"].startswith("football-api: ")
    assert alert["documentation"]["content"].strip()
    assert alert["conditions"]


@pytest.mark.parametrize("path", ALERT_FILES, ids=lambda p: p.stem)
def test_alert_uses_only_defined_metrics(path: Path) -> None:
    used = _referenced_metrics(_alert(path))
    assert used, "the alert must read a log-based metric"
    assert used <= {p.stem for p in METRIC_FILES}


@pytest.mark.parametrize(
    "path",
    [*METRIC_FILES, *ALERT_FILES, MONITORING / "apply.sh", MONITORING / "remove.sh"],
    ids=lambda p: p.name,
)
def test_no_project_id_email_or_channel_is_committed(path: Path) -> None:
    assert not _PROJECT_OR_EMAIL.search(path.read_text("utf-8"))
