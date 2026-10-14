package com.footballintelligence.feature.assistant

import com.footballintelligence.core.model.ChatMessage
import com.footballintelligence.core.model.HistoryTurn
import com.footballintelligence.core.model.MessageRole

/** Exchanges sent back with each question (ADR 030). */
private const val MAX_EXCHANGES = 4

/** The server accepts history messages up to this length; longer ones can't be sent intact. */
private const val MAX_TURN_CHARS = 1500

/**
 * The history to send with the next question: the last 4 question-and-answer
 * pairs whose answer the server signed. Errors and answers too long to send
 * whole are left out with their question, since an altered answer would fail
 * its signature.
 */
fun historyWindow(messages: List<ChatMessage>): List<HistoryTurn> = messages
    .zipWithNext()
    .filter { (question, answer) ->
        question.role == MessageRole.USER &&
            answer.role == MessageRole.ASSISTANT &&
            answer.signature != null &&
            question.text.length <= MAX_TURN_CHARS &&
            answer.text.length <= MAX_TURN_CHARS
    }
    .takeLast(MAX_EXCHANGES)
    .flatMap { (question, answer) ->
        listOf(
            HistoryTurn("user", question.text),
            HistoryTurn("assistant", answer.text, answer.signature),
        )
    }
