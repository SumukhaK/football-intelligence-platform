package com.footballintelligence.feature.team

import androidx.compose.animation.ExperimentalSharedTransitionApi
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.grid.itemsIndexed
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LeagueEmblem
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.TeamCrest
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_pick_league
import com.footballintelligence.feature.team.resources.cd_pick_team
import com.footballintelligence.feature.team.resources.picker_league_heading
import com.footballintelligence.feature.team.resources.picker_team_heading
import com.footballintelligence.feature.team.resources.picker_teams_empty
import com.footballintelligence.feature.team.resources.picker_welcome_intro
import kotlinx.coroutines.delay
import org.jetbrains.compose.resources.stringResource

@OptIn(ExperimentalSharedTransitionApi::class)
@Composable
private fun Modifier.sharedEmblem(league: String, scopes: PickerScopes): Modifier = with(scopes.shared) {
    this@sharedEmblem.sharedElement(rememberSharedContentState("emblem-$league"), scopes.visibility)
}

@OptIn(ExperimentalSharedTransitionApi::class)
@Composable
private fun Modifier.sharedName(league: String, scopes: PickerScopes): Modifier = with(scopes.shared) {
    this@sharedName.sharedBounds(rememberSharedContentState("name-$league"), scopes.visibility)
}

/** League step: a two-column grid of large emblem cards. */
@Composable
internal fun LeagueGrid(
    step: PickerStep.League,
    isOnboarding: Boolean,
    scopes: PickerScopes,
    onSelect: (String) -> Unit,
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(2),
        contentPadding = PaddingValues(16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = Modifier.fillMaxSize(),
    ) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                if (isOnboarding) {
                    Text(stringResource(Res.string.picker_welcome_intro), style = MaterialTheme.typography.bodyLarge)
                }
                Heading(stringResource(Res.string.picker_league_heading))
            }
        }
        items(step.leagues, key = { it }) { league ->
            ChoiceCard(
                selected = league == step.selected,
                description = stringResource(Res.string.cd_pick_league, league),
                onClick = { onSelect(league) },
            ) {
                LeagueEmblem(league, Modifier.sharedEmblem(league, scopes), size = LEAGUE_EMBLEM_SIZE)
                Text(
                    league,
                    style = MaterialTheme.typography.titleSmall,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.sharedName(league, scopes),
                )
            }
        }
    }
}

/** Team step: the chosen league's emblem as a header over a grid of crests. */
@Composable
internal fun TeamGrid(step: PickerStep.Team, scopes: PickerScopes, onSelect: (String) -> Unit, onRetry: () -> Unit) {
    Column(Modifier.fillMaxSize()) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(16.dp),
        ) {
            LeagueEmblem(step.league, Modifier.sharedEmblem(step.league, scopes), size = HEADER_EMBLEM_SIZE)
            Column {
                Text(
                    step.league,
                    style = MaterialTheme.typography.headlineSmall,
                    modifier = Modifier.sharedName(step.league, scopes),
                )
                Heading(stringResource(Res.string.picker_team_heading, step.league))
            }
        }
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
                CrestGrid(teams.teams, step.selected, onSelect)
            }
        }
    }
}

@Composable
private fun CrestGrid(teams: List<String>, selected: String?, onSelect: (String) -> Unit) {
    LazyVerticalGrid(
        columns = GridCells.Adaptive(TEAM_CELL_WIDTH),
        contentPadding = PaddingValues(start = 16.dp, end = 16.dp, bottom = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier.fillMaxSize(),
    ) {
        itemsIndexed(teams, key = { _, team -> team }) { index, team ->
            ChoiceCard(
                selected = team == selected,
                description = stringResource(Res.string.cd_pick_team, team),
                onClick = { onSelect(team) },
                modifier = Modifier.staggeredEnter(index),
            ) {
                TeamCrest(team, size = TEAM_CREST_SIZE)
                Text(
                    team,
                    style = MaterialTheme.typography.labelLarge,
                    textAlign = TextAlign.Center,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

/** A tappable card that shows a check and a primary outline when [selected]. */
@Composable
private fun ChoiceCard(
    selected: Boolean,
    description: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Card(
        onClick = onClick,
        border = if (selected) BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else null,
        colors = if (selected) {
            CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
        } else {
            CardDefaults.cardColors()
        },
        modifier = modifier
            .fillMaxWidth()
            .semantics {
                contentDescription = description
                this.selected = selected
            },
    ) {
        Box {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp, horizontal = 8.dp),
            ) { content() }
            if (selected) {
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.align(Alignment.TopEnd).padding(6.dp).size(20.dp),
                )
            }
        }
    }
}

@Composable
private fun Heading(text: String) {
    Text(text, style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
}

/** Fades and lifts each crest in, one after another, for the first screenful. */
@Composable
private fun Modifier.staggeredEnter(index: Int): Modifier {
    val progress = remember { Animatable(0f) }
    LaunchedEffect(Unit) {
        // Crests scrolled to later appear at once rather than after a long wait.
        if (index < STAGGERED_ITEMS) delay(index * STAGGER_MS)
        progress.animateTo(1f, tween(ENTER_MS))
    }
    return graphicsLayer {
        alpha = progress.value
        translationY = (1f - progress.value) * ENTER_LIFT.toPx()
    }
}

private val LEAGUE_EMBLEM_SIZE = 72.dp
private val HEADER_EMBLEM_SIZE = 56.dp
private val TEAM_CREST_SIZE = 48.dp
private val TEAM_CELL_WIDTH = 104.dp
private val ENTER_LIFT = 24.dp
private const val STAGGERED_ITEMS = 15
private const val STAGGER_MS = 35L
private const val ENTER_MS = 300
