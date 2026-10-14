package com.footballintelligence.feature.assistant.repository

import com.footballintelligence.core.model.ChatRequest
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.HistoryTurn
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.FootballApiService

/** Sends messages to the Football Intelligence Assistant. */
interface AssistantRepository {
    /** Asks [message] in conversation [conversationId], with the signed [history] so far. */
    suspend fun chat(
        message: String,
        conversationId: String,
        history: List<HistoryTurn>,
    ): NetworkResult<ChatResponse>
}

/** Production implementation backed by [FootballApiService]. */
class DefaultAssistantRepository(
    private val api: FootballApiService,
) : AssistantRepository {
    override suspend fun chat(
        message: String,
        conversationId: String,
        history: List<HistoryTurn>,
    ): NetworkResult<ChatResponse> = api.chat(ChatRequest(message, conversationId, history))
}
