"""Tests for assistant.tools.tool."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from assistant.tools.tool import Tool, ToolError, run_tool, run_tool_checked


def _echo(args: Mapping[str, Any]) -> dict[str, Any]:
    return {"echo": dict(args)}


def _fails(args: Mapping[str, Any]) -> None:
    raise ToolError("'Atlantis' did not play in Premier League 2026-2027")


def _crashes(args: Mapping[str, Any]) -> None:
    raise RuntimeError("bug")


TOOLS = [
    Tool("echo", "Echo the arguments.", {"type": "object"}, _echo),
    Tool("fails", "Always fails.", {"type": "object"}, _fails),
    Tool("crashes", "Raises a bug.", {"type": "object"}, _crashes),
]


def test_schema_uses_function_calling_format() -> None:
    """schema() wraps name, description and parameters as a function tool."""
    schema = TOOLS[0].schema()
    assert schema == {
        "type": "function",
        "function": {
            "name": "echo",
            "description": "Echo the arguments.",
            "parameters": {"type": "object"},
        },
    }


def test_run_tool_returns_result_as_json() -> None:
    """run_tool serialises the handler's result."""
    result = run_tool(TOOLS, "echo", {"home_team": "Arsenal"})
    assert json.loads(result) == {"echo": {"home_team": "Arsenal"}}


def test_run_tool_reports_tool_error_to_the_model() -> None:
    """An expected failure comes back as an error message, not an exception."""
    result = json.loads(run_tool(TOOLS, "fails", {}))
    assert result == {"error": "'Atlantis' did not play in Premier League 2026-2027"}


def test_run_tool_reports_unknown_tool() -> None:
    """A tool name the model made up comes back as an error message."""
    assert "Unknown tool 'guess'" in json.loads(run_tool(TOOLS, "guess", {}))["error"]


def test_run_tool_propagates_unexpected_errors() -> None:
    """Bugs in a handler are loud, not hidden from the caller."""
    with pytest.raises(RuntimeError, match="bug"):
        run_tool(TOOLS, "crashes", {})


def test_run_tool_checked_reports_the_error_it_hides() -> None:
    """The model sees the same JSON; the caller also learns that it failed."""
    failed = run_tool_checked(TOOLS, "fails", {})
    assert failed.content == run_tool(TOOLS, "fails", {})
    assert failed.error == "'Atlantis' did not play in Premier League 2026-2027"
    assert run_tool_checked(TOOLS, "echo", {}).error is None
    assert run_tool_checked(TOOLS, "guess", {}).error == "Unknown tool 'guess'."
