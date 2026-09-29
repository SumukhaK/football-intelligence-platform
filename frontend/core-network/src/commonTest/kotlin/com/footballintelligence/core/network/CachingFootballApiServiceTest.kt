package com.footballintelligence.core.network

import com.footballintelligence.core.model.ChatRequest
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.CompetitionsResponse
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.TeamsResponse
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class CachingFootballApiServiceTest {
    private class MemoryCache : ResponseCache {
        val entries = mutableMapOf<String, CachedResponse>()
        override fun read(key: String): CachedResponse? = entries[key]
        override fun write(key: String, response: CachedResponse) {
            entries[key] = response
        }
    }

    /** Answers from [teams] until [online] is switched off. */
    private class FakeApi : FootballApiService {
        var online = true
        var teams = TeamsResponse("Premier League", "2026/27", listOf("Arsenal", "Chelsea"))
        var calls = 0

        private fun <T> answer(value: T): NetworkResult<T> {
            calls++
            return if (online) {
                NetworkResult.Success(value)
            } else {
                NetworkResult.Error("Connection refused", kind = ErrorKind.OFFLINE)
            }
        }

        override suspend fun getTeams(competition: String) = answer(teams.copy(competition = competition))
        override suspend fun predict(request: PredictionRequest) = answer(prediction)
        override suspend fun getHealth(): NetworkResult<HealthStatus> = error("unused")
        override suspend fun getModel(): NetworkResult<ModelInfo> = error("unused")
        override suspend fun getCompetitions(): NetworkResult<CompetitionsResponse> = error("unused")
        override suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult> =
            error("unused")
        override suspend fun getInsights(request: PredictionRequest): NetworkResult<Insights> =
            error("unused")
        override suspend fun chat(request: ChatRequest): NetworkResult<ChatResponse> = error("unused")
    }

    private val cache = MemoryCache()
    private val api = FakeApi()
    private val service = CachingFootballApiService(api, cache, clock = { "2026-09-29T09:00:00Z" })

    @Test
    fun `fresh responses are saved and not marked as cached`() = runTest {
        val result = service.getTeams("Bundesliga")
        result as NetworkResult.Success
        assertNull(result.cachedAt)
        assertEquals(1, cache.entries.size)
    }

    @Test
    fun `offline returns the saved response with its time`() = runTest {
        service.getTeams("Bundesliga")
        api.online = false
        val result = service.getTeams("Bundesliga")
        result as NetworkResult.Success
        assertEquals("Bundesliga", result.data.competition)
        assertEquals("2026-09-29T09:00:00Z", result.cachedAt)
    }

    @Test
    fun `each request has its own entry`() = runTest {
        service.getTeams("Bundesliga")
        api.online = false
        val result = service.getTeams("Serie A")
        assertTrue(result is NetworkResult.Error)
    }

    @Test
    fun `offline with nothing saved is still an offline error`() = runTest {
        api.online = false
        val result = service.predict(PredictionRequest("Arsenal", "Chelsea"))
        assertEquals(ErrorKind.OFFLINE, (result as NetworkResult.Error).kind)
    }

    @Test
    fun `server errors are not hidden by old data`() = runTest {
        service.getTeams("Bundesliga")
        val failing = object : FootballApiService by api {
            override suspend fun getTeams(competition: String): NetworkResult<TeamsResponse> =
                NetworkResult.Error("HTTP 422", kind = ErrorKind.REJECTED)
        }
        val result = CachingFootballApiService(failing, cache) { "later" }.getTeams("Bundesliga")
        assertEquals(ErrorKind.REJECTED, (result as NetworkResult.Error).kind)
    }

    private companion object {
        val prediction = PredictionResult(
            homeTeam = "Arsenal",
            awayTeam = "Chelsea",
            predictedResult = "H",
            probabilityHome = 0.5,
            probabilityDraw = 0.3,
            probabilityAway = 0.2,
            confidence = 0.5,
            modelVersion = "v1",
        )
    }
}
