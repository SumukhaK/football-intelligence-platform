package com.footballintelligence.feature.team

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsTopHeight
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.designsystem.GreenPrimary
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.account_sign_out
import org.jetbrains.compose.resources.stringResource

/**
 * Shows loading or retry while the account's authoritative favourite is fetched.
 * Sign out is the way out when the server stays unreachable.
 */
@Composable
fun AccountPreferencesScreen(state: AccountPreferencesUiState, onRetry: () -> Unit, onSignOut: () -> Unit) {
    // The status bar icons are light everywhere, so this bar-less screen paints the green behind them.
    Spacer(Modifier.fillMaxWidth().windowInsetsTopHeight(WindowInsets.statusBars).background(GreenPrimary))
    when (state) {
        is AccountPreferencesUiState.Error -> Box(Modifier.fillMaxSize()) {
            ErrorView(errorMessage(state.kind, state.message), onRetry)
            TextButton(
                onClick = onSignOut,
                modifier = Modifier.align(Alignment.BottomCenter).navigationBarsPadding().padding(bottom = 24.dp),
            ) {
                Text(stringResource(Res.string.account_sign_out))
            }
        }
        AccountPreferencesUiState.Loading,
        AccountPreferencesUiState.ConfirmedEmpty,
        is AccountPreferencesUiState.Success,
        -> LoadingView()
    }
}
