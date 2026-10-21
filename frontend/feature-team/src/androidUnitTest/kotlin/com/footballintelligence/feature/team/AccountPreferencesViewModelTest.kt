package com.footballintelligence.feature.team

import com.footballintelligence.core.model.AccountPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.team.repository.AccountPreferencesRepository
import io.mockk.coEvery
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AccountPreferencesViewModelTest {
    private val repository = mockk<AccountPreferencesRepository>()
    private val arsenal = FavouriteTeam("Premier League", "Arsenal")

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        every { repository.sessionToken } returns "A"
    }

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `loading never confirms onboarding`() = runTest {
        coEvery { repository.load("A") } coAnswers { CompletableDeferred<NetworkResult<AccountPreferences>>().await() }
        assertEquals(AccountPreferencesUiState.Loading, AccountPreferencesViewModel(repository).state.value)
    }

    @Test
    fun `only successful null confirms a fresh account`() {
        coEvery { repository.load("A") } returns NetworkResult.Success(AccountPreferences("a@example.com", null))
        assertEquals(AccountPreferencesUiState.ConfirmedEmpty, AccountPreferencesViewModel(repository).state.value)
    }

    @Test
    fun `server favourite survives an empty device cache`() {
        coEvery { repository.load("A") } returns NetworkResult.Success(AccountPreferences("a@example.com", arsenal))
        assertEquals(AccountPreferencesUiState.Success(arsenal), AccountPreferencesViewModel(repository).state.value)
    }

    @Test
    fun `failed load stays retryable until server confirms empty`() {
        coEvery { repository.load("A") } returns NetworkResult.Error("Unavailable")
        val vm = AccountPreferencesViewModel(repository)
        assertInstanceOf(AccountPreferencesUiState.Error::class.java, vm.state.value)
        coEvery { repository.load("A") } returns NetworkResult.Success(AccountPreferences("a@example.com", null))
        vm.retry()
        assertEquals(AccountPreferencesUiState.ConfirmedEmpty, vm.state.value)
    }

    @Test
    fun `a delayed result for a signed out account cannot navigate`() = runTest {
        val answer = CompletableDeferred<NetworkResult<AccountPreferences>>()
        coEvery { repository.load("A") } coAnswers { answer.await() }
        val vm = AccountPreferencesViewModel(repository)
        every { repository.sessionToken } returns "B"
        answer.complete(NetworkResult.Success(AccountPreferences("a@example.com", arsenal)))
        assertEquals(AccountPreferencesUiState.Loading, vm.state.value)
    }
}
