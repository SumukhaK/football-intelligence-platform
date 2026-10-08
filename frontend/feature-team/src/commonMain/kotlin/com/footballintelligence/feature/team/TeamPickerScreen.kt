package com.footballintelligence.feature.team

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.AnimatedContentTransitionScope
import androidx.compose.animation.ContentTransform
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForwardIos
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_pick_league
import com.footballintelligence.feature.team.resources.cd_pick_team
import com.footballintelligence.feature.team.resources.picker_change_title
import com.footballintelligence.feature.team.resources.picker_league_heading
import com.footballintelligence.feature.team.resources.picker_team_heading
import com.footballintelligence.feature.team.resources.picker_teams_empty
import com.footballintelligence.feature.team.resources.picker_welcome_intro
import com.footballintelligence.feature.team.resources.picker_welcome_title
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/**
 * Favourite team picker: a league step, then that league's teams, sliding
 * between them. Shown once on first launch ([isOnboarding]) and from Settings.
 */
@OptIn(ExperimentalMaterial3Api::class)
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
        AnimatedContent(
            targetState = step,
            // Only a change of step animates; teams arriving update the team step in place.
            contentKey = { it is PickerStep.Team },
            transitionSpec = { slideBetweenSteps() },
            modifier = Modifier.padding(padding),
            label = "pickerStep",
        ) { current ->
            when (current) {
                is PickerStep.League -> LeagueStep(current.leagues, isOnboarding, onSelectLeague)
                is PickerStep.Team -> TeamStep(current, onSelectTeam, onRetry)
            }
        }
    }
}

/** Forward to the teams slides in from the right; back to the leagues slides in from the left. */
private fun AnimatedContentTransitionScope<PickerStep>.slideBetweenSteps(): ContentTransform {
    val direction = if (targetState is PickerStep.Team) 1 else -1
    return (slideInHorizontally { it * direction } + fadeIn()) togetherWith
        (slideOutHorizontally { -it * direction } + fadeOut())
}

@Composable
private fun LeagueStep(leagues: List<String>, isOnboarding: Boolean, onSelect: (String) -> Unit) {
    ChoiceList(
        heading = stringResource(Res.string.picker_league_heading),
        intro = if (isOnboarding) stringResource(Res.string.picker_welcome_intro) else null,
        choices = leagues,
        icon = Icons.Default.EmojiEvents,
        description = Res.string.cd_pick_league,
        onSelect = onSelect,
    )
}

@Composable
private fun TeamStep(step: PickerStep.Team, onSelect: (String) -> Unit, onRetry: () -> Unit) {
    when (val teams = step.teams) {
        is TeamsUiState.Loading -> LoadingView()
        is TeamsUiState.Error -> ErrorView(message = errorMessage(teams.kind, teams.message), onRetry = onRetry)
        is TeamsUiState.Success -> if (teams.teams.isEmpty()) {
            Text(
                stringResource(Res.string.picker_teams_empty, step.league),
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth().padding(32.dp),
            )
        } else {
            ChoiceList(
                heading = stringResource(Res.string.picker_team_heading, step.league),
                intro = null,
                choices = teams.teams,
                icon = Icons.Default.Shield,
                description = Res.string.cd_pick_team,
                onSelect = onSelect,
            )
        }
    }
}

@Suppress("LongParameterList") // Both steps share this list; each argument is one difference between them.
@Composable
private fun ChoiceList(
    heading: String,
    intro: String?,
    choices: List<String>,
    icon: ImageVector,
    description: StringResource,
    onSelect: (String) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.padding(bottom = 8.dp)) {
                intro?.let { Text(it, style = MaterialTheme.typography.bodyLarge) }
                Text(heading, style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
            }
        }
        items(choices, key = { it }) { choice ->
            val label = stringResource(description, choice)
            Card(modifier = Modifier.fillMaxWidth()) {
                ListItem(
                    headlineContent = { Text(choice) },
                    leadingContent = { Icon(icon, contentDescription = null) },
                    trailingContent = { Icon(Icons.AutoMirrored.Filled.ArrowForwardIos, contentDescription = null) },
                    modifier = Modifier
                        .clickable { onSelect(choice) }
                        .semantics { contentDescription = label },
                )
            }
        }
    }
}
