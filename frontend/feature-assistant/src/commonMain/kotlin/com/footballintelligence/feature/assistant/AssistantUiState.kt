package com.footballintelligence.feature.assistant

import com.footballintelligence.core.model.ChatMessage

/** UI state for the assistant chat screen. */
sealed class AssistantUiState {
    /** No messages yet, assistant ready. */
    data object Idle : AssistantUiState()

    /** A message is being sent and a response is loading. */
    data class Chatting(val messages: List<ChatMessage>) : AssistantUiState()

    /** Assistant is unavailable (backend 503). */
    data class Unavailable(val reason: String) : AssistantUiState()
}
