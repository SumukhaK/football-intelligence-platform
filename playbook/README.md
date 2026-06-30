# Playbook

Prompt templates, agent instructions, and retrieval configurations for the Football Intelligence Platform AI assistant.

---

## Ownership

Maintained by the AI engineer alongside the `ai/` layer. Prompt templates are treated as code: version-controlled, reviewed, and tested.

---

## Directory Structure

```
playbook/
  stage-00/    # Templates used during repository setup and planning
  stage-01/    # Templates for data engineering tasks
  stage-02/    # Templates for model training and evaluation tasks
  templates/   # Reusable base templates shared across stages
```

---

## Template Format

Every prompt template must document:

- **Purpose:** What this prompt is designed to do.
- **Input variables:** Every variable the prompt expects, with type and description.
- **Expected output format:** Structure and constraints on the response.
- **Known failure modes:** Situations where this prompt produces unreliable results.

---

## Rules

- Prompt templates are version-controlled here, not scattered in code.
- Templates are not modified without a review. Changes to prompts change system behaviour.
- Each template has at least one documented test case showing expected input and output.
- Templates that are retired are moved to an `archive/` subdirectory, not deleted.
- Never hardcode data in a prompt. Pass all facts as input variables retrieved from the dataset.

---

## Future Responsibilities

- Stage-03 templates for the RAG assistant.
- Stage-04 templates for API response formatting.
- Evaluation prompt templates for LLM-as-judge scoring.
