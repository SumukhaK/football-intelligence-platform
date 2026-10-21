"""Daily token budgets for the assistant: one per user and one for everyone (ADR 036).

A question starts only if both budgets still cover a typical answer; the
answer's actual tokens are charged afterwards, so one answer may run slightly
over and the next question is refused. Refusals and router replies use no
model and cost nothing. Budgets reset at midnight UTC.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.app.services.account_store import AccountStore
from backend.app.services.auth_errors import AuthError

# Usage rows outlive their day briefly, then a Firestore TTL policy deletes them.
_KEEP_USAGE = timedelta(days=2)


class BudgetExhaustedError(AuthError):
    """Today's assistant budget, the user's or everyone's, is used up."""

    status_code, error = 429, "Daily limit reached"
    outcome = "budget_exhausted"


@dataclass(frozen=True)
class Allowance:
    """What is left today, for the app's "about N questions left"."""

    questions_left: int
    resets_at: datetime


class AssistantBudget:
    """Checks and charges the per-user and global daily token budgets."""

    def __init__(
        self,
        store: AccountStore,
        per_user: int | None,
        total: int | None,
        tokens_per_answer: int,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        """Budgets in tokens a day; None turns that budget off."""
        self._store = store
        self._per_user = per_user
        self._total = total
        self._typical = tokens_per_answer
        self._clock = clock

    def check(self, email: str) -> None:
        """Refuse before the model runs when a typical answer no longer fits.

        Raises:
            BudgetExhaustedError: With a message saying when it resets.
        """
        day = self._day()
        if self._left(self._total, f"{day}_all") < self._typical:
            raise BudgetExhaustedError(
                "The assistant has answered all it can for today. "
                "Come back after midnight UTC; predictions still work."
            )
        if self._left(self._per_user, f"{day}_{email}") < self._typical:
            raise BudgetExhaustedError(
                "You've used today's questions. Come back after midnight UTC."
            )

    def charge(self, email: str, tokens: int | None) -> None:
        """Count an answer's tokens; an unreported count is a typical answer."""
        used = self._typical if tokens is None else tokens
        if used <= 0:
            return
        day, expires = self._day(), self._clock() + _KEEP_USAGE
        if self._total is not None:
            self._store.add_usage(f"{day}_all", used, expires)
        if self._per_user is not None:
            self._store.add_usage(f"{day}_{email}", used, expires)

    def allowance(self, email: str) -> Allowance | None:
        """Questions left for ``email`` today, or None when no budget applies."""
        if self._per_user is None and self._total is None:
            return None
        day = self._day()
        left = min(
            self._left(self._per_user, f"{day}_{email}"),
            self._left(self._total, f"{day}_all"),
        )
        midnight = datetime.combine(
            self._clock().date() + timedelta(days=1), datetime.min.time(), UTC
        )
        return Allowance(max(left, 0) // self._typical, midnight)

    def _left(self, budget: int | None, key: str) -> int:
        if budget is None:
            return 2**31
        return budget - self._store.usage(key)

    def _day(self) -> str:
        return self._clock().astimezone(UTC).date().isoformat()
