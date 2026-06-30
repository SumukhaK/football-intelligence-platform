# Football Intelligence Platform — Claude Code Context

## Project Overview
A full-stack football (soccer) intelligence platform that ingests match data, player stats, and tactical footage, then surfaces insights via AI-powered analysis and a web dashboard.

## Repo Structure
```
.claude/        # Claude Code config and this file
docs/           # Architecture docs, API specs, design decisions
playbook/       # Tactical playbooks and prompt templates
frontend/       # Web dashboard (to be defined)
backend/        # API server and data pipeline (to be defined)
ai/             # Models, agents, and inference code
datasets/       # Raw and processed football data
scripts/        # One-off and automation scripts
tools/          # Shared CLI tools and utilities
```

## Key Conventions
- Keep backend and frontend concerns strictly separated.
- All AI prompts and agent definitions live under `ai/`.
- Data transformations belong in `scripts/` (one-off) or `backend/` (production pipeline).
- Never commit raw credentials or API keys — use environment variables.

## Development Notes
- Stack and frameworks are not yet decided; update this file once chosen.
- Add architecture decision records (ADRs) to `docs/` as major choices are made.
