# UI/UX Review Against the Mobile App UI Design Skill

**Date:** 2026-09-29
**Reference:** [ceorkm/mobile-app-ui-design](https://github.com/ceorkm/mobile-app-ui-design) (SKILL.md and references), read as guidance only
**Screens reviewed:** home, team selection, result with insights, explanation, settings

## Where the app already matched

| Principle | Our app |
|---|---|
| Design every state: loading, empty, error, success | Every screen has a `Loading`, `Success` and `Error` state with previews (ADR 010) |
| Tap targets at least 44pt | Material 3 buttons, list items and dropdowns are 48dp |
| One font family, hierarchy by size and weight | Material 3 type scale on one family |
| Consistency across the app (the "comfort trap") | Shared cards, back button, error and loading views in `core-ui` |
| Visual cues over plain text | Probability and score bars, a draw tag, icons on home cards |
| Accessibility | Content descriptions on dropdowns, score rows and market rows |

## Gaps found and fixed in this change

| Principle | Before | After |
|---|---|---|
| Primary actions in the thumb zone | Explain and New prediction sat below every insight card, several screens down | Pinned in a bottom bar, always in reach |
| Emphasise values over labels | Percentages had the same weight as their labels | Percentages use a heavier style than labels |
| 60/30/10 colour; save strong colour for moments that matter | The headline card was a large saturated green block | A soft container, with the accent kept for the pick itself |
| Remove what does not serve the user | The result card showed the model version | Removed from the result. It stays on the explanation and settings screens |
| Peak moment | The result appeared all at once | Probability bars fill in as the result appears |
| F-pattern, key action first | Home opened with a developer-facing server status card | Home opens with Predict. Server status moves to the end |
| Empty or disabled states give guidance | The assistant button was greyed out with no reason | A muted line explains that the assistant needs Ollama running on the server |
| 8-point grid | 1, 2, 10 and 20dp spacings | 4, 12 and 24dp |
| Short, scannable labels | "Explain This Prediction" wrapped onto two lines | "Explain" and "New prediction" |

## Not adopted, with reasons

- **Glassmorphism, glow and gradient effects.** The skill itself warns against
  overusing them, and they fight the calm, data-first feel a prediction app needs.
- **Celebration animations for correct predictions.** The app does not yet know
  a result after the match. This is worth revisiting if match outcomes are ever
  tracked per user.
- **Personalisation by user stage.** There are no accounts (a non-goal in
  CLAUDE.md).
- **Friendly error copy for server errors.** Messages such as "HTTP 503: Service
  Unavailable" are still built in code. Mapping them to plain language needs typed
  error states in the ViewModels (noted in ADR 010), which is a separate change.
