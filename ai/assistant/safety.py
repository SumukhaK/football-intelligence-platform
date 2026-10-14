"""Llama Guard safety check on a user's question (ADR 027)."""

from __future__ import annotations

from collections.abc import Sequence

from assistant.generation.generator import Generator


class SafetyCheckError(RuntimeError):
    """Raised when the guard model's reply is neither safe nor unsafe."""


class SafetyCheck:
    """Asks a Llama Guard 3 model whether a question is harmful."""

    def __init__(self, guard: Generator) -> None:
        """Use ``guard``, a generator bound to a Llama Guard 3 model."""
        self._guard = guard

    def harmful_categories(
        self, question: str, earlier: Sequence[str] = ()
    ) -> list[str]:
        """The hazard codes (S1 to S14) the question falls under; empty if safe.

        ``earlier`` holds the user's previous questions in this chat (ADR 030),
        read together with this one so a request split across turns is caught.

        Raises:
            SafetyCheckError: The guard answered in an unexpected form.
        """
        text = "\n\n".join([*earlier, question])
        reply = self._guard.generate([{"role": "user", "content": text}])
        lines = [line.strip() for line in reply.strip().splitlines() if line.strip()]
        verdict = lines[0].lower() if lines else ""
        if verdict == "safe":
            return []
        if verdict == "unsafe":
            codes = lines[1].split(",") if len(lines) > 1 else []
            return [code.strip() for code in codes if code.strip()] or ["unknown"]
        raise SafetyCheckError("The safety model gave no verdict")
