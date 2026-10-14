package com.footballintelligence.feature.assistant

import com.footballintelligence.core.model.ChatMessage
import com.footballintelligence.core.model.HistoryTurn
import com.footballintelligence.core.model.MessageRole
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ChatMemoryTest {
    private fun q(text: String) = ChatMessage(MessageRole.USER, text)
    private fun a(text: String, signature: String? = "sig") =
        ChatMessage(MessageRole.ASSISTANT, text, signature = signature)

    @Test
    fun `an answer too long to send whole is left out with its question`() {
        val history = historyWindow(listOf(q("Long?"), a("x".repeat(1501)), q("Short?"), a("Yes")))
        assertEquals(listOf(HistoryTurn("user", "Short?"), HistoryTurn("assistant", "Yes", "sig")), history)
    }

    @Test
    fun `a question still waiting for its answer is not history`() {
        assertEquals(emptyList<HistoryTurn>(), historyWindow(listOf(q("Pending?"))))
    }
}
