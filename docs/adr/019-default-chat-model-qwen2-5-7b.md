# ADR 019 — qwen2.5 7B as the Default Chat Model

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The assistant's chat model was `llama3.2` (3B) by default. Since ADR 018 the
model must call tools and quote their numbers, and two local evaluations
measure that: `evaluation.assistant_grounding` (does the answer quote
`/v2/predict` without inventing numbers) and `evaluation.assistant_abstention`
(does it answer what the knowledge base covers and refuse what it doesn't).

The project rule is to use the smallest Ollama model that meets the quality bar
(`.claude/CLAUDE.md`, section 5), and never to fine-tune.

## Decision

The default `OLLAMA_CHAT_MODEL` is `qwen2.5:7b-instruct`, in
`backend/app/config.py`, `assistant/configuration.py` and `.env.example`.

Results on 7 and 8 October 2026, same index, model and questions:

| Model | Size | Grounding | Abstention |
|---|---|---|---|
| `llama3.2` | 3B, 2.0 GB | 5/11 | 15/20 |
| `qwen2.5:7b-instruct` | 7B, 4.7 GB | 11/11 | 20/20 |
| `qwen2.5:14b-instruct` | 14B, 9.0 GB | 11/11* | 20/20 |

\* Scored 10/11 at the time: the evaluation wrongly flagged the season in the
API's "unknown team" error, which the answer repeated. The evaluation now
counts the API's error as a source.

`llama3.2` called the right tool every time but misquoted the probability in 6
of 10 answers (66.35% for 66.65%), refused 3 questions the documents answer,
and twice printed a made-up `wikipedia` tool call as its answer. The 7B model
is the smallest tested that passes both checks; 14B adds nothing on them.

## Consequences

- Setup pulls about 4.7 GB for the chat model instead of 2 GB.
- Answers are slower. On the demo laptop's GPU an answer took about 45
  seconds, longer than the app's 30-second timeout (see
  `docs/showcase/demo-video/README.md`); that timeout is unchanged here.
- Anyone who set `OLLAMA_CHAT_MODEL=llama3.2` in their `.env` keeps it until
  they change it.
- A new candidate model should pass both evaluations before it becomes the
  default.
