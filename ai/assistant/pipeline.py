"""AssistantPipeline — builds the knowledge index and runs queries."""

from __future__ import annotations

import logging

from assistant.chunking.chunker import TextChunker
from assistant.configuration import AssistantSettings
from assistant.embeddings.embedder import Embedder
from assistant.generation.generator import Generator
from assistant.ingestion.document import Document
from assistant.ingestion.loader import DocumentLoader
from assistant.prompting.templates import DEFAULT_MIN_RELEVANCE
from assistant.providers import make_provider
from assistant.retrieval.vector_store import IndexInfo, VectorStore
from assistant.services.assistant_service import AssistantResponse, AssistantService

logger = logging.getLogger(__name__)

_BATCH_SIZE = 32


class AssistantPipeline:
    """High-level facade for building the index and querying the assistant.

    Suitable for use from CLI scripts, backend startup, and notebooks.
    """

    def __init__(
        self,
        settings: AssistantSettings,
        embedder: Embedder | None = None,
        generator: Generator | None = None,
        min_relevance: float = DEFAULT_MIN_RELEVANCE,
    ) -> None:
        """Initialise with configuration and optional overrides.

        Without overrides the provider in ``settings`` embeds and answers.
        ``min_relevance`` is recorded in a newly built index with its
        embedding model; measure it for any model but nomic-embed-text.
        """
        self._settings = settings
        provider = make_provider(settings)
        self._embedder: Embedder = embedder or provider.embedder
        self._generator: Generator = generator or provider.generator
        self._chat_model = provider.chat_model
        self._info = IndexInfo(provider.embed_model, min_relevance)
        self._store: VectorStore | None = None

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def build_index(self, force_rebuild: bool = False) -> int:
        """Load, chunk, embed, and persist all knowledge documents.

        Returns the number of chunks indexed.
        Skips re-building if the store already exists and *force_rebuild* is
        False.
        """
        store_path = self._settings.vector_store_path
        if not force_rebuild and store_path.exists():
            logger.info("Vector store exists at %s — skipping build.", store_path)
            self._store = VectorStore.load(store_path)
            return self._store.size()

        logger.info(
            "Building knowledge index from %s …",
            self._settings.knowledge_base_root,
        )
        loader = DocumentLoader(self._settings.knowledge_base_root)
        documents = loader.load_all()

        if not documents:
            logger.warning("No documents found — index will be empty.")
            self._store = VectorStore()
            self._store.save(store_path)
            return 0

        chunker = TextChunker(
            chunk_size=self._settings.chunk_size,
            overlap=self._settings.chunk_overlap,
        )
        chunks = chunker.chunk_all(documents)
        logger.info("Chunked %d documents into %d chunks.", len(documents), len(chunks))

        store = VectorStore()
        store = _embed_and_add(chunks, self._embedder, store)
        store.info = self._info
        store.save(store_path)
        self._store = store
        logger.info("Index built: %d chunks → %s", store.size(), store_path)
        return store.size()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def load_index(self) -> None:
        """Load a previously built index from the configured path."""
        self._store = VectorStore.load(self._settings.vector_store_path)

    def get_service(self) -> AssistantService:
        """Return an :class:`AssistantService` backed by the loaded index.

        Raises :class:`IndexNotLoadedError` if the index has not been built or
        loaded.
        """
        if self._store is None:
            raise IndexNotLoadedError(
                "Call build_index() or load_index() before get_service()."
            )
        return AssistantService(
            embedder=self._embedder,
            generator=self._generator,
            store=self._store,
            model_name=self._chat_model,
            top_k=self._settings.top_k,
            min_relevance=(
                self._store.info.min_relevance
                if self._store.info
                else DEFAULT_MIN_RELEVANCE
            ),
        )

    def query(self, question: str) -> AssistantResponse:
        """Convenience method: load index (if needed) and answer *question*."""
        if self._store is None:
            self.load_index()
        return self.get_service().chat(question)


class IndexNotLoadedError(RuntimeError):
    """Raised when the vector store has not been loaded or built."""


def _embed_and_add(
    chunks: list[Document],
    embedder: Embedder,
    store: VectorStore,
) -> VectorStore:
    for i in range(0, len(chunks), _BATCH_SIZE):
        batch = chunks[i : i + _BATCH_SIZE]
        texts = [c.text for c in batch]
        embeddings = embedder.embed(texts)
        store.add(batch, embeddings)
        logger.debug("Embedded batch %d/%d", i + len(batch), len(chunks))
    return store


def main(argv: list[str] | None = None) -> int:
    """Build the index with the configured provider.

    Usage, from ``ai/``::

        uv run python -m assistant.pipeline --rebuild [--min-relevance 0.6]

    Set ``ASSISTANT_PROVIDER`` and ``ASSISTANT_VECTOR_STORE_PATH`` to build a
    Workers AI index next to the local one.
    """
    import argparse

    from assistant.configuration import get_assistant_settings

    parser = argparse.ArgumentParser(prog="assistant.pipeline")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--min-relevance", type=float, default=DEFAULT_MIN_RELEVANCE)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_assistant_settings()
    pipeline = AssistantPipeline(settings, min_relevance=args.min_relevance)
    n = pipeline.build_index(force_rebuild=args.rebuild)
    print(f"Index built: {n} chunks in {settings.vector_store_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
