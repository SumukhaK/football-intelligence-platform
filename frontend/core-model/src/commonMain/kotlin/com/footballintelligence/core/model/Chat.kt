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
    /** The server's signature on an answer, sent back as chat history (ADR 030). */
    val signature: String? = null,
)

/** One earlier message sent with a question so the assistant can follow up (ADR 030). */
@Serializable
data class HistoryTurn(
    val role: String,
    val content: String,
    val signature: String? = null,
)

/** A retrieved source document citation. */
@Serializable
data class SourceCitation(
    val source: String,
    val excerpt: String,
    @SerialName("relevance_score") val relevanceScore: Double,
)

/** The user's favourite team as the assistant API takes it (ADR 031). */
@Serializable
data class ChatFavouriteTeam(val team: String, val competition: String)

/** Request body for POST /assistant/chat; history needs a conversation ID. */
@Serializable
data class ChatRequest(
    val message: String,
    @SerialName("conversation_id") val conversationId: String? = null,
    val history: List<HistoryTurn> = emptyList(),
    @SerialName("favourite_team") val favouriteTeam: ChatFavouriteTeam? = null,
)

/** Response from POST /assistant/chat. */
@Serializable
data class ChatResponse(
    val answer: String,
    val sources: List<SourceCitation>,
    val confidence: Double,
    val model: String,
    @SerialName("retrieved_count") val retrievedCount: Int,
    /** Null from servers older than v2.5.0 or when no conversation ID was sent. */
    val signature: String? = null,
)
