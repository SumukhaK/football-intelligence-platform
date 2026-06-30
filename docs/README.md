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
| [Architecture Impact](architecture-impact.md) | How Stages 1–7 progressively built the architecture and what each stage enabled downstream |
| [ADR Index](adr/README.md) | All Architectural Decision Records |

### Stage Reports

| Document | Stage | Status |
|---|---|---|
| [Stage 04 Summary](reports/stage-04-summary.md) | Data Acquisition Framework | ✅ Complete |
| [Stage 05 Summary](reports/stage-05-summary.md) | Real Dataset Ingestion | ✅ Complete |
| [Stage 06 Summary](reports/stage-06-summary.md) | Feature Engineering | ✅ Complete |
| [Stage 07 Summary](reports/stage-07-summary.md) | Model Training & Evaluation | ✅ Complete |

### Demos

| Document | Description |
|---|---|
| [Demo Index](demo/README.md) | Overview of available demos |
| [Stage 5 Demo](demo/stage-05-demo.md) | Live data ingestion walkthrough |
| [Stage 6 Demo](demo/stage-06-demo.md) | Feature engineering walkthrough |
| [Stage 7 Demo](demo/stage-07-demo.md) | Model training and evaluation walkthrough |

### Troubleshooting

| Document | Description |
|---|---|
| [Troubleshooting Guide](troubleshooting.md) | Common issues and fixes for Python, uv, Android, and CI |

### Releases

| Document | Description |
|---|---|
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
