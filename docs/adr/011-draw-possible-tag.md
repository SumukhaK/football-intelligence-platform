# ADR 011 — Flag Possible Draws Without Changing the Pick

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The match model never makes a draw its most likely outcome, although about a
quarter of matches end level. The [draw report](../reports/draw-handling.md)
shows that its draw probabilities are well calibrated but never go above
about 0.36. A rule that picks draws more often loses accuracy fast: catching a
third of draws costs 4 to 5 points. Six draw-oriented features gave no
measurable gain.

Users still want to know when a draw is a real possibility. The decision taken
on 2026-09-28 was "tag only": keep the pick and flag tight games.

## Decision

1. `POST /predict` returns a new boolean, `draw_possible`. It is true when
   `probability_draw` is at least a threshold. `predicted_result` and
   `confidence` are unchanged.
2. The threshold is 0.28, read off 2022/23 only. Flagged matches draw about
   27% of the time at any threshold from 0.24 to 0.28, so the choice is how
   many matches to flag. A tag on most matches would mean nothing, so the
   threshold is the lowest that flags under a third of 2022/23 matches (30%).
   Those drew 27% of the time, against 23% for the rest. On 2023/24,
   2024/25–2025/26 and 2026/27 so far, flagged matches drew 31%, 28% and 35%
   of the time, against 25%, 24% and 18% for the rest, with 29% to 41% of
   matches flagged.
3. The threshold is a backend setting, `DRAW_POSSIBLE_THRESHOLD`, so it can be
   re-tuned when the model changes without an API change.
4. The field defaults to false, so older clients and older servers stay
   compatible.

## Consequences

- The app can show a "Draw possible" tag without any accuracy cost.
- The tag is a nudge, not a prediction: 7 in 10 flagged matches still have a
  winner. The app wording must not say a draw is likely.
- Any retrained model, or the Dixon-Coles blend (ADR 009), must re-run
  `evaluation.draw_analysis` and re-tune the threshold before release.
