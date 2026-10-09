"""Check the static landing page's local links, assets and essential metadata."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class SiteParser(HTMLParser):
    """Collect references and the page structure for a static smoke check."""

    def __init__(self) -> None:
        """Initialise the collected references and document markers."""
        super().__init__()
        self.references: list[str] = []
        self.ids: list[str] = []
        self.headings = 0
        self.lang = False
        self.viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record link targets, identifiers and required document markers."""
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(str(values["id"]))
        for key in ("href", "src", "poster"):
            if values.get(key):
                self.references.append(str(values[key]))
        self.headings += tag == "h1"
        self.lang |= tag == "html" and values.get("lang") == "en"
        self.viewport |= tag == "meta" and values.get("name") == "viewport"


def check_site(directory: Path) -> list[str]:
    """Return structural and local-reference errors for the site's index."""
    parser = SiteParser()
    parser.feed((directory / "index.html").read_text(encoding="utf-8"))
    errors: list[str] = []
    if parser.headings != 1 or not parser.lang or not parser.viewport:
        errors.append("Expected one h1, English lang and viewport metadata")
    if len(parser.ids) != len(set(parser.ids)):
        errors.append("Duplicate element ids")
    for reference in parser.references:
        target = urlsplit(reference)
        if target.scheme or target.netloc:
            continue
        if target.path.startswith("/"):
            errors.append(f"Root-relative URL breaks project Pages: {reference}")
            continue
        path = directory / unquote(target.path)
        if target.path and not path.is_file():
            errors.append(f"Missing asset: {reference}")
        if not target.path and target.fragment not in parser.ids:
            errors.append(f"Missing section: {reference}")
    return errors


if __name__ == "__main__":
    site = Path(__file__).resolve().parents[1] / "docs" / "site"
    problems = check_site(site)
    if problems:
        raise SystemExit("\n".join(problems))
    print("Site check passed: local assets, anchors, metadata and heading.")
