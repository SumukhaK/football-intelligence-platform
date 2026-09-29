# :feature-assistant

Football intelligence assistant screen — a conversational UI over the RAG-powered Ollama backend.

## Ownership

Presentation layer. The AI-facing feature module.

## Contents

- `AssistantViewModel` — owns `AssistantUiState` and the message history.
- `AssistantScreen` — chat UI with message bubbles and an input field.
- `AssistantRepository` — sends questions to `POST /v2/assistant/chat`.

## Constraints

- The ViewModel must not fabricate responses. All answers come from the backend.
- Streaming responses must be handled gracefully — partial messages are valid state.
- TDD: ViewModel tests written before implementation.
- No hardcoded strings.
