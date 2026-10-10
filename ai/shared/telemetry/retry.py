"""Retries with backoff for outbound calls, recording every attempt (contract 3, 4)."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from shared.telemetry.events import EventName, emit
from shared.telemetry.tracing import tracer

AttemptStatus = Literal["timeout", "http_error", "connection_error", "error"]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryPolicy:
    """How many times and how long to wait between attempts."""

    max_attempts: int
    base_delay_s: float = 0.5
    max_delay_s: float = 8.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("RetryPolicy.max_attempts must be at least 1.")


@dataclass(frozen=True)
class AttemptOutcome:
    """How a failed attempt is reported, and whether it may be retried."""

    status: AttemptStatus
    http_status: int | None = None
    retryable: bool = False
    retry_after_s: float | None = None
    cause: str | None = None

    @property
    def reason(self) -> str:
        """The ``cause`` logged on a retry: given, the HTTP status, or the status."""
        if self.cause is not None:
            return self.cause
        if self.http_status is not None:
            return f"http_{self.http_status}"
        return self.status


class RetryableError(Exception):
    """Raised by a call to say this attempt may be retried."""

    def __init__(self, cause: str, retry_after_s: float | None = None) -> None:
        super().__init__(cause)
        self.cause = cause
        self.retry_after_s = retry_after_s


def classify_retryable(exc: Exception) -> AttemptOutcome:
    """Retry a ``RetryableError``; treat anything else as a final error."""
    if isinstance(exc, RetryableError):
        return AttemptOutcome("error", None, True, exc.retry_after_s, exc.cause)
    return AttemptOutcome("error")


def backoff_wait(
    policy: RetryPolicy, attempt: int, outcome: AttemptOutcome, rng: random.Random
) -> float:
    """Seconds to wait after failed ``attempt``: Retry-After, else full jitter."""
    if outcome.retry_after_s is not None:
        return min(outcome.retry_after_s, policy.max_delay_s)
    ceiling = min(policy.max_delay_s, policy.base_delay_s * 2 ** (attempt - 1))
    return rng.uniform(0, ceiling)


@dataclass(frozen=True)
class _Call:
    dependency: str
    operation: str
    policy: RetryPolicy


def _record_attempt(
    call: _Call, attempt: int, outcome: AttemptOutcome | None, duration_s: float
) -> None:
    emit(
        logger,
        EventName.DEPENDENCY_CALL,
        f"Call to {call.dependency} finished.",
        dependency=call.dependency,
        operation=call.operation,
        status="ok" if outcome is None else outcome.status,
        http_status=None if outcome is None else outcome.http_status,
        attempt=attempt,
        duration_ms=round(duration_s * 1000),
    )


def _record_retry(
    call: _Call, span: trace.Span, attempt: int, wait_s: float, cause: str
) -> None:
    wait_ms = round(wait_s * 1000)
    span.add_event("retry", {"attempt": attempt, "wait_ms": wait_ms, "cause": cause})
    emit(
        logger,
        EventName.RETRY,
        f"Call to {call.dependency} failed; retrying.",
        dependency=call.dependency,
        operation=call.operation,
        attempt=attempt,
        max_attempts=call.policy.max_attempts,
        wait_ms=wait_ms,
        cause=cause,
    )


def call_with_retry[T](
    fn: Callable[[], T],
    *,
    dependency: str,
    operation: str,
    policy: RetryPolicy,
    classify: Callable[[Exception], AttemptOutcome] = classify_retryable,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> T:
    """Call ``fn`` until it succeeds, fails for good or runs out of attempts.

    Only pass idempotent calls (GETs): a retried call may have run already.
    The last exception is re-raised unchanged.
    """
    call = _Call(dependency, operation, policy)
    jitter = rng if rng is not None else random.Random()
    attempt = 1
    while True:
        with tracer().start_as_current_span(
            f"dependency.{dependency}", attributes={"attempt": attempt}
        ) as span:
            started = clock()
            try:
                result = fn()
            except Exception as exc:
                outcome = classify(exc)
                _record_attempt(call, attempt, outcome, clock() - started)
                if not outcome.retryable or attempt >= policy.max_attempts:
                    raise
                span.set_status(StatusCode.ERROR, outcome.reason)
                wait_s = backoff_wait(policy, attempt, outcome, jitter)
                _record_retry(call, span, attempt, wait_s, outcome.reason)
            else:
                _record_attempt(call, attempt, None, clock() - started)
                return result
        sleep(wait_s)
        attempt += 1
