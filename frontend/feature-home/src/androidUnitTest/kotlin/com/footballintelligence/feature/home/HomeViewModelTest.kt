package com.footballintelligence.feature.home

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.Fixture
import com.footballintelligence.core.model.FixturesResponse
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.home.repository.FixturesRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.time.ZoneId
import java.util.Locale

@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {
    private val repository = mockk<FixturesRepository>()
    private val zone = ZoneId.of("Europe/London")

    private val fixtures = listOf(
        Fixture("2026-10-10", "2026-10-10T12:30:00+01:00", "Arsenal", "Leeds", "Matchday 6"),
        Fixture("2026-10-10", null, "Man City", "Fulham", "Matchday 6"),
        Fixture("2026-10-18", "2026-10-18T16:30:00+01:00", "Everton", "Chelsea", "Matchday 7"),
    )

    private fun respond(competition: String, cachedAt: String? = null) {
        coEvery { repository.getFixtures(competition) } returns
            NetworkResult.Success(FixturesResponse(competition, fixtures), cachedAt)
    }

    private fun viewModel() = HomeViewModel(repository, zone, Locale.US)

    @BeforeEach
    fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `the premier league is selected first`() {
        respond("Premier League")
        val vm = viewModel()
        assertEquals("Premier League", vm.selectedLeague.value)
        coVerify { repository.getFixtures("Premier League") }
    }

    @Test
    fun `fixtures are grouped by day with local kick-off times`() {
        respond("Premier League")
        val state = viewModel().state.value as HomeUiState.Success
        assertEquals(listOf("Sat 10 Oct", "Sun 18 Oct"), state.days.map { it.label })
        assertEquals(
            listOf(FixtureRow("Arsenal", "Leeds", "12:30"), FixtureRow("Man City", "Fulham", null)),
            state.days.first().fixtures,
        )
    }

    @Test
    fun `choosing a league loads its fixtures`() {
        respond("Premier League")
        respond("Serie A")
        val vm = viewModel()
        vm.selectLeague("Serie A")
        assertEquals("Serie A", vm.selectedLeague.value)
        coVerify { repository.getFixtures("Serie A") }
        assertEquals(HomeUiState.Success::class, vm.state.value::class)
    }

    @Test
    fun `saved data carries when it was saved`() {
        respond("Premier League", cachedAt = "2026-09-29T09:00:00Z")
        val state = viewModel().state.value as HomeUiState.Success
        assertNotNull(state.savedAt)
    }

    @Test
    fun `fresh data has no offline time`() {
        respond("Premier League")
        assertNull((viewModel().state.value as HomeUiState.Success).savedAt)
    }

    @Test
    fun `an unreachable server is an error`() {
        coEvery { repository.getFixtures(any()) } returns
            NetworkResult.Error("Connection refused", kind = ErrorKind.OFFLINE)
        val state = viewModel().state.value as HomeUiState.Error
        assertEquals(ErrorKind.OFFLINE, state.kind)
    }

    @Test
    fun `refresh reloads the selected league without leaving the content`() {
        respond("Premier League")
        val vm = viewModel()
        vm.refresh()
        coVerify(exactly = 2) { repository.getFixtures("Premier League") }
        assertEquals(HomeUiState.Success::class, vm.state.value::class)
        assertFalse(vm.isRefreshing.value)
    }

    @Test
    fun `no upcoming fixtures is an empty list, not an error`() {
        coEvery { repository.getFixtures(any()) } returns
            NetworkResult.Success(FixturesResponse("Premier League", emptyList()))
        assertEquals(emptyList<FixtureDay>(), (viewModel().state.value as HomeUiState.Success).days)
    }
}
