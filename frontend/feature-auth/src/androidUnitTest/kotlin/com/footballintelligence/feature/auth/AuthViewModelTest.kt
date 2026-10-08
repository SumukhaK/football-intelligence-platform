package com.footballintelligence.feature.auth

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.auth.repository.AuthRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.CsvSource

@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {
    private val repository = mockk<AuthRepository>()
    private val vm by lazy { AuthViewModel(repository) }

    @BeforeEach
    fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    private fun fillSignIn() {
        vm.updateEmail("sam@example.com")
        vm.updatePassword("matchday-2026")
    }

    private fun fillInvite(password: String = "matchday-2026") {
        vm.selectTab(AuthTab.INVITE_CODE)
        vm.updateEmail("sam@example.com")
        vm.updateCode("bX3k9_QpZr2LmN7vT0aYwQ")
        vm.updateNewPassword(password)
    }

    @Test
    fun `signing in sends the email and password and keeps the spinner until the app moves on`() {
        coEvery { repository.signIn(any(), any()) } returns NetworkResult.Success(Unit)
        fillSignIn()
        vm.submit()
        coVerify { repository.signIn("sam@example.com", "matchday-2026") }
        assertEquals(AuthUiState.Loading, vm.state.value)
    }

    @Test
    fun `redeeming an invite sends the code and new password`() {
        coEvery { repository.redeemInvite(any(), any(), any()) } returns NetworkResult.Success(Unit)
        fillInvite()
        vm.submit()
        coVerify { repository.redeemInvite("sam@example.com", "bX3k9_QpZr2LmN7vT0aYwQ", "matchday-2026") }
    }

    @Test
    fun `the button shows progress while signing in`() {
        val answer = CompletableDeferred<NetworkResult<Unit>>()
        coEvery { repository.signIn(any(), any()) } coAnswers { answer.await() }
        fillSignIn()
        vm.submit()
        assertEquals(AuthUiState.Loading, vm.state.value)
        vm.submit()
        coVerify(exactly = 1) { repository.signIn(any(), any()) }
    }

    @ParameterizedTest
    @CsvSource(
        "401, WRONG_CREDENTIALS",
        "403, BLOCKED",
        "429, TOO_MANY_TRIES",
        "500, OTHER",
    )
    fun `sign-in failures map to their own message`(code: Int, problem: AuthProblem) {
        coEvery { repository.signIn(any(), any()) } returns NetworkResult.Error("nope", code)
        fillSignIn()
        vm.submit()
        assertEquals(problem, (vm.state.value as AuthUiState.Error).problem)
    }

    @ParameterizedTest
    @CsvSource("400, INVALID_INVITE", "422, PASSWORD_TOO_SHORT")
    fun `invite failures map to their own message`(code: Int, problem: AuthProblem) {
        coEvery { repository.redeemInvite(any(), any(), any()) } returns NetworkResult.Error("nope", code)
        fillInvite()
        vm.submit()
        assertEquals(problem, (vm.state.value as AuthUiState.Error).problem)
    }

    @Test
    fun `no connection uses the app's offline wording`() {
        coEvery { repository.signIn(any(), any()) } returns
            NetworkResult.Error("Connection refused", kind = ErrorKind.OFFLINE)
        fillSignIn()
        vm.submit()
        assertEquals(AuthUiState.Error(AuthProblem.OTHER, ErrorKind.OFFLINE, "Connection refused"), vm.state.value)
    }

    @Test
    fun `a short invite password is caught before sending`() {
        fillInvite(password = "short")
        vm.submit()
        assertEquals(AuthProblem.PASSWORD_TOO_SHORT, (vm.state.value as AuthUiState.Error).problem)
        coVerify(exactly = 0) { repository.redeemInvite(any(), any(), any()) }
    }

    @Test
    fun `an incomplete form is not sent`() {
        vm.updateEmail("sam@example.com")
        vm.submit()
        assertEquals(AuthUiState.Idle, vm.state.value)
        coVerify(exactly = 0) { repository.signIn(any(), any()) }
    }

    @Test
    fun `switching tabs keeps the email and clears the error`() {
        coEvery { repository.signIn(any(), any()) } returns NetworkResult.Error("nope", 401)
        fillSignIn()
        vm.submit()
        vm.selectTab(AuthTab.INVITE_CODE)
        assertEquals(AuthTab.INVITE_CODE, vm.form.value.tab)
        assertEquals("sam@example.com", vm.form.value.email)
        assertEquals(AuthUiState.Idle, vm.state.value)
    }

    @Test
    fun `typing clears the error`() {
        coEvery { repository.signIn(any(), any()) } returns NetworkResult.Error("nope", 401)
        fillSignIn()
        vm.submit()
        vm.updatePassword("matchday-2027")
        assertEquals(AuthUiState.Idle, vm.state.value)
    }
}
