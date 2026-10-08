package com.footballintelligence.app

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.compose.composable
import com.footballintelligence.core.navigation.Screen
import com.footballintelligence.feature.auth.AuthEvents
import com.footballintelligence.feature.auth.AuthScreen
import com.footballintelligence.feature.auth.AuthViewModel
import com.footballintelligence.feature.auth.ConsentScreen
import com.footballintelligence.feature.auth.ConsentUiState
import com.footballintelligence.feature.auth.ConsentViewModel
import org.koin.androidx.compose.koinViewModel

/** Routes drawn edge to edge, under the status bar, without the bottom bar. */
val FULL_SCREEN_ROUTES = setOf(Screen.Auth.route, Screen.Consent.route)

/**
 * Sign-in and the notice (ADR 022). Signing in is noticed by [FollowSession];
 * [onReady] continues into the app once the notice is accepted.
 */
fun NavGraphBuilder.authRoutes(onReady: () -> Unit) {
    composable(Screen.Auth.route) {
        val vm: AuthViewModel = koinViewModel()
        val form by vm.form.collectAsState()
        val state by vm.state.collectAsState()
        val events = remember(vm) {
            AuthEvents(
                onSelectTab = vm::selectTab,
                onEmailChange = vm::updateEmail,
                onPasswordChange = vm::updatePassword,
                onCodeChange = vm::updateCode,
                onNewPasswordChange = vm::updateNewPassword,
                onSubmit = vm::submit,
            )
        }
        AuthScreen(form = form, uiState = state, events = events)
    }

    composable(Screen.Consent.route) {
        val vm: ConsentViewModel = koinViewModel()
        val state by vm.state.collectAsState()
        LaunchedEffect(state) {
            if (state == ConsentUiState.Accepted) onReady()
        }
        ConsentScreen(
            uiState = state,
            onStoreQuestionsChange = vm::setStoreQuestions,
            onAccept = vm::accept,
            onSignOut = vm::signOut,
            onRetry = vm::retry,
        )
    }
}

/**
 * Keeps the screen in step with the session: losing it (sign out, or any
 * request answered 401) returns to sign-in from anywhere, and signing in
 * moves on to the notice.
 */
@Composable
fun FollowSession(navController: NavHostController, signedIn: Boolean) {
    LaunchedEffect(signedIn) {
        val route = navController.currentDestination?.route
        when {
            !signedIn && route != Screen.Auth.route -> navController.restartAt(Screen.Auth.route)
            signedIn && route == Screen.Auth.route -> navController.restartAt(Screen.Consent.route)
        }
    }
}

/** Opens [route] with nothing behind it, so back leaves the app. */
fun NavHostController.restartAt(route: String) {
    navigate(route) { popUpTo(graph.id) { inclusive = true } }
}
