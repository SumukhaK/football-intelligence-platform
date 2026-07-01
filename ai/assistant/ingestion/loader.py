"""DocumentLoader — reads local project artifacts into Document objects."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from assistant.ingestion.document import Document

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads knowledge documents from local project artifact directories.

    All paths are resolved relative to *root*, which should be the project's
    ``ai/`` directory when running inside the uv workspace.
    """

    def __init__(self, root: Path) -> None:
        """Initialise with the project root path."""
        self._root = root

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_all(self) -> list[Document]:
        """Load all available knowledge documents."""
        docs: list[Document] = []
        docs.extend(self._load_markdown_files())
        docs.extend(self._load_json_files())
        logger.info("Loaded %d documents from knowledge base.", len(docs))
        return docs

    # ------------------------------------------------------------------
    # Markdown loaders
    # ------------------------------------------------------------------

    def _load_markdown_files(self) -> list[Document]:
        docs: list[Document] = []
        patterns = [
            ("models", "**/*.md", "model_card"),
            ("../docs/adr", "*.md", "adr"),
            ("../docs/reports", "*.md", "report"),
            ("../docs", "*.md", "documentation"),
        ]
        for rel_dir, glob_pat, doc_type in patterns:
            base = self._root / rel_dir
            if not base.exists():
                continue
            for path in sorted(base.glob(glob_pat)):
                doc = self._read_markdown(path, doc_type)
                if doc is not None:
                    docs.append(doc)
        return docs

    def _read_markdown(self, path: Path, doc_type: str) -> Document | None:
        try:
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                return None
            return Document(
                id=path.stem,
                text=text,
                source=str(path),
                doc_type=doc_type,
                metadata={"filename": path.name, "type": doc_type},
            )
        except OSError as exc:
            logger.warning("Could not read %s: %s", path, exc)
            return None

    # ------------------------------------------------------------------
    # JSON loaders
    # ------------------------------------------------------------------

    def _load_json_files(self) -> list[Document]:
        docs: list[Document] = []
        json_targets = [
            ("models/latest/evaluation_report.json", "evaluation_report"),
            ("models/latest/metrics.json", "metrics"),
            ("models/latest/config.json", "model_config"),
            ("explanations/global_summary.json", "shap_global_summary"),
            ("../datasets/features/feature_metadata.json", "feature_metadata"),
            (
                "../datasets/features/feature_generation_report.json",
                "feature_report",
            ),
        ]
        for rel_path, doc_type in json_targets:
            full = self._root / rel_path
            if not full.exists():
                continue
            doc = self._read_json(full, doc_type)
            if doc is not None:
                docs.append(doc)
        return docs

    def _read_json(self, path: Path, doc_type: str) -> Document | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(data, indent=2)
            return Document(
                id=path.stem,
                text=text,
                source=str(path),
                doc_type=doc_type,
                metadata={"filename": path.name, "type": doc_type},
            )
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read %s: %s", path, exc)
            return None
