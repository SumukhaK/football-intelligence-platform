# Assistant guardrails, limits and caching: analysis

Analysis from 8 October 2026, with the decisions taken since. The season tools and router it called "answerable later" are built (ADR 021). The rest is tracker steps 3a, 3b and 6a in [hosting-execution-tracker.md](hosting-execution-tracker.md).

## Decisions (8 October 2026)

- **Identity:** invite-only email and password accounts, not Google sign-in. See [accounts-and-consent-plan.md](accounts-and-consent-plan.md).
- **Consent:** a consent screen after the first sign-in. Question text is stored only with opt-in.
- **Strikes:** a permanent ban after 3 harmful or abusive questions.
- **Unanswerable-yet questions:** the tools were built instead (ADR 021).
- **Limits:** one daily token budget per user. An answer is never cut off midway.
- **Allowance:** none in the staging beta. Production limits come from beta usage.
- **Audience:** family and friends only. The app isn't published in any store.

## Where we are today

- **Rate limiting:** one in-memory, sliding one-minute window per client IP address, 120 requests a minute (ADR 014). It resets when the server restarts and isn't shared between instances, and IP addresses aren't users: a whole mobile network can share one.
- **No user identity:** there are no accounts and no device ID, so the server can't count anything "per user" yet.
- **No shared state:** everything is files. Per-user counters, strikes and a cache need storage that survives restarts and is shared by every instance.
- **Single-turn chat:** each request carries one message and no history, so there's no conversation length to limit yet.
- **What the assistant can answer:** match predictions, SHAP explanations and fixtures (tools), plus project documents (retrieval). It **can't** answer "who will top the Premier League by New Year", because nothing projects a league table. It also can't answer "who won the league in 2015/16", because the index holds documents, not match results. Your scope rule therefore needs two checks: whether a question is **in scope**, and whether it's **answerable today**.

## Recommended design: a gateway in front of the model

Every chat request passes through these checks, cheapest first. Only the last one costs model tokens.

| # | Check | How | Model cost | Counts against the user |
|---|---|---|---|---|
| 1 | Identity and ban | Verify the app's identity token; look up strikes and ban status | none | no |
| 2 | Input limits | Max characters; one message; reject empty or oversized input | none | no |
| 3 | Safety | Small rules list, then a dedicated moderation model (for example Llama Guard on Workers AI) | small, separate model | no, but may add a strike |
| 4 | Answer cache | Exact match on the normalised question, scoped to the current data snapshot, model and prompt version | none | no |
| 5 | Scope router | Rules and entities (teams, leagues, seasons, dates) plus the retrieval score we already compute | none (the embedding is already needed) | no |
| 6 | Quota | The user's daily token budget, and a global daily budget for the whole service | none | n/a |
| 7 | Model | Retrieval, tools and generation, as today; hard caps on input, output tokens and tool rounds | yes | yes, actual tokens |

### 1. Scope router

- **Deterministic first.** Match team and league names against the team list we already serve, read seasons and dates in the question, and use the retrieval score the request already pays for (the 0.81 cut-off).
- **Rules from your examples:** a future season (2027/28 or later), another league, or other sports means refusing with a fixed message and no model call. The current season and seasons in our data are in scope.
- **"In scope but not answerable yet"** (league-table projections, historical results) gets its own honest message, not a generic "I don't know", and doesn't count against the user. Adding those abilities later means new tools (a season simulation using the goals model, a results lookup), each a separate task.
- **No LLM classifier at first.** Use one only if the router's eval shows rules plus embeddings aren't good enough. Even then it should be the smallest model, because it runs on every question.
- **Router eval:** label 50+ questions as in scope, out of scope, or answerable later. Track wrong refusals, not just wrong answers. A router that refuses good questions is the failure users notice most.

### 2. Cache

