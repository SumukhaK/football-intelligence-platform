"""Markdown rendering for model comparison reports."""

from __future__ import annotations

from typing import Any

_FORECASTS = ["candidate", "current", "priors", "bookmaker"]
_TITLES = {
    "test": "Test seasons, all leagues",
    "holdout": "Holdout seasons, all leagues",
    "like_for_like": "Current model's own test matches (Premier League 2023/24)",
}


def render_markdown(report: dict[str, Any]) -> str:
    """Render a comparison report as Markdown tables plus a verdict."""
    lines = [
        "# Model Comparison",
        "",
        f"Candidate run: `{report['candidate_run']}`",
        "",
        "Lower is better for log loss, RPS and Brier. Rows without odds are",
        "excluded so every forecast is scored on the same matches. Bookmaker",
        "probabilities are a benchmark only; odds are never model inputs.",
    ]
    for key in ("like_for_like", "test", "holdout"):
        lines += ["", f"## {_TITLES[key]}", ""]
        for group, scores in report[key].items():
            if group.startswith("delta_"):
                continue
            lines += _table(group, scores)
        if key == "like_for_like":
            lines += _deltas(report[key])
    lines += _verdict(report["verdict"])
    return "\n".join(lines) + "\n"


def _table(group: str, scores: dict[str, dict[str, float]]) -> list[str]:
    """Render one group's forecasts as a Markdown table."""
    n = int(next(iter(scores.values()))["n"])
    rows = [
        f"**{group}** ({n} matches)",
        "",
        "| Forecast | Log loss | RPS | Brier | Accuracy |",
        "|---|---|---|---|---|",
    ]
    for name in _FORECASTS:
        if name in scores:
            s = scores[name]
            rows.append(
                f"| {name} | {s['log_loss']:.4f} | {s['rps']:.4f} | "
                f"{s['brier']:.4f} | {s['accuracy']:.3f} |"
            )
    return rows + [""]


def _deltas(block: dict[str, Any]) -> list[str]:
    """Render the paired bootstrap deltas of candidate minus current."""
    rows = [
        "Candidate minus current, paired bootstrap (negative favours candidate):",
        "",
    ]
    for key in ("delta_log_loss", "delta_rps"):
        d = block[key]
        rows.append(
            f"- {d['metric']}: {d['mean']:+.4f} "
            f"(95% interval {d['lower']:+.4f} to {d['upper']:+.4f}, "
            f"{d['n_resamples']} resamples)"
        )
    return rows


def _verdict(verdict: dict[str, Any]) -> list[str]:
    """Render the promotion verdict and each check."""
    rows = ["", "## Promotion verdict (ADR 007)", ""]
    rows.append("**Promote**" if verdict["promote"] else "**Do not promote**")
    rows.append("")
    for name, passed in verdict["checks"].items():
        rows.append(f"- {'pass' if passed else 'fail'}: {name.replace('_', ' ')}")
    return rows
