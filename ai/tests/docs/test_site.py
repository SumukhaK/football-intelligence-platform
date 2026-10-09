"""Check project Pages references before publishing the landing page."""

from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[3]
CHECK = cast(
    Callable[[Path], list[str]],
    runpy.run_path(str(ROOT / "scripts" / "check_site.py"))["check_site"],
)


def test_committed_site_has_no_broken_local_references() -> None:
    """The committed landing page must work at a project Pages subpath."""
    assert CHECK(ROOT / "docs" / "site") == []


def test_checker_reports_missing_assets_and_sections(tmp_path: Path) -> None:
    """Missing assets and anchor targets must fail before deployment."""
    (tmp_path / "index.html").write_text(
        '<html lang="en"><meta name="viewport"><h1>Page</h1>'
        '<a href="#missing">Section</a><img src="missing.png"></html>',
        encoding="utf-8",
    )
    errors = CHECK(tmp_path)
    assert "Missing section: #missing" in errors
    assert "Missing asset: missing.png" in errors


def test_checker_rejects_root_relative_urls(tmp_path: Path) -> None:
    """Root-relative assets would escape the repository's Pages URL prefix."""
    (tmp_path / "index.html").write_text(
        '<html lang="en"><meta name="viewport"><h1>Page</h1>'
        '<img src="/styles.css"></html>',
        encoding="utf-8",
    )
    assert CHECK(tmp_path) == ["Root-relative URL breaks project Pages: /styles.css"]
