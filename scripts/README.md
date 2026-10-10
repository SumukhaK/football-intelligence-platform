# Scripts

Setup, automation, and migration scripts for the Football Intelligence Platform.

---

## Ownership

Shared. Any engineer may add scripts, but each script must be documented and reviewed before merge.

---

## Purpose

Scripts are one-off or operational tools that do not belong in the application codebase.

---

## Rules

- Every script has a docstring or header comment describing its purpose, inputs, and outputs.
- Scripts are idempotent where possible. Running a script twice must not corrupt state.
- Scripts do not contain business logic. Business logic belongs in `backend/` or `ai/`.
- No hardcoded credentials. Scripts read from environment variables or `.env`.
- Scripts that modify data must have a dry-run mode.

---

## Status

The website check lives in `check_site.py`. Run it from the repository root
with `python scripts/check_site.py` before publishing. It validates local
links, assets and document structure.

Application operational scripts live in `ai/scripts/`: backfill, live refresh,
fixtures refresh, crest tables and account management.
