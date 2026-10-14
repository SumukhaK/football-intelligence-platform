package com.footballintelligence.feature.auth

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.Me
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.auth.repository.AuthRepository
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
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ConsentViewModelTest {
    private val repository = mockk<AuthRepository>(relaxUnitFun = true)

    private fun me(required: Boolean = true, version: Int = 1, text: String = "Notice v$version") =
        NetworkResult.Success(Me("sam@example.com", required, version, text, storeQuestions = false))

    @BeforeEach
    fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `the notice from the server is shown with storing off`() {
        coEvery { repository.me() } returns me()
        val vm = ConsentViewModel(repository)
        assertEquals(ConsentUiState.Ready("Notice v1", version = 1, storeQuestions = false), vm.state.value)
    }

    @Test
    fun `an accepted notice moves straight on`() {
        coEvery { repository.me() } returns me(required = false)
        assertEquals(ConsentUiState.Accepted, ConsentViewModel(repository).state.value)
    }

    @Test
    fun `accepting without storing questions sends the version shown`() {
        coEvery { repository.me() } returns me()
        coEvery { repository.acceptConsent(1, false) } returns me(required = false)
        val vm = ConsentViewModel(repository)
        vm.accept()
        coVerify { repository.acceptConsent(1, false) }
        assertEquals(ConsentUiState.Accepted, vm.state.value)
    }

    @Test
    fun `accepting with storing questions turned on sends it`() {
        coEvery { repository.me() } returns me()
        coEvery { repository.acceptConsent(1, true) } returns me(required = false)
        val vm = ConsentViewModel(repository)
        vm.setStoreQuestions(true)
        vm.accept()
        coVerify { repository.acceptConsent(1, true) }
        assertEquals(ConsentUiState.Accepted, vm.state.value)
    }

    @Test
    fun `an outdated notice is fetched again`() {
        coEvery { repository.me() } returnsMany listOf(me(version = 1), me(version = 2))
        coEvery { repository.acceptConsent(1, false) } returns NetworkResult.Error("Consent required", 403)
        val vm = ConsentViewModel(repository)
        vm.accept()
        coVerify(exactly = 2) { repository.me() }
        assertEquals(ConsentUiState.Ready("Notice v2", version = 2), vm.state.value)
    }

    @Test
    fun `a failed accept keeps the notice and shows why`() {
        coEvery { repository.me() } returns me()
        coEvery { repository.acceptConsent(any(), any()) } returns
            NetworkResult.Error("down", kind = ErrorKind.OFFLINE)
        val vm = ConsentViewModel(repository)
        vm.setStoreQuestions(true)
        vm.accept()
        val expected = ConsentUiState.Ready(
            "Notice v1",
            version = 1,
            storeQuestions = true,
            error = ConsentUiState.Error("down", ErrorKind.OFFLINE),
        )
        assertEquals(expected, vm.state.value)
    }

    @Test
    fun `offline at launch carries on with saved data`() {
        coEvery { repository.me() } returns NetworkResult.Error("down", kind = ErrorKind.OFFLINE)
        assertEquals(ConsentUiState.Accepted, ConsentViewModel(repository).state.value)
    }

    @Test
    fun `other failures can be retried`() {
        coEvery { repository.me() } returnsMany listOf(NetworkResult.Error("boom", 500), me())
        val vm = ConsentViewModel(repository)
        assertEquals(ConsentUiState.Error("boom"), vm.state.value)
        vm.retry()
        assertEquals(ConsentUiState.Ready("Notice v1", version = 1), vm.state.value)
    }

    @Test
    fun `signing out ends the session`() {
        coEvery { repository.me() } returns me()
        ConsentViewModel(repository).signOut()
        coVerify { repository.signOut() }
    }
}
