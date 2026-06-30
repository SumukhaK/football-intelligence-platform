package com.footballintelligence.feature.settings

import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.FootballApiService
import com.footballintelligence.feature.settings.repository.DefaultModelInfoRepository
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class ModelInfoRepositoryTest {

    private val api = mockk<FootballApiService>()
    private val repository = DefaultModelInfoRepository(api)

    private val modelInfo = ModelInfo(
        modelVersion = "v1.0",
        datasetVersion = "2023-24",
        trainingTimestamp = "2026-06-30T10:00:00",
        gitCommit = "abc1234",
        metrics = mapOf("test_accuracy" to 0.561),
    )

    @Test
    fun `getModelInfo returns success on api success`() = runTest {
        coEvery { api.getModel() } returns NetworkResult.Success(modelInfo)
        val result = repository.getModelInfo()
        assertTrue(result is NetworkResult.Success)
        assertEquals(modelInfo, (result as NetworkResult.Success).data)
    }

    @Test
    fun `getModelInfo returns error on api failure`() = runTest {
        coEvery { api.getModel() } returns NetworkResult.Error("503")
        val result = repository.getModelInfo()
        assertTrue(result is NetworkResult.Error)
    }
}
