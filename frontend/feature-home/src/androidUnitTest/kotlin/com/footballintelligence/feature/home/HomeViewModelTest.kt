package com.footballintelligence.feature.home

import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.home.repository.HealthRepository
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

@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {
    private val repository = mockk<HealthRepository>()
    private val health = HealthStatus("ok", true, true, false, "0.1.0")

    @BeforeEach
    fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `fresh data has no offline time`() {
        coEvery { repository.getHealth() } returns NetworkResult.Success(health)
        val state = HomeViewModel(repository).state.value as HomeUiState.Success
        assertNull(state.savedAt)
    }

    @Test
    fun `saved data carries when it was saved`() {
        coEvery { repository.getHealth() } returns
            NetworkResult.Success(health, cachedAt = "2026-09-29T09:00:00Z")
        val state = HomeViewModel(repository).state.value as HomeUiState.Success
        assertNotNull(state.savedAt)
    }

    @Test
    fun `refresh reloads without leaving the content`() {
        coEvery { repository.getHealth() } returns NetworkResult.Success(health)
        val viewModel = HomeViewModel(repository)
        viewModel.refresh()
        coVerify(exactly = 2) { repository.getHealth() }
        assertEquals(HomeUiState.Success(health), viewModel.state.value)
        assertFalse(viewModel.isRefreshing.value)
    }
}
