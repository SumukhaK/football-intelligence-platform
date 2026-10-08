package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.OutlookPoint
import com.footballintelligence.core.model.TeamOutlook
import com.footballintelligence.core.model.TeamProjection
import com.footballintelligence.core.model.TeamStrength
import com.footballintelligence.feature.team.repository.TeamRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.time.Instant
import java.time.ZoneId
import java.util.Locale

/** The Season outlook part of [MyTeamViewModel]. */
@OptIn(ExperimentalCoroutinesApi::class)
class SeasonOutlookViewModelTest {
    private val arsenal = FavouriteTeam("Premier League", "Arsenal")
    private val repository = mockk<TeamRepository>()
    private val store = mockk<FavouriteTeamStore> { every { load() } returns arsenal }

    private val city = TeamProjection("Man City", 15, 80.44, 1, 0.512, 0.951, 0.0)
    private val arsenalRow = TeamProjection("Arsenal", 13, 74.6, 2, 0.2314, 0.7926, 0.004)
    private val outlook = TeamOutlook(
        competition = "Premier League",
        season = "2026/27",
        team = "Arsenal",
        asOf = "2026-10-08",
        modelVersion = "dc-2026-10-08",
        simulations = 10_000,
        historySimulations = 2_000,
        projection = arsenalRow,
        strengths = TeamStrength(attack = 1.23, defence = 0.69),
        table = listOf(city, arsenalRow),
        history = listOf(
            OutlookPoint("2026-08-14", 0, 3, 0.18, 0.71, 0.01),
            OutlookPoint("2026-08-23", 2, 2, 0.25, 0.8, 0.0),
        ),
    )

    private fun respond(result: NetworkResult<TeamOutlook>) {
        coEvery { repository.getTeamFixtures(any()) } returns NetworkResult.Success(emptyList())
        coEvery { repository.getOutlook(arsenal) } returns result
    }

    private fun viewModel() = MyTeamViewModel(
        repository,
        store,
        { Instant.parse("2026-10-08T12:00:00Z") },
        ZoneId.of("Europe/London"),
        Locale.US,
    )

    @BeforeEach
    fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `the outlook shows the team's projected finish in whole percentages`() {
        respond(NetworkResult.Success(outlook))
        val result = (viewModel().outlookState.value as SeasonOutlookUiState.Success).outlook
        assertEquals(2, result.position)
        assertEquals(13, result.currentPoints)
        assertEquals(75, result.expectedPoints)
        assertEquals(listOf(23, 79, 0), listOf(result.titlePercent, result.topFourPercent, result.relegationPercent))
        assertEquals(1.23, result.attack)
        assertEquals(0.69, result.defence)
    }

    @Test
    fun `the history keeps every point in order for the chart`() {
        respond(NetworkResult.Success(outlook))
        val history = (viewModel().outlookState.value as SeasonOutlookUiState.Success).outlook.history
        assertEquals(
            listOf(ChancePoint(0, 0.18f, 0.71f, 0.01f), ChancePoint(2, 0.25f, 0.8f, 0.0f)),
            history,
        )
    }

    @Test
    fun `the projected table marks the favourite team`() {
        respond(NetworkResult.Success(outlook))
        val table = (viewModel().outlookState.value as SeasonOutlookUiState.Success).outlook.table
        assertEquals(
            listOf(
                TableRow(1, "Man City", 15, 80, 51, 95, 0, isFavourite = false),
                TableRow(2, "Arsenal", 13, 75, 23, 79, 0, isFavourite = true),
            ),
            table,
        )
    }

    @Test
    fun `saved data carries when it was saved`() {
        respond(NetworkResult.Success(outlook, cachedAt = "2026-10-07T09:00:00Z"))
        assertNotNull((viewModel().outlookState.value as SeasonOutlookUiState.Success).savedAt)
    }

    @Test
    fun `a failed outlook is an error and leaves the next match alone`() {
        respond(NetworkResult.Error("Season outlook not available", kind = ErrorKind.SERVER_BUSY))
        val vm = viewModel()
        assertEquals(ErrorKind.SERVER_BUSY, (vm.outlookState.value as SeasonOutlookUiState.Error).kind)
        assertEquals(MyTeamUiState.NoUpcomingMatch("Arsenal"), vm.state.value)
    }

    @Test
    fun `refresh and retry reload the outlook`() {
        respond(NetworkResult.Success(outlook))
        val vm = viewModel()
        vm.refresh()
        vm.retry()
        coVerify(exactly = 3) { repository.getOutlook(arsenal) }
    }
}
