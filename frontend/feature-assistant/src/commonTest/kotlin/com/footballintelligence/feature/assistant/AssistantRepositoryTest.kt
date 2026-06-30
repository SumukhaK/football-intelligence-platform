package com.footballintelligence.feature.assistant

import com.footballintelligence.core.model.ChatRequest
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.FootballApiService
import com.footballintelligence.feature.assistant.repository.DefaultAssistantRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class AssistantRepositoryTest {

    private val api = mockk<FootballApiService>()
    private val repository = DefaultAssistantRepository(api)

    private val response = ChatResponse(
        answer = "The model achieved 56% accuracy.",
        sources = emptyList(),
        confidence = 0.85,
        model = "llama3.2",
        retrievedCount = 3,
    )

    @Test
    fun `chat sends message to api and returns success`() = runTest {
        coEvery { api.chat(ChatRequest("test question")) } returns NetworkResult.Success(response)
        val result = repository.chat("test question")
        assertTrue(result is NetworkResult.Success)
        assertEquals(response, (result as NetworkResult.Success).data)
        coVerify(exactly = 1) { api.chat(ChatRequest("test question")) }
    }

    @Test
    fun `chat returns error on api failure`() = runTest {
        coEvery { api.chat(any()) } returns NetworkResult.Error("503", 503)
        val result = repository.chat("hello")
        assertTrue(result is NetworkResult.Error)
        assertEquals(503, (result as NetworkResult.Error).code)
    }
}
