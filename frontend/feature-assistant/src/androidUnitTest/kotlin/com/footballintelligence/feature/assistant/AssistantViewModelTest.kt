package com.footballintelligence.feature.assistant

import com.footballintelligence.core.model.ChatFavouriteTeam
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.HistoryTurn
import com.footballintelligence.core.model.MessageRole
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.assistant.repository.AssistantRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import io.mockk.slot
import kotlinx.coroutines.CompletableDeferred
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
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.ValueSource

@OptIn(ExperimentalCoroutinesApi::class)
class AssistantViewModelTest {

    private val repository = mockk<AssistantRepository>()
    private var clock = 0L
    private var ids = 0
    private val sentHistory = mutableListOf<List<HistoryTurn>>()
    private val sentIds = mutableListOf<String>()
    private val sentTeams = mutableListOf<ChatFavouriteTeam?>()
    private var favourite: FavouriteTeam? = null

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
        favouriteTeam = { favourite },
    )

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        val history = slot<List<HistoryTurn>>()
        val id = slot<String>()
        coEvery { repository.chat(any(), capture(id), capture(history), any()) } answers {
            sentIds += id.captured
            sentHistory += history.captured
            sentTeams += arg<ChatFavouriteTeam?>(3)
            NetworkResult.Success(answer("A to ${firstArg<String>()}"))
        }
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `the questions left come from the latest answer`() {
        val vm = viewModel()
        assertEquals(null, vm.questionsLeft.value)
        coEvery { repository.chat(any(), any(), any(), any()) } returns
            NetworkResult.Success(answer("A").copy(questionsLeft = 4))
        vm.send("Everton v Chelsea?")
        assertEquals(4, vm.questionsLeft.value)
    }

    @Test
    fun `a used-up budget leaves no questions`() {
        val vm = viewModel()
        coEvery { repository.chat(any(), any(), any(), any()) } returns
            NetworkResult.Error("Come back after midnight UTC.", 429, ErrorKind.REJECTED)
        vm.send("One more?")
        assertEquals(0, vm.questionsLeft.value)
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
        coEvery { repository.chat("Broken?", any(), any(), any()) } returns NetworkResult.Error("HTTP 500", 500)
        vm.send("Broken?")
        vm.send("Next?")
        assertEquals(emptyList<HistoryTurn>(), sentHistory.last())
    }

    @Test
    fun `a failed question shows a plain-language error, not the raw exception`() {
        val vm = viewModel()
        coEvery { repository.chat("Lost?", any(), any(), any()) } returns
            NetworkResult.Error("Connect timeout [url=http://10.0.2.2:8000]", kind = ErrorKind.OFFLINE)
        vm.send("Lost?")
        val reply = (vm.state.value as AssistantUiState.Chatting).messages.last()
        assertEquals(MessageRole.ASSISTANT, reply.role)
        assertEquals(ErrorKind.OFFLINE, reply.errorKind)
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
    fun `new chat while sending preserves the conversation until the answer arrives`() {
        val vm = viewModel()
        vm.send("First?")
        val pending = CompletableDeferred<NetworkResult<ChatResponse>>()
        coEvery { repository.chat("Pending?", any(), any(), any()) } coAnswers {
            sentIds += arg<String>(1)
            sentHistory += arg<List<HistoryTurn>>(2)
            pending.await()
        }
        vm.send("Pending?")
        val busyState = vm.state.value
        vm.newChat()
        vm.send("Duplicate?")
        assertEquals(busyState, vm.state.value)
        assertEquals(true, vm.isSending.value)
        assertEquals(1, ids)
        assertEquals(listOf("conv-1", "conv-1"), sentIds)
        assertEquals(2, sentHistory.last().size)

        pending.complete(NetworkResult.Success(answer("Pending answer")))
        val messages = (vm.state.value as AssistantUiState.Chatting).messages
        assertEquals(listOf("First?", "A to First?", "Pending?", "Pending answer"), messages.map { it.text })
        assertEquals(false, vm.isSending.value)
        vm.send("Follow-up?")
        assertEquals("conv-1", sentIds.last())
        assertEquals(HistoryTurn("assistant", "Pending answer", "sig-Pending answer"), sentHistory.last().last())
        vm.newChat()
        assertEquals(AssistantUiState.Idle, vm.state.value)
        vm.send("Fresh?")
        assertEquals("conv-2", sentIds.last())
        assertEquals(emptyList<HistoryTurn>(), sentHistory.last())
    }

    @ParameterizedTest
    @ValueSource(ints = [500, 503])
    fun `new chat works after a pending request fails`(code: Int) {
        val pending = CompletableDeferred<NetworkResult<ChatResponse>>()
        coEvery { repository.chat("Pending?", any(), any(), any()) } coAnswers { pending.await() }
        val vm = viewModel()
        vm.send("Pending?")
        val busyState = vm.state.value
        vm.newChat()
        assertEquals(busyState, vm.state.value)
        assertEquals(1, ids)
        pending.complete(NetworkResult.Error("Unavailable", code))
        assertEquals(false, vm.isSending.value)
        vm.newChat()
        assertEquals(AssistantUiState.Idle, vm.state.value)
        vm.send("Fresh?")
        assertEquals("conv-2", sentIds.last())
        assertEquals(emptyList<HistoryTurn>(), sentHistory.last())
    }

    @Test
    fun `thirty idle minutes start a new conversation`() {
        val vm = viewModel()
        vm.send("Everton v Chelsea?")
        clock += 31 * 60 * 1000L
        vm.send("And the draw?")
        assertEquals(emptyList<HistoryTurn>(), sentHistory.last())
        assertEquals(listOf("conv-1", "conv-2"), sentIds)
        coVerify(exactly = 2) { repository.chat(any(), any(), any(), any()) }
    }

    @Test
    fun `the saved favourite team goes with each question`() {
        favourite = FavouriteTeam(league = "Premier League", team = "Man United")
        viewModel().send("Where will we finish?")
        assertEquals(ChatFavouriteTeam("Man United", "Premier League"), sentTeams.single())
    }

    @Test
    fun `no favourite team sends none`() {
        viewModel().send("Hello?")
        assertEquals(null, sentTeams.single())
    }
}
