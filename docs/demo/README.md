# Demo Scripts

Step-by-step walkthroughs of the Football Intelligence Platform for technical interviews and code reviews.

---

## Purpose

These demos are designed for reviewers, recruiters, and interviewers who want to see the platform running end-to-end. Each demo covers one completed stage and can be run independently (given its prerequisites are met).

---

## Available Demos

| Demo | Stage | What you see | Time |
|---|---|---|---|
| [Stage 5 — Data Ingestion](stage-05-demo.md) | 5 | Live download, schema validation, versioned dataset | ~3 min |
| [Stage 6 — Feature Engineering](stage-06-demo.md) | 6 | 9 feature generators, 42-column feature matrix, validation | ~3 min |
| [Stage 7 — Model Training](stage-07-demo.md) | 7 | XGBoost training, evaluation, model card, registry | ~5 min |

---

## Prerequisites

All demos require:

1. A working AI workspace: `cd ai && uv sync --extra dev`
2. An internet connection (Stage 5 only)
3. The prior stage's outputs (see each demo for specifics)

---

## Recommended Order

For a full end-to-end demonstration, run the stages in order:

1. Stage 5 — produces the canonical dataset
2. Stage 6 — produces the feature matrix
3. Stage 7 — produces the trained model

Each stage can also be demonstrated individually using the pre-generated artifacts already committed to the repository.
