# :feature-assistant

Football intelligence assistant screen — a conversational UI over the RAG-powered Ollama backend.

## Ownership

Presentation layer. The AI-facing feature module.

## Future Contents

- `AssistantViewModel` — owns `AssistantUiState` including message history. TDD required.
- `AssistantScreen` — chat-style UI with message bubbles and input field.
- `AssistantRepository` interface and implementation.

## Constraints

- The ViewModel must not fabricate responses. All answers come from the backend.
- Streaming responses must be handled gracefully — partial messages are valid state.
- TDD: ViewModel tests written before implementation.
- No hardcoded strings.
