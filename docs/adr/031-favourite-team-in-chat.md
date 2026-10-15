# ADR 031 — The Favourite Team in Chat

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The app asks each user for a favourite team on first launch (ADR 023) and keeps it on the phone. The assistant never saw it. On staging, the owner asked "where do you think we will be on the table by end of Christmas" and the assistant replied that it needed to know which team they support, though the app knew it was Man United.

## Decision

1. **The app sends the favourite team with each question.** `POST /v2/assistant/chat` gains an optional `favourite_team: {team, competition}`. Both are short strings limited to letters, digits, spaces and `.'&()-`, so they can't carry instructions.
2. **The server adds it to the question, in the user's voice.** The assistant reads "…question…\n\n(About me: I support Man United in the Premier League.)". The season router then finds the team the way it does when a team is named (ADR 021), and the model reads "we" and "my team" as that team. No prompt rule or router change is needed.
3. **The safety check reads only what the user typed.** History keeps the user's own text, so the note never reaches the history or its signatures (ADR 030).
4. **Nothing is stored.** The team stays on the phone. The server uses it for one answer and logs nothing about it.

## Consequences

- **Easier:** "Where will we finish?", "When do we play next?" and "How are we doing?" work without naming the team.
- **Questions about other teams are unaffected.** The note only adds context, and the model still answers about whichever team the question names.
- **Evaluation:** the conversation eval gains a favourite-team case.
- **Older apps** send no team and are answered as before.