- What you described is a **response cache**: the same question gets the stored answer. "Prompt caching" usually means the provider reusing a shared prompt prefix to cut cost. That's worth having too, but it's the provider's feature, not ours.
- **Exact match on a normalised question** (lower case, whitespace and punctuation cleaned up, team aliases mapped). I'd avoid a "semantic" cache that matches similar questions: "Arsenal vs Leeds" and "Arsenal vs Chelsea" embed almost identically, and returning the wrong match's prediction is worse than paying for a model call.
- **The key includes the data snapshot, model version and prompt version**, so the daily refresh, a new model or a prompt change empties it automatically. Predictions change when results come in, so a cached prediction must never outlive its snapshot.
- Router refusals and safety refusals are fixed messages, so they need no cache.

### 3. Safety and strikes

- **Separate harmful from disrespectful from off-topic.** Football fans swear about their own team. "F***ing Arsenal lost again" is a valid question, not abuse. Only content aimed at harm (threats, hate, sexual content, self-harm, attempts to make the assistant misbehave) should add a strike. Off-topic questions never do.
- **I'd escalate rather than ban for ever after 3:** 1st strike is a warning, 2nd blocks for 24 hours, 3rd blocks for 7 days, 4th blocks permanently, with a manual unban. False positives are certain, and a permanent ban from a single model's judgement is harsh. If you want it stricter, 3 strikes then permanent is easy to configure.
- **A permanent ban is only as strong as identity.** With an anonymous install ID, reinstalling the app gets around it. That's acceptable for a portfolio app, but it shouldn't be claimed as more than it is.
- **Safety checks run before the cache**, so a harmful question never gets a cached answer.
- **Privacy:** store strike counts and categories, not the text of the questions.

### 4. Quotas and the token budget

I'd merge your points 3 and 4 into **one daily token budget per user**, shown in the app as "about N questions left".

- Each model answer costs its actual tokens. Short answers use less, so the same budget allows about 5 short questions or about 3 long ones, which is the behaviour you described, with one rule instead of two.
- **Cached answers, router refusals and safety refusals cost nothing.**
- **Per request:** a cap on input length, output tokens (`max_tokens`) and tool rounds (already 3). A request starts only if the remaining budget covers a typical answer, and the actual cost is charged afterwards. One answer may run slightly over the budget; the next request is then refused.
- **A global daily budget** sits on top. Per-user limits don't protect the bill from many users at once. When the provider's daily free quota (10,000 neurons) is nearly used, the assistant pauses for everyone with a clear message, and predictions keep working.
- The budget resets at a fixed time (UTC midnight) and the app shows when.
- Conversation length: chat is single-turn today, so "questions per day" is the limit that matters. If multi-turn chat is added later, the history counts towards the token budget.

### 5. App changes

- On first entry to the Assistant screen, show a one-time rules sheet: what it can answer, the daily allowance, the conduct rules and the strike policy. After that, an info button reopens it.
- Show "about N questions left today" and when it resets, using new response fields or headers. That's an API contract change, so it goes in the ADR and `docs/api.md`.
- All text goes in `strings.xml`, with previews and accessibility descriptions, following the project standards.

### 6. Infrastructure this needs

- **Identity:** a verified, stable ID per install. Recommended: Firebase Anonymous Auth. It's free, the server verifies the token, there's no sign-in screen, and it can be upgraded to Google sign-in later.
- **Shared state:** Firestore (free tier: 50,000 reads and 20,000 writes a day) for budgets, strikes, bans and the cache, with a time-to-live so cache entries expire. This is the first real database in the project, so it needs an ADR. Redis would be faster, but managed Redis isn't free.
- **On/off by configuration:** everything above is switched on in staging and production and off for local development, so local work stays simple. All of it is still tested in CI.
- **Hosting tracker:** this becomes a new step after "Connect the hosted LLM", because the limits only matter once the model costs money.

## Questions as first asked

1. **Identity:** Firebase Anonymous Auth, so a ban is per install and there's no sign-in (recommended), or Google sign-in, so a ban follows the person?
2. **Strikes:** escalating, so warning, 24 hours, 7 days, then permanent (recommended), or permanent after 3?
3. **Questions we can't answer yet** (table projections, past results): refuse honestly now and add tools as separate tasks later (recommended), or build those tools before launch?
4. **Limits:** one daily token budget shown as "about N questions left" (recommended), or fixed question counts plus a separate token cap?
5. **Daily allowance:** what roughly? I'd start at about 4 average answers' worth, then tune it from real usage and cost.
