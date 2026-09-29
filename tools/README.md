# Tools

Shared CLI utilities for the Football Intelligence Platform.

---

## Ownership

Shared. Tools are reviewed before merge and must meet the same coding standards as application code.

---

## Purpose

Tools are reusable command-line utilities that multiple parts of the project depend on. Unlike scripts, tools are designed to be called repeatedly in different contexts.

---

## Rules

- Every tool is a standalone executable with a `--help` flag.
- Tools are typed (Python type annotations) and tested.
- Tools do not import from `backend/` or `ai/` application code. If shared logic is needed, extract it to a shared library.
- Tools read configuration from environment variables or explicit arguments. No hardcoded paths.

---

## Status

Empty. The project's command-line tools live in `ai/scripts/` and the pipeline
packages (`python -m training.pipeline` and similar); see
[docs/reference/cli.md](../docs/reference/cli.md).
