"""Measures where the retrieval cut-off belongs for an index's embedding model.

Embeds the abstention eval's questions with the configured provider and prints
each one's best retrieval score. In-scope questions should score above every
out-of-scope one; the cut-off goes between the two groups and is recorded in
the index with ``python -m assistant.pipeline --rebuild --min-relevance X``
(ADR 025). Run from ``ai/`` with the provider and index you want to measure:

    ASSISTANT_PROVIDER=workers_ai VECTOR_STORE_PATH=assistant/vector_store_workers_ai \\
        uv run python -m evaluation.relevance_cutoff
"""

from __future__ import annotations

from dataclasses import dataclass

from assistant.configuration import get_assistant_settings
from assistant.embeddings.embedder import Embedder
from assistant.providers import make_provider
from assistant.retrieval.retriever import retrieve
from assistant.retrieval.vector_store import VectorStore
from evaluation.assistant_abstention import ANSWERABLE, UNANSWERABLE


@dataclass(frozen=True)
class Separation:
    """The best scores of both groups and whether a cut-off separates them."""

    lowest_in_scope: float
    highest_out_of_scope: float

    @property
    def separable(self) -> bool:
        """True when every in-scope question beats every out-of-scope one."""
        return self.lowest_in_scope > self.highest_out_of_scope

    @property
    def cut_off(self) -> float:
        """Midway between the groups, rounded to two places."""
        return round((self.lowest_in_scope + self.highest_out_of_scope) / 2, 2)


def top_scores(
    questions: tuple[str, ...], embedder: Embedder, store: VectorStore
) -> dict[str, float]:
    """Each question's best retrieval score against ``store``."""
    vectors = embedder.embed(list(questions))
    return {
        question: retrieve(vector, store, 1)[0][1]
        for question, vector in zip(questions, vectors, strict=True)
    }


def separation(
    in_scope: dict[str, float], out_of_scope: dict[str, float]
) -> Separation:
    """How far apart the two groups' best scores are."""
    return Separation(min(in_scope.values()), max(out_of_scope.values()))


def main() -> int:
    """Print every score and the suggested cut-off; 1 if none separates them."""
    settings = get_assistant_settings()
    store = VectorStore.load(settings.vector_store_path)
    embedder = make_provider(settings).embedder
    groups = {
        "in scope": top_scores(ANSWERABLE, embedder, store),
        "out of scope": top_scores(UNANSWERABLE, embedder, store),
    }
    for label, scores in groups.items():
        print(f"{label}:")
        for question, score in sorted(scores.items(), key=lambda item: item[1]):
            print(f"  {score:.3f}  {question}")
    result = separation(groups["in scope"], groups["out of scope"])
    print(f"lowest in scope {result.lowest_in_scope:.3f}, ", end="")
    print(f"highest out of scope {result.highest_out_of_scope:.3f}")
    if not result.separable:
        print("No cut-off separates the groups; the prompt must do the rest.")
        return 1
    print(f"Suggested --min-relevance {result.cut_off}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
