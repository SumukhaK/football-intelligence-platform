"""Tests for the draw calibration and draw-rule analysis."""

from __future__ import annotations

import numpy as np

from evaluation.draw_analysis import (
    analyse_block,
    draw_calibration,
    draw_rule_tradeoff,
    pick_with_draw_margin,
)

CLASSES = ["A", "D", "H"]
PROBS = np.array(
    [
        [0.20, 0.30, 0.50],  # home clear favourite
        [0.36, 0.31, 0.33],  # tight game, draw 0.05 behind
        [0.60, 0.25, 0.15],  # away clear favourite
        [0.34, 0.33, 0.33],  # draw 0.01 behind
    ]
)
ACTUAL = np.array(["H", "D", "A", "D"])


def test_zero_margin_is_the_plain_most_likely_pick() -> None:
    picks = pick_with_draw_margin(PROBS, CLASSES, 0.0)
    assert picks.tolist() == ["H", "A", "A", "A"]


def test_margin_turns_close_games_into_draws() -> None:
    picks = pick_with_draw_margin(PROBS, CLASSES, 0.05)
    assert picks.tolist() == ["H", "D", "A", "D"]


def test_margin_works_whatever_the_class_order() -> None:
    order = ["H", "D", "A"]
    reordered = PROBS[:, [2, 1, 0]]
    picks = pick_with_draw_margin(reordered, order, 0.05)
    assert picks.tolist() == ["H", "D", "A", "D"]


def test_tradeoff_reports_accuracy_and_draws_caught() -> None:
    rows = {r["margin"]: r for r in draw_rule_tradeoff(PROBS, ACTUAL, CLASSES)}
    assert rows[0.0]["accuracy"] == 0.5
    assert rows[0.0]["draws_caught"] == 0.0
    assert rows[0.05]["accuracy"] == 1.0
    assert rows[0.05]["draws_caught"] == 1.0


def test_calibration_bins_compare_predicted_and_observed() -> None:
    bins = draw_calibration(PROBS, ACTUAL, CLASSES)
    assert sum(b["matches"] for b in bins) == len(ACTUAL)
    top = bins[-1]
    assert top["matches"] == 2
    assert top["observed"] == 1.0


def test_block_summary() -> None:
    block = analyse_block(PROBS, ACTUAL, CLASSES)
    assert block["matches"] == 4
    assert block["draw_rate"] == 0.5
    assert block["max_draw_probability"] == 0.33
