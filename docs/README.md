# Documentation

This directory contains all project documentation except code-level docstrings.

---

## Ownership

Maintained by the project architect. The implementation engineer updates documentation when architecture or behaviour changes, in the same commit as the change.

---

## Index

### Setup

| Document | Description |
|---|---|
| [Quick Start Guide](setup/quick-start.md) | Clone, install, run the full pipeline and build Android from scratch |

### Reference

| Document | Description |
|---|---|
| [API Reference](api.md) | Both API versions, every endpoint, request fields, responses, errors and the rate limit |
| [CLI Reference](reference/cli.md) | Every supported CLI command with options, examples, and expected output |
| [Repository Structure](repository-structure.md) | Every top-level directory: purpose, what belongs, what does not |

### Architecture

| Document | Description |
|---|---|
| [Architecture Impact](architecture-impact.md) | How Stages 1–7 built the architecture and what each stage enabled downstream (historical view) |
| [ADR Index](adr/README.md) | All Architectural Decision Records |

### Stage Reports

| Document | Stage | Status |
|---|---|---|
| [Stage 04 Summary](reports/stage-04-summary.md) | Data Acquisition Framework | ✅ Complete |
| [Stage 05 Summary](reports/stage-05-summary.md) | Real Dataset Ingestion | ✅ Complete |
| [Stage 06 Summary](reports/stage-06-summary.md) | Feature Engineering | ✅ Complete |
| [Stage 07 Summary](reports/stage-07-summary.md) | Model Training & Evaluation | ✅ Complete |
| [Stage 08 Summary](reports/stage-08-summary.md) | Explainable AI (SHAP) | ✅ Complete |
| [Stage 09 Summary](reports/stage-09-summary.md) | FastAPI Backend | ✅ Complete |
| [Stage 10 Summary](reports/stage-10-summary.md) | Football Intelligence Assistant | ✅ Complete |
| [Stage 11 Summary](reports/stage-11-summary.md) | Android Application | ✅ Complete |
| [Stage 12 Summary](reports/stage-12-summary.md) | End-to-End Integration | ✅ Complete |

### Plans

| Document | Description |
|---|---|
| [Next Phase Plan](plans/next-phase-plan.md) | Testing gaps, draw handling, scoreline predictions: order, design, impact analysis |
| [Five Leagues Plan](plans/five-leagues-plan.md) | Serving all five leagues in the API and app |
| [Multi-League Retraining Plan](plans/multi-league-retraining-plan.md) | Goal, data profile and phased plan for retraining on top-5 league data |
| [Multi-League Model Comparison](reports/multi-league-retraining-comparison.md) | Candidate vs current model, bookmaker and priors, with the promotion verdict |
| [2026/27 Live Check](reports/in-season-2026-27.md) | Served model scored on 2026/27 matches played up to 20 September 2026 (checked 28 September) |
| [Draw Handling](reports/draw-handling.md) | Why draws are a tag, not a pick |
| [Goals Model](reports/goals-model.md) | Dixon-Coles scoreline model and its evaluation |
| [Kaggle Extras](reports/kaggle-extras.md) | xG, FIFA ratings and Champions League rest days tested; none adopted |
| [UI/UX Review](reports/ui-ux-review.md) | App review against mobile design guidelines |

### Demos

| Document | Description |
|---|---|
| [Demo Index](demo/README.md) | Overview of all available demos |
| [Stage 5 Demo](demo/stage-05-demo.md) | Live data ingestion walkthrough |
| [Stage 6 Demo](demo/stage-06-demo.md) | Feature engineering walkthrough |
| [Stage 7 Demo](demo/stage-07-demo.md) | Model training and evaluation walkthrough |
| [Stage 8 Demo](demo/stage-08-demo.md) | SHAP explainability walkthrough |
| [Stage 9 Demo](demo/stage-09-demo.md) | FastAPI backend and REST API walkthrough |
| [Stage 10 Demo](demo/stage-10-demo.md) | AI assistant and RAG pipeline walkthrough |
| [Stage 11 Demo](demo/stage-11-demo.md) | Android application walkthrough |
| [Stage 12 Demo](demo/stage-12-demo.md) | End-to-end integration and validation walkthrough |

### Showcase

| Document | Description |
|---|---|
| [Project Showcase](showcase/project-showcase.md) | Full technical write-up: architecture, design decisions, AI engineering highlights |
| [Project Timeline](showcase/project-timeline.md) | Stage-by-stage build history with purpose, outcome, and deliverables |
| [Portfolio Summary](showcase/portfolio-summary.md) | Two-page recruiter-facing summary |
| [Interview Guide](showcase/interview-guide.md) | 50 likely interview questions with answers and trade-off reasoning |
| [Demo Script](showcase/demo-script.md) | 5/10/20-minute demo scripts with talking points and commands |
| [Screenshots](showcase/screenshots/README.md) | Screenshot capture checklist |
| [Demo Video](showcase/demo-video/README.md) | Demo video notes, captions and thumbnail |

### Troubleshooting

| Document | Description |
|---|---|
| [Troubleshooting Guide](troubleshooting.md) | Common issues and fixes for Python, uv, Android, the backend and CI |

### Releases

| Document | Description |
|---|---|
| [v2.1.0 Release Notes](releases/v2.1.0.md) | App icon, Kick-off launch screen and loader, branch flow |
| [v2.0.1 Release Notes](releases/v2.0.1.md) | Faster offline fallback in the app, demo video |
| [v2.0.0 Release Notes](releases/v2.0.0.md) | Five leagues, versioned API, fixtures, goals model, offline app |
| [v1.0.0 Release Notes](releases/v1.0.0.md) | Full release notes for the complete platform (Stages 1–12) |
| [v1.0.0 Readiness Report](releases/v1.0.0-readiness.md) | Final build, test, API, and CLI verification results |
| [v0.2.0 Release Notes](releases/v0.2.0.md) | Full release notes for Stages 1–10 |
| [v0.2.0 Readiness Report](releases/v0.2.0-readiness.md) | Build, test, API, and CLI verification results |
| [v0.1.0 Release Notes](releases/v0.1.0.md) | Full release notes for the first stable milestone |
| [v0.1.0 Readiness Report](releases/v0.1.0-readiness.md) | Build, test, and CLI verification results |

---

## Directory Structure

```
docs/
  adr/            # Architectural Decision Records
  demo/           # Stage-by-stage demo scripts for technical interviews
  plans/          # Plans for the follow-on phase after Stage 12
  reference/      # CLI command reference
  releases/       # Release notes and readiness reports
  reports/        # Stage summaries and model/data experiment reports
  setup/          # Installation and quick-start guides
  showcase/       # Recruiter-facing showcase: portfolio summary, timeline, interview guide, demo scripts, demo video
  README.md       # This index
  api.md          # API reference
  architecture-impact.md   # How Stages 1–7 built on each other
  repository-structure.md  # Directory ownership guide
  troubleshooting.md       # Common issues and fixes
```

The directory also holds empty placeholder folders (`ai/`, `architecture/`, `backend/`, `constitution/`, `decisions/`, `frontend/`, `prompts/`, `roadmap/`, `testing/`) that contain only a `.gitkeep`.

---

## Rules

- Every document reflects the current state of the system. Outdated documents are updated, not left to drift.
- Documents that define a contract (API spec, data schema) are updated in the same commit as the implementation.
- ADRs are never deleted. Superseded ADRs are marked Deprecated and a new ADR is written.
- No design document should be written in isolation. Every document is associated with a stage or an ADR.
