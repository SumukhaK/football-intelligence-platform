"""AssistantPipeline — builds the knowledge index and runs queries."""

from __future__ import annotations

import logging

from assistant.chunking.chunker import TextChunker
from assistant.configuration import AssistantSettings
from assistant.embeddings.embedder import Embedder, OllamaEmbedder
from assistant.generation.generator import Generator, OllamaGenerator
from assistant.ingestion.document import Document
from assistant.ingestion.loader import DocumentLoader
from assistant.retrieval.vector_store import VectorStore
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
    ) -> None:
        """Initialise the pipeline with configuration and optional overrides."""
        self._settings = settings
        self._embedder: Embedder = embedder or OllamaEmbedder(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        self._generator: Generator = generator or OllamaGenerator(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
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
            model_name=self._settings.ollama_chat_model,
            top_k=self._settings.top_k,
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


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from assistant.configuration import get_assistant_settings

    _settings = get_assistant_settings()
    _pipeline = AssistantPipeline(_settings)
    n = _pipeline.build_index(force_rebuild="--rebuild" in sys.argv)
    print(f"Index built: {n} chunks in {_settings.vector_store_path}")
