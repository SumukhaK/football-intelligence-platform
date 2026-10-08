package com.footballintelligence.feature.auth

import android.content.res.Configuration
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.ui.PreviewSurface

private val signInForm = AuthForm(email = "sam@example.com", password = "matchday-2026")
private val inviteForm = AuthForm(
    tab = AuthTab.INVITE_CODE,
    email = "sam@example.com",
    code = "bX3k9_QpZr2LmN7vT0aYwQ",
    newPassword = "matchday-2026",
)
private const val NOTICE =
    "Football Intelligence is a private project shared with family and friends.\n\n" +
        "The text of your questions is stored only if you allow it below."

@Composable
private fun Auth(form: AuthForm, state: AuthUiState = AuthUiState.Idle) {
    PreviewSurface { AuthScreen(form = form, uiState = state, events = AuthEvents()) }
}

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun SignInPreview() = Auth(signInForm)

@Preview(heightDp = 844, widthDp = 390, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun SignInDarkPreview() = Auth(signInForm)

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun SignInLoadingPreview() = Auth(signInForm, AuthUiState.Loading)

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun SignInErrorPreview() = Auth(signInForm, AuthUiState.Error(AuthProblem.WRONG_CREDENTIALS))

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun SignInOfflinePreview() = Auth(signInForm, AuthUiState.Error(AuthProblem.OTHER, ErrorKind.OFFLINE))

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun InviteCodePreview() = Auth(inviteForm)

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun InviteCodeErrorPreview() = Auth(inviteForm, AuthUiState.Error(AuthProblem.INVALID_INVITE))

@Composable
private fun Consent(state: ConsentUiState) {
    PreviewSurface {
        ConsentScreen(uiState = state, onStoreQuestionsChange = {}, onAccept = {}, onSignOut = {}, onRetry = {})
    }
}

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun ConsentPreview() = Consent(ConsentUiState.Ready(NOTICE, version = 1))

@Preview(heightDp = 844, widthDp = 390, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun ConsentDarkPreview() = Consent(ConsentUiState.Ready(NOTICE, version = 1, storeQuestions = true))

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun ConsentSubmittingPreview() = Consent(ConsentUiState.Ready(NOTICE, version = 1, isSubmitting = true))

@Preview(heightDp = 844, widthDp = 390)
@Composable
private fun ConsentErrorPreview() = Consent(ConsentUiState.Error("", ErrorKind.OFFLINE))
