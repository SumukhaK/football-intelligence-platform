package com.footballintelligence.feature.auth

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.NetworkResult
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class AuthErrorTest {
    @Test
    fun `a wrong password says so`() {
        val error = NetworkResult.Error("Wrong email or password.", 401, ErrorKind.REJECTED).toAuthError()
        assertEquals(AuthProblem.WRONG_CREDENTIALS, error.problem)
    }

    @Test
    fun `the backend's lockout is too many tries`() {
        val error = NetworkResult.Error("Too many failed sign-ins.", 429, ErrorKind.REJECTED).toAuthError()
        assertEquals(AuthProblem.TOO_MANY_TRIES, error.problem)
    }

    @Test
    fun `a busy server is not mistaken for a lockout`() {
        val error = NetworkResult.Error("HTTP 429", 429, ErrorKind.SERVER_BUSY).toAuthError()
        assertEquals(AuthProblem.OTHER, error.problem)
        assertEquals(ErrorKind.SERVER_BUSY, error.kind)
    }
}
