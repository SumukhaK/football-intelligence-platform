package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.Fixture
import com.footballintelligence.core.model.FixturesResponse
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.TeamsResponse
import com.footballintelligence.core.network.FootballApiService
import com.footballintelligence.feature.team.repository.DefaultTeamRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class TeamRepositoryTest {
    private val api = mockk<FootballApiService>()
    private val repository = DefaultTeamRepository(api)
    private val arsenal = FavouriteTeam("Premier League", "Arsenal")

    private val fixtures = listOf(
        Fixture("2026-10-10", null, "Arsenal", "Leeds", "Matchday 6"),
        Fixture("2026-10-10", null, "Man City", "Fulham", "Matchday 6"),
        Fixture("2026-10-18", null, "Everton", "Arsenal", "Matchday 7"),
    )

    @Test
    fun `team fixtures keep only the team's matches in order`() = runTest {
        coEvery { api.getFixtures("Premier League") } returns
            NetworkResult.Success(FixturesResponse("Premier League", fixtures))
        val result = repository.getTeamFixtures(arsenal) as NetworkResult.Success
        assertEquals(listOf(fixtures[0], fixtures[2]), result.data)
    }

    @Test
    fun `team fixtures keep when saved data was saved`() = runTest {
        coEvery { api.getFixtures(any()) } returns
            NetworkResult.Success(FixturesResponse("Premier League", fixtures), cachedAt = "2026-10-01T09:00:00Z")
        val result = repository.getTeamFixtures(arsenal) as NetworkResult.Success
        assertEquals("2026-10-01T09:00:00Z", result.cachedAt)
    }

    @Test
    fun `team fixtures pass errors through`() = runTest {
        val error = NetworkResult.Error("Connection refused", kind = ErrorKind.OFFLINE)
        coEvery { api.getFixtures(any()) } returns error
        assertEquals(error, repository.getTeamFixtures(arsenal))
    }

    @Test
    fun `teams come from the chosen league`() = runTest {
        val teams = TeamsResponse("Serie A", "2026/27", listOf("Inter", "Milan"))
        coEvery { api.getTeams("Serie A") } returns NetworkResult.Success(teams)
        assertEquals(NetworkResult.Success(teams), repository.getTeams("Serie A"))
    }

    @Test
    fun `predict, explain and insights delegate to the api`() = runTest {
        val request = PredictionRequest("Arsenal", "Leeds", "Premier League")
        val error = NetworkResult.Error("503")
        coEvery { api.predict(request) } returns error
        coEvery { api.explain(request) } returns error
        coEvery { api.getInsights(request) } returns error
        repository.predict(request)
        repository.explain(request)
        repository.insights(request)
        coVerify(exactly = 1) {
            api.predict(request)
            api.explain(request)
            api.getInsights(request)
        }
    }
}
