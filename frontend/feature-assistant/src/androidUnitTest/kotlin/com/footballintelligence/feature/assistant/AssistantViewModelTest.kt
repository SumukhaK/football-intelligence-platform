package com.footballintelligence.feature.assistant

import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.HistoryTurn
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.assistant.repository.AssistantRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import io.mockk.slot
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AssistantViewModelTest {

    private val repository = mockk<AssistantRepository>()
    private var clock = 0L
    private var ids = 0
    private val sentHistory = mutableListOf<List<HistoryTurn>>()
    private val sentIds = mutableListOf<String>()

    private fun answer(text: String, signature: String? = "sig-$text") = ChatResponse(
        answer = text,
        sources = emptyList(),
        confidence = 0.0,
        model = "gemma",
        retrievedCount = 0,
        signature = signature,
    )

    private fun viewModel() = AssistantViewModel(
        repository = repository,
        now = { clock },
        newConversationId = { "conv-${++ids}" },
    )

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        val history = slot<List<HistoryTurn>>()
        val id = slot<String>()
        coEvery { repository.chat(any(), capture(id), capture(history)) } answers {
            sentIds += id.captured
            sentHistory += history.captured
            NetworkResult.Success(answer("A to ${firstArg<String>()}"))
        }
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `the first question goes with no history`() {
        viewModel().send("Everton v Chelsea?")
        assertEquals(emptyList<HistoryTurn>(), sentHistory.single())
        assertEquals("conv-1", sentIds.single())
    }

    @Test
    fun `a follow-up carries the earlier exchange and its signature`() {
        val vm = viewModel()
        vm.send("Everton v Chelsea?")
        vm.send("And the draw?")
        assertEquals(
            listOf(
                HistoryTurn("user", "Everton v Chelsea?"),
                HistoryTurn("assistant", "A to Everton v Chelsea?", "sig-A to Everton v Chelsea?"),
            ),
            sentHistory.last(),
        )
        assertEquals(listOf("conv-1", "conv-1"), sentIds)
    }

    @Test
    fun `an unsigned answer and its question are not sent back`() {
        val vm = viewModel()
        coEvery { repository.chat("Broken?", any(), any()) } returns NetworkResult.Error("HTTP 500", 500)
        vm.send("Broken?")
        vm.send("Next?")
        assertEquals(emptyList<HistoryTurn>(), sentHistory.last())
    }

    @Test
    fun `only the last four exchanges are sent`() {
        val vm = viewModel()
        repeat(6) { vm.send("Q$it") }
        vm.send("Q6")
        val history = sentHistory.last()
        assertEquals(8, history.size)
        assertEquals(HistoryTurn("user", "Q2"), history.first())
    }

    @Test
    fun `new chat clears the conversation and starts a new one`() {
        val vm = viewModel()
        vm.send("Everton v Chelsea?")
        vm.newChat()
        assertEquals(AssistantUiState.Idle, vm.state.value)
        vm.send("Hello?")
        assertEquals(emptyList<HistoryTurn>(), sentHistory.last())
        assertNotEquals(sentIds.first(), sentIds.last())
    }

    @Test
    fun `thirty idle minutes start a new conversation`() {
        val vm = viewModel()
        vm.send("Everton v Chelsea?")
        clock += 31 * 60 * 1000L
        vm.send("And the draw?")
        assertEquals(emptyList<HistoryTurn>(), sentHistory.last())
        assertEquals(listOf("conv-1", "conv-2"), sentIds)
        coVerify(exactly = 2) { repository.chat(any(), any(), any()) }
    }
}
