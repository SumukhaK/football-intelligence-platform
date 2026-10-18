package com.footballintelligence.app

import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import com.footballintelligence.core.navigation.Screen
import com.footballintelligence.feature.team.AccountPreferencesScreen
import com.footballintelligence.feature.team.AccountPreferencesUiState
import com.footballintelligence.feature.team.AccountPreferencesViewModel
import org.koin.androidx.compose.koinViewModel

/** Routes only on a successful server response; loading and failures retain the retry gate. */
fun NavGraphBuilder.accountPreferencesRoute(navController: NavHostController) {
    composable(Screen.AccountPreferences.route) {
        val vm: AccountPreferencesViewModel = koinViewModel()
        val state by vm.state.collectAsState()
        LaunchedEffect(state) {
            state.destination()?.let { navController.restartAt(it.route) }
        }
        AccountPreferencesScreen(state, onRetry = vm::retry)
    }
}

/** Null retains the account gate while the server has not confirmed a usable result. */
internal fun AccountPreferencesUiState.destination(): Screen? = when (this) {
    AccountPreferencesUiState.ConfirmedEmpty -> Screen.Onboarding
    is AccountPreferencesUiState.Success -> Screen.Home
    AccountPreferencesUiState.Loading, is AccountPreferencesUiState.Error -> null
}
