package com.footballintelligence.app

import android.content.Context
import android.content.Intent
import androidx.activity.compose.BackHandler
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import com.footballintelligence.feature.team.PickerFlow
import com.footballintelligence.feature.team.PickerOutcome
import com.footballintelligence.feature.team.PickerStep
import com.footballintelligence.feature.team.TeamPickerScreen
import com.footballintelligence.feature.team.TeamPickerViewModel
import org.koin.androidx.compose.koinViewModel
import org.koin.core.parameter.parametersOf

/**
 * The favourite team picker for [flow]. System back on the team step returns
 * to the leagues; saving finishes onboarding or relaunches the app.
 */
@Composable
fun TeamPickerRoute(flow: PickerFlow, onLeave: () -> Unit, onOnboardingFinished: () -> Unit) {
    val vm: TeamPickerViewModel = koinViewModel(parameters = { parametersOf(flow) })
    val step by vm.step.collectAsState()
    val context = LocalContext.current
    LaunchedEffect(vm) {
        vm.outcome.collect { outcome ->
            when (outcome) {
                PickerOutcome.ONBOARDING_FINISHED -> onOnboardingFinished()
                PickerOutcome.RELAUNCH -> context.relaunch()
            }
        }
    }
    BackHandler(enabled = step is PickerStep.Team, onBack = vm::backToLeagues)
    TeamPickerScreen(
        step = step,
        isOnboarding = flow == PickerFlow.ONBOARDING,
        onSelectLeague = vm::selectLeague,
        onSelectTeam = vm::selectTeam,
        onBackToLeagues = vm::backToLeagues,
        onRetry = vm::retryTeams,
        onLeave = onLeave,
    )
}

/**
 * Restarts the app in a fresh task. Unlike recreate(), this clears every
 * ViewModel and the back stack, so all screens load the new team's data.
 */
private fun Context.relaunch() {
    val launcher = checkNotNull(packageManager.getLaunchIntentForPackage(packageName)).component
    startActivity(Intent.makeRestartActivityTask(launcher))
}
