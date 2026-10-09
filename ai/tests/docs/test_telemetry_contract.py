"""Tests that the telemetry contract's markdown and JSON copies agree."""

import json
import re
from pathlib import Path
from typing import Any

OBSERVABILITY_DIR = Path(__file__).resolve().parents[3] / "docs" / "observability"
CATALOGUE_ROW = re.compile(r"^\| `([a-z_.]+)` \|", re.MULTILINE)
VERSION_LINE = re.compile(r"^Version: (\S+)$", re.MULTILINE)


def _markdown() -> str:
    return (OBSERVABILITY_DIR / "telemetry-contract.md").read_text(encoding="utf-8")


def _events_json() -> dict[str, Any]:
    text = (OBSERVABILITY_DIR / "telemetry-events.json").read_text(encoding="utf-8")
    data: dict[str, Any] = json.loads(text)
    return data


def _catalogue_section(markdown: str) -> str:
    start = markdown.index("## 3. Event catalogue")
    end = markdown.index("### Component names", start)
    return markdown[start:end]


def test_json_and_markdown_list_the_same_events() -> None:
    markdown_events = set(CATALOGUE_ROW.findall(_catalogue_section(_markdown())))
    assert markdown_events == set(_events_json()["events"])


def test_version_strings_match() -> None:
    match = VERSION_LINE.search(_markdown())
    assert match is not None
    assert match.group(1) == _events_json()["contract_version"]
