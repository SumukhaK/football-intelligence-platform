package com.footballintelligence.feature.home

import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.FootballApiService
import com.footballintelligence.feature.home.repository.DefaultHealthRepository
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class HealthRepositoryTest {

    private val api = mockk<FootballApiService>()
    private val repository = DefaultHealthRepository(api)

    private val sampleHealth = HealthStatus(
        status = "ok",
        modelLoaded = true,
        explainabilityAvailable = true,
        assistantAvailable = true,
        version = "0.2.0",
    )

    @Test
    fun `getHealth returns success when api succeeds`() = runTest {
        coEvery { api.getHealth() } returns NetworkResult.Success(sampleHealth)
        val result = repository.getHealth()
        assertTrue(result is NetworkResult.Success)
        assertEquals(sampleHealth, (result as NetworkResult.Success).data)
    }

    @Test
    fun `getHealth returns error when api fails`() = runTest {
        coEvery { api.getHealth() } returns NetworkResult.Error("Connection refused")
        val result = repository.getHealth()
        assertTrue(result is NetworkResult.Error)
        assertEquals("Connection refused", (result as NetworkResult.Error).message)
    }
}
