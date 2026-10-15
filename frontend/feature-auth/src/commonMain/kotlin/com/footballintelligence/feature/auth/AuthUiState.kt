package com.footballintelligence.feature.auth

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.NetworkResult

/** The two ways in: an existing account, or an invite code from the owner. */
enum class AuthTab { SIGN_IN, INVITE_CODE }

/** What the user has typed. The email is shared by both tabs. */
data class AuthForm(
    val tab: AuthTab = AuthTab.SIGN_IN,
    val email: String = "",
    val password: String = "",
    val code: String = "",
    val newPassword: String = "",
) {
    /** True once every field on the current tab has something in it. */
    val isComplete: Boolean
        get() = email.isNotBlank() &&
            when (tab) {
                AuthTab.SIGN_IN -> password.isNotEmpty()
                AuthTab.INVITE_CODE -> code.isNotBlank() && newPassword.isNotEmpty()
            }
}

/** What the user can do on the sign-in screen. */
data class AuthEvents(
    val onSelectTab: (AuthTab) -> Unit = {},
    val onEmailChange: (String) -> Unit = {},
    val onPasswordChange: (String) -> Unit = {},
    val onCodeChange: (String) -> Unit = {},
    val onNewPasswordChange: (String) -> Unit = {},
    val onSubmit: () -> Unit = {},
)

/** Why sign-in failed, each with its own wording on screen. */
enum class AuthProblem {
    WRONG_CREDENTIALS,
    TOO_MANY_TRIES,
    INVALID_INVITE,
    INVITE_USED,
    INVITE_EXPIRED,
    PASSWORD_TOO_SHORT,
    BLOCKED,

    /** No connection or an unexpected answer: the app's usual error wording. */
    OTHER,
}

/** UI state for the sign-in and invite code screen. */
sealed class AuthUiState {
    data object Idle : AuthUiState()
    data object Loading : AuthUiState()

    /** Still loading after [WAKING_UP_AFTER_MS]: the server is most likely starting from cold. */
    data object WakingUp : AuthUiState()
    data class Error(
        val problem: AuthProblem,
        val kind: ErrorKind = ErrorKind.UNKNOWN,
        val message: String = "",
    ) : AuthUiState()
}

/** True while a sign-in is on its way: the form is locked and the button spins. */
val AuthUiState.isBusy: Boolean
    get() = this == AuthUiState.Loading || this == AuthUiState.WakingUp

/** The server answers in about a second when warm; longer means it is starting up. */
const val WAKING_UP_AFTER_MS = 4_000L

/** The backend's sign-in failures (ADR 022) as screen errors. */
fun NetworkResult.Error.toAuthError(): AuthUiState.Error {
    val problem = if (kind == ErrorKind.SERVER_BUSY) AuthProblem.OTHER else authProblemFor(code)
    return AuthUiState.Error(problem, kind, message)
}

private fun authProblemFor(code: Int?): AuthProblem =
    when (code) {
        HTTP_BAD_REQUEST -> AuthProblem.INVALID_INVITE
        HTTP_UNAUTHORIZED -> AuthProblem.WRONG_CREDENTIALS
        HTTP_FORBIDDEN -> AuthProblem.BLOCKED
        HTTP_CONFLICT -> AuthProblem.INVITE_USED
        HTTP_GONE -> AuthProblem.INVITE_EXPIRED
        HTTP_UNPROCESSABLE -> AuthProblem.PASSWORD_TOO_SHORT
        HTTP_TOO_MANY_REQUESTS -> AuthProblem.TOO_MANY_TRIES
        else -> AuthProblem.OTHER
    }

/** The backend's minimum password length for an invite. */
const val MIN_PASSWORD_LENGTH = 10

private const val HTTP_BAD_REQUEST = 400
private const val HTTP_UNAUTHORIZED = 401
private const val HTTP_FORBIDDEN = 403
private const val HTTP_CONFLICT = 409
private const val HTTP_GONE = 410
private const val HTTP_UNPROCESSABLE = 422
private const val HTTP_TOO_MANY_REQUESTS = 429
