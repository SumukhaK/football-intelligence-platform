"""Tests for call_with_retry: attempts, backoff, events and spans."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from shared.telemetry.retry import (
    AttemptOutcome,
    RetryableError,
    RetryPolicy,
    backoff_wait,
    call_with_retry,
)

Events = Callable[[str], list[tuple[str, dict[str, Any]]]]


class _Flaky:
    """Fails with each queued error in turn, then returns ``"ok"``."""

    def __init__(self, *errors: Exception) -> None:
        self._errors = list(errors)
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        if self._errors:
            raise self._errors.pop(0)
        return "ok"


def _timeout(exc: Exception) -> AttemptOutcome:
    if isinstance(exc, TimeoutError):
        return AttemptOutcome("timeout", retryable=True)
    if isinstance(exc, RetryableError):
        return AttemptOutcome("http_error", 429, True, exc.retry_after_s)
    return AttemptOutcome("http_error", 404)


def _call(fn: _Flaky, attempts: int = 3, **kwargs: Any) -> tuple[str, list[float]]:
    waits: list[float] = []
    result = call_with_retry(
        fn,
        dependency="football_data",
        operation="get",
        policy=RetryPolicy(max_attempts=attempts),
        classify=kwargs.pop("classify", _timeout),
        sleep=waits.append,
        rng=random.Random(1),
        clock=lambda: 0.0,
        **kwargs,
    )
    return result, waits


def test_success_first_time_records_one_call_and_no_retry(events: Events) -> None:
    assert _call(_Flaky()) == ("ok", [])
    ((level, attrs),) = events("dependency.call")
    assert level == "INFO"
    assert attrs == {
        "dependency": "football_data",
        "operation": "get",
        "status": "ok",
        "http_status": None,
        "attempt": 1,
        "duration_ms": 0,
    }
    assert events("retry") == []


def test_two_timeouts_then_success(events: Events) -> None:
    fn = _Flaky(TimeoutError(), TimeoutError())
    result, waits = _call(fn)
    assert result == "ok"
    assert waits == pytest.approx([0.06718212205620061, 0.8474337369372327])
    calls = events("dependency.call")
    assert [a["status"] for _, a in calls] == ["timeout", "timeout", "ok"]
    assert [a["attempt"] for _, a in calls] == [1, 2, 3]
    assert [lvl for lvl, _ in calls] == ["WARNING", "WARNING", "INFO"]
    retries = events("retry")
    assert [(a["attempt"], a["wait_ms"], a["cause"]) for _, a in retries] == [
        (1, 67, "timeout"),
        (2, 847, "timeout"),
    ]
    assert all(a["max_attempts"] == 3 for _, a in retries)


def test_exhausted_attempts_reraise_the_last_error(events: Events) -> None:
    last = TimeoutError("third")
    fn = _Flaky(TimeoutError("first"), TimeoutError("second"), last)
    with pytest.raises(TimeoutError) as raised:
        _call(fn)
    assert raised.value is last
    assert fn.calls == 3
    assert len(events("retry")) == 2


def test_non_retryable_failure_is_not_retried(events: Events) -> None:
    fn = _Flaky(KeyError("missing"))
    with pytest.raises(KeyError):
        _call(fn)
    assert fn.calls == 1
    ((_, attrs),) = events("dependency.call")
    assert (attrs["status"], attrs["http_status"]) == ("http_error", 404)
    assert events("retry") == []


def test_retry_after_is_used_and_capped() -> None:
    fn = _Flaky(RetryableError("rate", 2.0), RetryableError("rate", 60.0))
    assert _call(fn) == ("ok", [2.0, 8.0])


def test_max_attempts_one_never_sleeps() -> None:
    with pytest.raises(TimeoutError):
        _call(_Flaky(TimeoutError()), attempts=1)


def test_policy_needs_at_least_one_attempt() -> None:
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_backoff_ceiling_doubles_up_to_the_cap() -> None:
    policy = RetryPolicy(max_attempts=10, base_delay_s=1.0, max_delay_s=4.0)
    outcome = AttemptOutcome("timeout", retryable=True)

    class _Top(random.Random):
        def uniform(self, a: float, b: float) -> float:
            return b

    waits = [backoff_wait(policy, n, outcome, _Top()) for n in range(1, 6)]
    assert waits == [1.0, 2.0, 4.0, 4.0, 4.0]


def test_default_classifier_retries_only_retryable_error(events: Events) -> None:
    waits: list[float] = []
    fn = _Flaky(RetryableError("busy"))
    policy = RetryPolicy(max_attempts=2)
    result = call_with_retry(
        fn,
        dependency="openfootball",
        operation="get",
        policy=policy,
        sleep=waits.append,
    )
    assert result == "ok"
    ((_, attrs),) = events("retry")
    assert attrs["cause"] == "busy"
    with pytest.raises(KeyError):
        call_with_retry(
            _Flaky(KeyError()),
            dependency="openfootball",
            operation="get",
            policy=policy,
        )


def test_each_attempt_has_a_span_with_retry_events(
    spans: InMemorySpanExporter,
) -> None:
    _call(_Flaky(TimeoutError()))
    recorded = spans.get_finished_spans()
    assert [s.name for s in recorded] == ["dependency.football_data"] * 2
    assert [s.attributes and s.attributes["attempt"] for s in recorded] == [1, 2]
    (event,) = recorded[0].events
    assert event.name == "retry"
    assert dict(event.attributes or {}) == {
        "attempt": 1,
        "wait_ms": 67,
        "cause": "timeout",
    }
    assert recorded[1].events == ()
