# ADR 021 — Season Tools and a Rule-Based Router for the Assistant

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The assistant could predict single matches, explain them and list upcoming
fixtures (ADR 018). Questions fans actually ask had no data behind them:
"who will top the league after Boxing Day", "who won the league in 2015/16",
"when is the next Manchester derby", "which team will keep the most clean
sheets". The home screen shows only upcoming fixtures, so the assistant is the
only place to ask about the rest of the season.

Two new tools fix the data gap, but the default chat model, `qwen2.5:7b`
(ADR 019), often refused instead of calling them, on 4 of 5 season questions.
It refused most when platform documents also scored above the retrieval
cut-off. `qwen2.5:14b` called them, but is slower and twice the size.

## Decision

1. **Internal tools, not endpoints.** `team_matches` lists a team's results
   (any season in the data) and, this season, its remaining fixtures,
   optionally against one opponent, with a note when no meeting is left.
   `league_table` gives the table on any date of a season we hold. Users never
   see a list of tools.
2. **Projection.** For a date later this season, `league_table` plays every
   remaining fixture up to that date 10,000 times with each league's
   Dixon-Coles goals model (ADR 009) and adds the results to the real table.
   It reports expected points, goals and clean sheets, the most likely
   position, and the chance of finishing first, top four, bottom three,
   scoring the most goals and keeping the most clean sheets. A fixed seed makes
   answers repeatable for the same data. Ties use goal difference only.
3. **Leaders spelled out.** Each table also returns the leading team for the
   common questions, because the 7B model misread a 20-row table and quoted the
   wrong team.
4. **Rule-based router.** `SeasonRouter` reads the question before the model:
   - player questions (top scorer, assists) and seasons that have not started
     get a fixed reply, with no retrieval or model call;
   - table, results and head-to-head questions get their tool calls decided by
     code: league and team names (including full club names, nicknames and
     named derbies), seasons, and dates ("after Boxing Day", "Valentine's
     Day", "end of January", "3 January", "this season");
   - "who wins" questions about a meeting or a team's next match also run
     `predict_match` for the next fixture;
   - everything else, including questions about the platform, goes to the
     model unchanged.
   Routed questions skip document retrieval. The model still writes the answer
   and may call more tools.
5. **Team names.** Names people type ("Manchester United") map to the data's
   names ("Man United") through the openfootball club names and a short
   nickname list, for the new tools and for `predict_match`/`explain_match`.
6. **Today's date in the prompt**, so relative dates land in the right season.
7. **Evaluation.** `evaluation.assistant_season` asks seven questions, runs the
   tool each answer should come from, and checks the answer names the expected
   team and invents no numbers.

## Consequences

- With `qwen2.5:7b-instruct`, the season eval went from 3 of 7 without the
  router to 7 of 7 with it, on 8 October 2026.
- Routed and refused questions use fewer tokens. The router is the first
  piece of the guardrails gateway planned for production.
- The router is rules, so questions phrased in ways it doesn't recognise fall
  through to the model, which may still refuse. New phrasings are added with a
  test each.
- No player-level data exists, so player questions stay refused until a new
  data source and its own ADR.
- The projection ignores head-to-head and other league-specific tie-breakers,
  and does not model squad changes during the season.
