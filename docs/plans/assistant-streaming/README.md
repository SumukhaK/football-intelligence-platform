# Assistant streaming: read me first

This folder plans and tracks streaming the assistant's answers to the app, word by word. It is built so any step can be handed to a fresh coding thread, and reviewed by another fresh thread, without either needing this conversation.

| File | What it is |
|---|---|
| [plan.md](plan.md) | Why, what stays the same, the design, effort and risks |
| [contract.md](contract.md) | The exact endpoint, events and duties both sides build to |
| [fixtures/](fixtures/) | Sample streams: the contract as files both sides test against |
| [tracker.md](tracker.md) | The 12 steps, their order, owners, status and evidence |
| [steps/](steps/) | One self-contained prompt per step |
| [review.md](review.md) | The prompt for reviewing any step's PR |

## How to run one step

1. Open [tracker.md](tracker.md) and pick the next step whose **Needs** are all `Done`.
2. Start a fresh thread or agent session on a clean clone of the repo. For parallel work, use a separate clone per thread (for example `football-intelligence-platform-st03` next to the main checkout).
3. Paste: "Do the step in `docs/plans/assistant-streaming/steps/STnn-....md` on the latest `develop`. Follow it exactly." The step file carries everything else: goal, files it may touch, design, the tests to write first, rules, commands and the reviewer checklist.
4. The thread writes the tests first and shows them failing (**Red**), makes them pass (**Green**), runs every command, checks by hand, updates the docs and its tracker row, and opens a PR into `develop`. Then it stops.
5. Start a second fresh thread for review: "Review PR #n against `docs/plans/assistant-streaming/review.md` and the step file it names." The reviewer fixes what it finds or asks for fixes, and merges into `develop` when everything passes.
6. Pull `develop` locally and start the next step.

## Disciplines every step follows

These are repeated inside each step file so no thread can miss them.

- **Tests first.** Every behaviour starts as a failing test. The PR shows the Red and Green runs.
- **One concern per PR.** A step does only what its file says. Anything else found on the way becomes a note in the PR, not a change.
- **Owned files only.** Each step lists the files it may touch; the tracker's ownership table stops parallel threads clashing.
- **The contract is fixed.** No step changes [contract.md](contract.md) or the fixtures. If one must change, that is its own docs PR first, and both lanes re-check against it.
- **Guardrails never weaken.** Safety check, budget, router, relevance cut-off, tool rounds and the grounding retry all still run before any word is sent. [review.md](review.md) lists the invariants.
- **Repo rules.** `.claude/CLAUDE.md` wins over everything here: 400-line files, 40-line functions, docstrings, Black/Ruff/mypy, detekt/spotless, strings in resources, previews, Conventional Commits, PRs into `develop`.
- **Green means green.** No test is skipped, deleted or weakened to pass. A failure that is not the PR's own is shown to be red on `develop` too and named in the PR.
- **Evidence or it did not happen.** Each step links its evidence in the tracker: PR, report, transcript or recording.

## Release

When ST11 is done, the release goes through the usual flow: a PR from `develop` to `main` with CI, the emulator smoke test and release notes, then a tag with the debug APK and AAB. That needs the owner's go-ahead.
