package com.footballintelligence.feature.assistant

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.ChatMessage
import com.footballintelligence.core.model.MessageRole
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.SourceCitation
import com.footballintelligence.feature.assistant.repository.AssistantRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** ViewModel managing the assistant chat conversation. */
class AssistantViewModel(
    private val repository: AssistantRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<AssistantUiState>(AssistantUiState.Idle)
    val state: StateFlow<AssistantUiState> = _state.asStateFlow()

    private val _isSending = MutableStateFlow(false)
    val isSending: StateFlow<Boolean> = _isSending.asStateFlow()

    private val conversationHistory = mutableListOf<ChatMessage>()

    fun send(text: String) {
        if (text.isBlank() || _isSending.value) return

        val userMessage = ChatMessage(role = MessageRole.USER, text = text)
        conversationHistory.add(userMessage)
        _state.value = AssistantUiState.Chatting(conversationHistory.toList())
        _isSending.value = true

        viewModelScope.launch {
            when (val result = repository.chat(text)) {
                is NetworkResult.Success -> {
                    val response = result.data
                    val assistantMessage = ChatMessage(
                        role = MessageRole.ASSISTANT,
                        text = response.answer,
                        sources = response.sources.map { src ->
                            SourceCitation(
                                source = src.source,
                                excerpt = src.excerpt,
                                relevanceScore = src.relevanceScore,
                            )
                        },
                        confidence = response.confidence,
                    )
                    conversationHistory.add(assistantMessage)
                    _state.value = AssistantUiState.Chatting(conversationHistory.toList())
                }
                is NetworkResult.Error -> {
                    val errorCode = result.code
                    if (errorCode == 503) {
                        _state.value = AssistantUiState.Unavailable(result.message)
                    } else {
                        val errorMessage = ChatMessage(
                            role = MessageRole.ASSISTANT,
                            text = "Error: ${result.message}",
                        )
                        conversationHistory.add(errorMessage)
                        _state.value = AssistantUiState.Chatting(conversationHistory.toList())
                    }
                }
                is NetworkResult.Loading -> Unit
            }
            _isSending.value = false
        }
    }
}
