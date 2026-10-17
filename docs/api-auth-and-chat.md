# Authentication and Assistant API

Current v2.6.0 contract. Paths below use the `/v2` prefix. [API reference](api.md).

## Sign-in and consent

With `AUTH_REQUIRED=true` (staging and production), every `/v2` data route needs `Authorization: Bearer <token>` from a signed-in user who has accepted the current notice. `/v2/health`, `/docs`, `/redoc`, `/openapi.json`, the crest and emblem redirects (image loaders send no token) and the routes below stay open. `/v1` and unversioned paths are not mounted, because they would bypass sign-in. `AUTH_REQUIRED` is off by default, so local development needs no token (ADR 022).

Accounts are invite-only. The owner creates an invite with `uv run python -m scripts.manage_accounts invite --email <email>`.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/v2/auth/redeem-invite` | `email`, `code` (as `XXXX-XXXX`; case, spaces and dashes are ignored), `password` (10+ characters) | `{ "token", "expires_at" }`. Creates the account, or resets its password with a new invite, and ends older sessions. |
| POST | `/v2/auth/login` | `email`, `password` | `{ "token", "expires_at" }`. Sessions last 30 days. |
| POST | `/v2/auth/logout` | none | 204; ends the session behind the token. |
| GET | `/v2/me` | none | `email`, `consent_required`, `consent_version`, `consent_text`, `store_questions` |
| POST | `/v2/me/consent` | `version`, `store_questions` (default false) | The updated `/v2/me` body. With `store_questions` true, each later chat question's text is kept for 90 days (not the answer, ADR 034); false stops it. |

Errors:

| Status | `error` | When |
|---|---|---|
| 400 | `Invalid invite` | No invite for this email, or the code is wrong. |
| 409 | `Invite already used` | The right code, already redeemed: the account exists, so sign in. Only the code's holder gets this answer. |
| 410 | `Invite expired` | The right code, older than 7 days: ask for a new one. |
| 401 | `Not signed in` | No token, or an unknown, expired or revoked one. |
| 401 | `Invalid credentials` | Wrong email or password; the message never says which. |
| 403 | `Consent required` | The current notice has not been accepted, or `version` is not the current one. |
| 403 | `Account blocked` | The account is banned. |
| 422 | `Password too short` | Fewer than 10 characters. |
| 429 | `Too many attempts` | 5 failed sign-ins for the email within 15 minutes; it is locked for 15 minutes. |

---

## POST /assistant/chat

Retrieval-augmented answers about the project's data and models. Returns 503
when the assistant is turned off, its vector store is missing, or its model
provider is unreachable, out of quota or too slow. Predictions keep working.

`ASSISTANT_PROVIDER` chooses who answers (ADR 025): `ollama` (the default),
`workers_ai` (Cloudflare Workers AI, using `WORKERS_AI_ACCOUNT_ID`,
`WORKERS_AI_API_TOKEN`, `WORKERS_AI_CHAT_MODEL` and `WORKERS_AI_EMBED_MODEL`)
or `off`. `model` in the response names the chat model that wrote the answer.
`sources` is always empty and the answer carries no `[source: ...]` markers:
the model still cites, but the server logs its sources and citations in
`assistant.answer` instead of sending them (ADR 029).

**Chat memory (ADR 030).** To ask a follow-up, send the chat so far:

```json
{
  "message": "And the draw?",
  "conversation_id": "a1b2c3d4e5f6",
  "history": [
    {"role": "user", "content": "Who wins Everton v Chelsea?"},
    {"role": "assistant", "content": "Everton are slight favourites at 41%.",
     "signature": "<the signature that answer came with>"}
  ]
}
```

- `conversation_id` (8–64 letters, digits, `_` or `-`) is made by the app and
  is needed whenever `history` is sent. Every answer to a request with one
  carries a `signature`.
- `history` holds at most 8 messages, oldest first, each at most 1,500
  characters. Every `assistant` item must carry the `signature` its answer
  came with, signed for this user and conversation.
- If any signature is missing or wrong, the whole history is ignored, and the
  question is answered on its own; this is logged as a `guardrail.event` with
  kind `history`. History over 1,200 tokens (about 4,800 characters) is trimmed,
  oldest first, never rejected.
- The safety check reads the user's earlier questions with the new one; only the
  new one can add a strike. The prompt and numeric validation require new numbers to be supported by tools
  called for this question. History supplies conversational context, not fresh model evidence.
- Without `conversation_id` and `history`, the endpoint behaves as before.

**Favourite team (ADR 031).** `"favourite_team": {"team": "Man United", "competition": "Premier League"}` tells the assistant who "we" and "my team" are. Each field is at most 60 characters of letters, digits, spaces and `.'&()-`. The team is added to the question for the model and the season router, but not to the safety check or the history.

For a match prediction, its SHAP explanation or a league's upcoming fixtures,
the assistant calls tools that run the same services as `/v2/predict`,
`/v2/explain` and `/v2/fixtures`, so it quotes the latest model's numbers
(ADR 018). The chat model must support tool calling.

It can also answer season questions through internal tools: a team's results
and next meetings, and the league table on any date of a season in the data,
projected with the goals model when the date is still ahead (ADR 021). A
rule-based router reads each question first. Questions about individual
players or seasons that have not started get a fixed reply without calling
the model; those responses have `"model": "router"`, `"sources": []` and
`"confidence": 0.0`.

With `ASSISTANT_SAFETY=true` (required on Cloud Run when the assistant is on),
Llama Guard 3 checks the question before retrieval, routing and generation (ADR 027). A harmful
question gets a fixed refusal with `"model": "safety"`, `"sources": []` and
`"confidence": 0.0`, and adds a strike to the signed-in user; the answer says
how many strikes they have. The third strike bans the account and ends its
sessions, so the next request gets `403 Account blocked`. Swearing about
football is not harmful. If the safety model can't be reached, chat returns
`503` and no strike is added.

---
