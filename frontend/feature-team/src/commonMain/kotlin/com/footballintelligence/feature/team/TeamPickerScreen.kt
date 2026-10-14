package com.footballintelligence.feature.team

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedContentTransitionScope
import androidx.compose.animation.AnimatedVisibilityScope
import androidx.compose.animation.ContentTransform
import androidx.compose.animation.ExperimentalSharedTransitionApi
import androidx.compose.animation.SharedTransitionLayout
import androidx.compose.animation.SharedTransitionScope
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.picker_change_title
import com.footballintelligence.feature.team.resources.picker_welcome_title
import org.jetbrains.compose.resources.stringResource

/**
 * Favourite team picker: a grid of league emblems, then that league's crests.
 * The chosen league's emblem morphs into the team step's header and back.
 * Shown once on first launch ([isOnboarding]) and from Settings.
 */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalSharedTransitionApi::class)
@Composable
fun TeamPickerScreen(
    step: PickerStep,
    isOnboarding: Boolean,
    onSelectLeague: (String) -> Unit,
    onSelectTeam: (String) -> Unit,
    onBackToLeagues: () -> Unit,
    onRetry: () -> Unit,
    onLeave: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    val title = if (isOnboarding) Res.string.picker_welcome_title else Res.string.picker_change_title
                    Text(stringResource(title))
                },
                navigationIcon = {
                    when {
                        step is PickerStep.Team -> BackButton(onClick = onBackToLeagues)
                        !isOnboarding -> BackButton(onClick = onLeave)
                    }
                },
            )
        },
        modifier = modifier,
    ) { padding ->
        SharedTransitionLayout(Modifier.padding(padding)) {
            AnimatedContent(
                targetState = step,
                // Only a change of step animates; teams arriving update the team step in place.
                contentKey = { it is PickerStep.Team },
                transitionSpec = { crossfadeSteps() },
                label = "pickerStep",
            ) { current ->
                val scopes = PickerScopes(this@SharedTransitionLayout, this@AnimatedContent)
                when (current) {
                    is PickerStep.League -> LeagueGrid(current, isOnboarding, scopes, onSelectLeague)
                    is PickerStep.Team -> TeamGrid(current, scopes, onSelectTeam, onRetry)
                }
            }
        }
    }
}

/** The emblem carries the motion between steps, so the rest of each step just fades. */
private fun AnimatedContentTransitionScope<PickerStep>.crossfadeSteps(): ContentTransform =
    fadeIn() togetherWith fadeOut()

/** The scopes a picker step needs to share its league emblem and name with the other step. */
@OptIn(ExperimentalSharedTransitionApi::class)
internal class PickerScopes(val shared: SharedTransitionScope, val visibility: AnimatedVisibilityScope)
