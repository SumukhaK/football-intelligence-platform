"""Tool definitions the assistant offers the chat model (ADR 018)."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

ToolHandler = Callable[[Mapping[str, Any]], Any]


class ToolError(Exception):
    """An expected tool failure, such as an unknown team, shown to the model."""


@dataclass(frozen=True)
class Tool:
    """A function the chat model may call, described by a JSON schema."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def schema(self) -> dict[str, Any]:
        """Return the tool in the Ollama / OpenAI function-calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def run_tool(tools: Sequence[Tool], name: str, arguments: Mapping[str, Any]) -> str:
    """Run the named tool and return its result as JSON for the model.

    Expected failures (:class:`ToolError`, an unknown tool name) come back as
    ``{"error": ...}`` so the model can tell the user. Anything else propagates.
    """
    tool = next((t for t in tools if t.name == name), None)
    if tool is None:
        return json.dumps({"error": f"Unknown tool '{name}'."})
    try:
        result = tool.handler(arguments)
    except ToolError as exc:
        return json.dumps({"error": str(exc)})
    return json.dumps(result, default=str)
