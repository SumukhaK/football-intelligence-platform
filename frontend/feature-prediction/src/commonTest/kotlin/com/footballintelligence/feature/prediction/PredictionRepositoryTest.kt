package com.footballintelligence.feature.prediction

import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.buildNeutralFeatures
import com.footballintelligence.core.network.FootballApiService
import com.footballintelligence.feature.prediction.repository.DefaultPredictionRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class PredictionRepositoryTest {

    private val api = mockk<FootballApiService>()
    private val repository = DefaultPredictionRepository(api)

    private val request = PredictionRequest(
        homeTeam = "Arsenal",
        awayTeam = "Chelsea",
        features = buildNeutralFeatures(),
    )

    private val result = PredictionResult(
        homeTeam = "Arsenal",
        awayTeam = "Chelsea",
        predictedResult = "H",
        probabilityHome = 0.55,
        probabilityDraw = 0.25,
        probabilityAway = 0.20,
        confidence = 0.55,
        modelVersion = "test-v1",
    )

    @Test
    fun `predict delegates to api and returns success`() = runTest {
        coEvery { api.predict(request) } returns NetworkResult.Success(result)
        val response = repository.predict(request)
        assertTrue(response is NetworkResult.Success)
        assertEquals("H", (response as NetworkResult.Success).data.predictedResult)
        coVerify(exactly = 1) { api.predict(request) }
    }

    @Test
    fun `predict returns error when api fails`() = runTest {
        coEvery { api.predict(request) } returns NetworkResult.Error("503")
        val response = repository.predict(request)
        assertTrue(response is NetworkResult.Error)
    }

    @Test
    fun `explain delegates to api`() = runTest {
        coEvery { api.explain(request) } returns NetworkResult.Error("503")
        repository.explain(request)
        coVerify(exactly = 1) { api.explain(request) }
    }
}
