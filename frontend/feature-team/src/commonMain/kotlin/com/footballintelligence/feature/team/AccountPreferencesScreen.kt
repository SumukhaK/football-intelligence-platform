package com.footballintelligence.feature.team

import androidx.compose.runtime.Composable
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.errorMessage

/** Shows loading or retry while the account's authoritative favourite is fetched. */
@Composable
fun AccountPreferencesScreen(state: AccountPreferencesUiState, onRetry: () -> Unit) {
    when (state) {
        is AccountPreferencesUiState.Error -> ErrorView(errorMessage(state.kind, state.message), onRetry)
        AccountPreferencesUiState.Loading,
        AccountPreferencesUiState.ConfirmedEmpty,
        is AccountPreferencesUiState.Success,
        -> LoadingView()
    }
}
