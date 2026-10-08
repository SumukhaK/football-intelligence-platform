package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.SERVED_LEAGUES
import com.footballintelligence.core.model.TeamsResponse
import com.footballintelligence.feature.team.repository.TeamRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class TeamPickerViewModelTest {
    private val repository = mockk<TeamRepository>()
    private val store = mockk<FavouriteTeamStore>(relaxed = true)
    private val serieA = listOf("Inter", "Milan", "Napoli")
    private val serieATeams = NetworkResult.Success(TeamsResponse("Serie A", "2026/27", serieA))

    private fun viewModel(flow: PickerFlow = PickerFlow.ONBOARDING) = TeamPickerViewModel(flow, repository, store)

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        coEvery { repository.getTeams("Serie A") } returns serieATeams
    }

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `the picker starts on the league step with the five leagues`() {
        assertEquals(PickerStep.League(SERVED_LEAGUES), viewModel().step.value)
    }

    @Test
    fun `picking a league moves to its teams`() {
        val vm = viewModel()
        vm.selectLeague("Serie A")
        assertEquals(PickerStep.Team("Serie A", TeamsUiState.Success(serieA)), vm.step.value)
    }

    @Test
    fun `back on the team step returns to the leagues`() {
        val vm = viewModel()
        vm.selectLeague("Serie A")
        vm.backToLeagues()
        assertEquals(PickerStep.League(SERVED_LEAGUES), vm.step.value)
    }

    @Test
    fun `teams that fail to load can be retried`() {
        coEvery { repository.getTeams("Serie A") } returns
            NetworkResult.Error("Connection refused", kind = ErrorKind.OFFLINE)
        val vm = viewModel()
        vm.selectLeague("Serie A")
        assertEquals(
            PickerStep.Team("Serie A", TeamsUiState.Error("Connection refused", ErrorKind.OFFLINE)),
            vm.step.value,
        )
        vm.retryTeams()
        coVerify(exactly = 2) { repository.getTeams("Serie A") }
    }

    @Test
    fun `a slow answer for a league the fan left does not reopen it`() {
        val answer = CompletableDeferred<NetworkResult<TeamsResponse>>()
        coEvery { repository.getTeams("Serie A") } coAnswers { answer.await() }
        val vm = viewModel()
        vm.selectLeague("Serie A")
        vm.backToLeagues()
        answer.complete(serieATeams)
        assertEquals(PickerStep.League(SERVED_LEAGUES), vm.step.value)
    }

    @Test
    fun `picking a team during onboarding saves it and finishes onboarding`() = runTest {
        val vm = viewModel(PickerFlow.ONBOARDING)
        vm.selectLeague("Serie A")
        vm.selectTeam("Inter")
        verify { store.save(FavouriteTeam("Serie A", "Inter")) }
        assertEquals(PickerOutcome.ONBOARDING_FINISHED, vm.outcome.first())
    }

    @Test
    fun `switching league from settings saves the new team and relaunches`() = runTest {
        val vm = viewModel(PickerFlow.CHANGE_LEAGUE)
        assertEquals(PickerStep.League(SERVED_LEAGUES), vm.step.value)
        vm.selectLeague("Serie A")
        vm.selectTeam("Napoli")
        verify { store.save(FavouriteTeam("Serie A", "Napoli")) }
        assertEquals(PickerOutcome.RELAUNCH, vm.outcome.first())
    }

    @Test
    fun `switching team starts on the saved league's teams and relaunches`() = runTest {
        every { store.load() } returns FavouriteTeam("Serie A", "Inter")
        val vm = viewModel(PickerFlow.CHANGE_TEAM)
        assertEquals(PickerStep.Team("Serie A", TeamsUiState.Success(serieA)), vm.step.value)
        vm.selectTeam("Milan")
        verify { store.save(FavouriteTeam("Serie A", "Milan")) }
        assertEquals(PickerOutcome.RELAUNCH, vm.outcome.first())
    }
}
