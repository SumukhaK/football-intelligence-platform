package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Role of a chat participant. */
enum class MessageRole { USER, ASSISTANT }

/** A single message in the conversation history. */
data class ChatMessage(
    val role: MessageRole,
    val text: String,
    val sources: List<SourceCitation> = emptyList(),
    val confidence: Double? = null,
)

/** A retrieved source document citation. */
@Serializable
data class SourceCitation(
    val source: String,
    val excerpt: String,
    @SerialName("relevance_score") val relevanceScore: Double,
)

/** Request body for POST /assistant/chat. */
@Serializable
data class ChatRequest(val message: String)

/** Response from POST /assistant/chat. */
@Serializable
data class ChatResponse(
    val answer: String,
    val sources: List<SourceCitation>,
    val confidence: Double,
    val model: String,
    @SerialName("retrieved_count") val retrievedCount: Int,
)
