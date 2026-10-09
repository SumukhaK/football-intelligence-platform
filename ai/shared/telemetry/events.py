"""The event catalogue (telemetry contract section 3) and how events are logged."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any


class EventName(StrEnum):
    """Every event the backend may emit."""

    HTTP_REQUEST = "http.request"
    APP_ERROR = "app.error"
    APP_CRASH = "app.crash"
    COMPONENT_LOAD = "component.load"
    COMPONENT_DEGRADED = "component.degraded"
    RATELIMIT_REJECTED = "ratelimit.rejected"
    AUTH_EVENT = "auth.event"
    REFRESH_RUN = "refresh.run"
    DATA_FRESHNESS = "data.freshness"
    ASSISTANT_ANSWER = "assistant.answer"
    ASSISTANT_TOOL = "assistant.tool"
    ASSISTANT_ABSTAIN = "assistant.abstain"
    DEPENDENCY_CALL = "dependency.call"
    RETRY = "retry"
    FALLBACK = "fallback"
    GUARDRAIL_EVENT = "guardrail.event"


_FIXED_LEVELS = {
    EventName.APP_CRASH: logging.ERROR,
    EventName.COMPONENT_DEGRADED: logging.WARNING,
    EventName.RATELIMIT_REJECTED: logging.WARNING,
    EventName.RETRY: logging.WARNING,
    EventName.FALLBACK: logging.WARNING,
}
# Events that are INFO when their `status` attribute is "ok", WARNING otherwise.
_OK_STATUS_EVENTS = frozenset(
    {
        EventName.COMPONENT_LOAD,
        EventName.REFRESH_RUN,
        EventName.ASSISTANT_TOOL,
        EventName.DEPENDENCY_CALL,
    }
)
_HTTP_STATUS_EVENTS = frozenset({EventName.HTTP_REQUEST, EventName.APP_ERROR})
_AUTH_WARNING_OUTCOMES = frozenset({"failed", "locked_out", "blocked"})


def _http_level(name: EventName, status: object) -> int:
    code = status if isinstance(status, int) else 0
    if code >= 500:
        return logging.ERROR
    if code >= 400 or name is EventName.APP_ERROR:
        return logging.WARNING
    return logging.INFO


def severity(name: EventName, attributes: dict[str, Any]) -> int:
    """Return the level the contract gives ``name`` with these attributes."""
    if name in _FIXED_LEVELS:
        return _FIXED_LEVELS[name]
    if name in _HTTP_STATUS_EVENTS:
        return _http_level(name, attributes.get("status"))
    if name in _OK_STATUS_EVENTS:
        return logging.INFO if attributes.get("status") == "ok" else logging.WARNING
    if name is EventName.AUTH_EVENT:
        warn = attributes.get("outcome") in _AUTH_WARNING_OUTCOMES
        return logging.WARNING if warn else logging.INFO
    return logging.INFO


def emit(
    logger: logging.Logger,
    name: EventName,
    message: str,
    *,
    level: int | None = None,
    **attributes: Any,
) -> None:
    """Log event ``name`` with ``attributes``, at the contract's level by default."""
    chosen = severity(name, attributes) if level is None else level
    logger.log(chosen, message, extra={"event": name.value, "attributes": attributes})
