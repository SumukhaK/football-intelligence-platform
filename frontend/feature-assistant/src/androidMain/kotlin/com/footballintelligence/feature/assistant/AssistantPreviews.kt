package com.footballintelligence.feature.assistant

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.ChatMessage
import com.footballintelligence.core.model.MessageRole
import com.footballintelligence.core.model.SourceCitation
import com.footballintelligence.core.ui.PreviewSurface

private val sampleConversation = listOf(
    ChatMessage(role = MessageRole.USER, text = "Why does the model favour Arsenal at home?"),
    ChatMessage(
        role = MessageRole.ASSISTANT,
        text = "Arsenal's strength rating is the highest in the league, and they win 68% of home games.",
        sources = listOf(
            SourceCitation(source = "model_card.md", excerpt = "Elo rating", relevanceScore = 0.82),
            SourceCitation(source = "features.md", excerpt = "Home win rate", relevanceScore = 0.64),
        ),
        confidence = 0.74,
    ),
)

@Composable
private fun Assistant(state: AssistantUiState, isSending: Boolean = false) {
    PreviewSurface {
        AssistantScreen(uiState = state, isSending = isSending, onSend = {}, onBack = {})
    }
}

@Preview
@Composable
private fun AssistantWelcomePreview() = Assistant(AssistantUiState.Idle)

@Preview
@Composable
private fun AssistantConversationPreview() = Assistant(AssistantUiState.Chatting(sampleConversation), isSending = true)

@Preview
@Composable
private fun AssistantUnavailablePreview() = Assistant(AssistantUiState.Unavailable("Ollama is not running."))
