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
| [CLI Reference](reference/cli.md) | Every supported CLI command with options, examples, and expected output |
| [Repository Structure](repository-structure.md) | Every top-level directory: purpose, what belongs, what does not |

### Architecture

| Document | Description |
|---|---|
| [Architecture Impact](architecture-impact.md) | How Stages 1–12 progressively built the architecture and what each stage enabled downstream |
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

### Troubleshooting

| Document | Description |
|---|---|
| [Troubleshooting Guide](troubleshooting.md) | Common issues and fixes for Python, uv, Android, and CI |

### Releases

| Document | Description |
|---|---|
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
  reference/      # CLI command reference and API specifications
  releases/       # Release notes and readiness reports
  reports/        # Stage completion summaries
  setup/          # Installation and quick-start guides
  showcase/       # Recruiter-facing showcase: portfolio summary, timeline, interview guide, demo scripts
  README.md       # This index
  architecture-impact.md   # How stages built on each other
  repository-structure.md  # Directory ownership guide
  troubleshooting.md       # Common issues and fixes
```

---

## Rules

- Every document reflects the current state of the system. Outdated documents are updated, not left to drift.
- Documents that define a contract (API spec, data schema) are updated in the same commit as the implementation.
- ADRs are never deleted. Superseded ADRs are marked Deprecated and a new ADR is written.
- No design document should be written in isolation. Every document is associated with a stage or an ADR.
