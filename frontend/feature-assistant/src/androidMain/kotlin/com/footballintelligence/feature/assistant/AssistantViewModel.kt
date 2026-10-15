package com.footballintelligence.feature.assistant

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.ChatFavouriteTeam
import com.footballintelligence.core.model.ChatMessage
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.MessageRole
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.SourceCitation
import com.footballintelligence.feature.assistant.repository.AssistantRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlin.random.Random

/**
 * ViewModel managing the assistant chat. The conversation it shows is also
 * the memory it sends back with each question (ADR 030): the last 4 signed
 * exchanges, reset by [newChat] or after 30 minutes idle.
 */
class AssistantViewModel(
    private val repository: AssistantRepository,
    private val now: () -> Long = System::currentTimeMillis,
    private val newConversationId: () -> String = ::randomConversationId,
    private val favouriteTeam: () -> FavouriteTeam? = { null },
) : ViewModel() {

    private val _state = MutableStateFlow<AssistantUiState>(AssistantUiState.Idle)
    val state: StateFlow<AssistantUiState> = _state.asStateFlow()

    private val _isSending = MutableStateFlow(false)
    val isSending: StateFlow<Boolean> = _isSending.asStateFlow()

    private val conversationHistory = mutableListOf<ChatMessage>()
    private var conversationId = newConversationId()
    private var lastActivity = now()

    /** Starts a new conversation: the screen clears and the assistant forgets. */
    fun newChat() {
        conversationHistory.clear()
        conversationId = newConversationId()
        _state.value = AssistantUiState.Idle
    }

    fun send(text: String) {
        if (text.isBlank() || _isSending.value) return
        if (now() - lastActivity > IDLE_RESET_MILLIS) newChat()
        lastActivity = now()

        val history = historyWindow(conversationHistory)
        val userMessage = ChatMessage(role = MessageRole.USER, text = text)
        conversationHistory.add(userMessage)
        _state.value = AssistantUiState.Chatting(conversationHistory.toList())
        _isSending.value = true

        viewModelScope.launch {
            val team = favouriteTeam()?.let { ChatFavouriteTeam(it.team, it.league) }
            when (val result = repository.chat(text, conversationId, history, team)) {
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
                        confidence = retrievalConfidence(response.confidence, response.sources.size),
                        signature = response.signature,
                    )
                    conversationHistory.add(assistantMessage)
                    _state.value = AssistantUiState.Chatting(conversationHistory.toList())
                }
                is NetworkResult.Error -> {
                    val errorCode = result.code
                    if (errorCode == HTTP_SERVICE_UNAVAILABLE) {
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

/** The backend returns 503 when the assistant (Ollama or its index) is down. */
private const val HTTP_SERVICE_UNAVAILABLE = 503

/** After this long without a question the next one starts a new conversation. */
private const val IDLE_RESET_MILLIS = 30 * 60 * 1000L

private const val ID_LENGTH = 16
private const val ID_RADIX = 36

private fun randomConversationId(): String =
    (1..ID_LENGTH).joinToString("") { Random.nextInt(ID_RADIX).toString(ID_RADIX) }
