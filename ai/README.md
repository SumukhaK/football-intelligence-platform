# AI

Data engineering, machine learning, explainability, and retrieval-augmented generation for the Football Intelligence Platform.

---

## Ownership

AI and data engineering implementation. Follows `.claude/CLAUDE.md` sections 5 and 6.

---

## Responsibilities

This directory owns:

- Raw data ingestion and schema validation.
- Feature engineering for model training.
- XGBoost model training and serialisation.
- SHAP explainability — every prediction includes a SHAP explanation.
- Retrieval-augmented generation pipeline using Ollama.
- Prompt templates and retrieval configuration.
- Evaluation scripts: prediction accuracy, assistant faithfulness, hallucination rate.

---

## Directory Structure

```
ai/
  ingestion/          # Scripts that pull raw data into datasets/raw/
  validation/         # Schema validation against datasets/schemas/
  feature_engineering/ # Transforms processed data into model-ready features
  training/           # XGBoost training scripts and hyperparameter configs
  evaluation/         # Evaluation harness for model and assistant quality
  inference/          # Inference wrappers used by the backend
  rag/                # Retrieval pipeline: indexing, search, context assembly
  prompts/            # Prompt templates (source of truth is playbook/)
  datasets/           # Symlinks or references to datasets/processed/
  models/             # Serialised model artefacts (gitignored by default)
```

---

## AI Philosophy

- The assistant never invents facts. Every response is grounded in retrieved data or model output.
- SHAP values accompany every prediction.
- Prompt templates are version-controlled and tested.
- Model selection favours the smallest Ollama model that meets quality thresholds.
- Fine-tuning and LoRA are out of scope. Improve quality through better retrieval and better prompts.
- No model is merged without a passing evaluation run.

---

## Future Responsibilities

- Multi-league data support.
- Player-level prediction (not just match-level).
- Structured evaluation dashboard.
- Retrieval quality benchmarking against labelled question sets.
