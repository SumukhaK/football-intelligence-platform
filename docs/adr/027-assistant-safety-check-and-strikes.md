# ADR 027 — Assistant Safety Check and Strikes

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The owner decided (8 October 2026, [guardrails analysis](../plans/assistant-guardrails-analysis.md))
that a user who asks 3 harmful or abusive questions is banned for good, that
football swearing never counts, and that the staging beta runs this check
before friends use it. ADR 022 already gave each user a `strikes` count and a
`banned` status that ends every session; nothing added strikes yet.

A word list cannot tell "our defence is absolute shit" from a threat, so the
check needs a model built for it. The owner's Workers AI account (ADR 025)
offers Meta's Llama Guard 3 through the same OpenAI-compatible endpoint the
assistant already calls. Tried on 14 October 2026: angry fan questions ("this
ref is a blind idiot", "will Chelsea destroy Everton", "I want to die, Leeds
are going down") came back `safe`; a threat to a referee, a request for the
manager's home and a racist chant came back `unsafe` (S1, S7, S10). Each check
costs about 9 neurons, so the free daily allowance covers about a thousand.

## Decision

1. **A safety check runs before everything else in chat**, including the
   season router and retrieval, with Llama Guard 3: `@cf/meta/llama-guard-3-8b`
   on Workers AI, or `llama-guard3:1b` on local Ollama. It reads only the
   question. Any `unsafe` verdict, whatever its category, blocks the question
   without a model call.
2. **A blocked question adds a strike to the signed-in user.** The third
   strike bans the account and revokes its sessions, as an owner ban does.
   The answer is a fixed refusal saying how many strikes the user has, with
   `model` set to `safety`, so the response shape and the app are unchanged.
   The request after a ban gets the existing `403 Account blocked`. The owner
   script's `unban` lifts a ban and clears the strikes.
3. **Off unless `ASSISTANT_SAFETY=true`.** Local development needs no guard
   model. On Cloud Run the server refuses to start with the assistant on and
   the check off, as it does for sign-in (ADR 025).
4. **Fails closed.** If the guard model can't be reached or answers in an
   unexpected form, chat returns the usual structured 503 and no strike is
   added; predictions keep working.
5. **Privacy.** Only the strike count and the verdict's categories are kept
   and logged (`guardrail.event`), never the question (ADR 022).

## Consequences

- **Easier:** the beta can open to friends with the conduct rule the owner
  set, enforced without the owner reading questions.
- **False positives will happen** and cost a strike. Three strikes and a
  manual unban keep one wrong verdict from banning anyone.
- **Latency and cost:** one extra small model call before every answer.
- **Not covered:** prompt injection ("ignore your instructions") is not
  unsafe to Llama Guard; the system prompt and the grounding rules handle it.
  The answer cache, budgets and the in-app rules sheet are later parts of
  hosting step 3b.
