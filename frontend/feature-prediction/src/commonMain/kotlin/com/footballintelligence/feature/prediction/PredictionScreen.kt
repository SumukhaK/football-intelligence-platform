package com.footballintelligence.feature.prediction

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.OfflineBanner
import com.footballintelligence.core.ui.RefreshableContent
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.prediction.resources.Res
import com.footballintelligence.feature.prediction.resources.action_predict
import com.footballintelligence.feature.prediction.resources.away_team
import com.footballintelligence.feature.prediction.resources.cd_predict
import com.footballintelligence.feature.prediction.resources.cd_team_dropdown
import com.footballintelligence.feature.prediction.resources.home_team
import com.footballintelligence.feature.prediction.resources.league
import com.footballintelligence.feature.prediction.resources.prediction_title
import com.footballintelligence.feature.prediction.resources.season_note
import com.footballintelligence.feature.prediction.resources.select_teams
import com.footballintelligence.feature.prediction.resources.teams_must_differ
import com.footballintelligence.feature.prediction.resources.versus
import org.jetbrains.compose.resources.stringResource

/** Team selection screen for submitting a match prediction. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PredictionScreen(
    uiState: PredictionInputUiState,
    competitionsState: CompetitionsUiState,
    teamsState: TeamsUiState,
    onSelectCompetition: (String) -> Unit,
    onPredict: (homeTeam: String, awayTeam: String) -> Unit,
    onRetryTeams: () -> Unit,
    onNavigateToResult: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    isRefreshing: Boolean = false,
    onRefresh: () -> Unit = {},
    presetTeams: Pair<String, String>? = null,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.prediction_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        modifier = modifier,
    ) { padding ->
        when (uiState) {
            is PredictionInputUiState.Loading -> LoadingView(Modifier.padding(padding))
            is PredictionInputUiState.Error -> ErrorView(
                message = errorMessage(uiState.kind, uiState.message),
                modifier = Modifier.padding(padding),
            )
            is PredictionInputUiState.Success -> {
                // Navigate once per result, not on every recomposition.
                LaunchedEffect(uiState.result) { onNavigateToResult() }
                LoadingView(Modifier.padding(padding))
            }
            is PredictionInputUiState.Idle -> Column(Modifier.padding(padding)) {
                if (competitionsState is CompetitionsUiState.Success) {
                    LeaguePicker(
                        state = competitionsState,
                        onSelect = onSelectCompetition,
                        modifier = Modifier.padding(start = 16.dp, end = 16.dp, top = 16.dp),
                    )
                }
                val league = (competitionsState as? CompetitionsUiState.Success)?.selected.orEmpty()
                when (teamsState) {
                    is TeamsUiState.Loading -> LoadingView(Modifier.weight(1f))
                    is TeamsUiState.Error -> ErrorView(
                        message = errorMessage(teamsState.kind, teamsState.message),
                        onRetry = onRetryTeams,
                        modifier = Modifier.weight(1f),
                    )
                    is TeamsUiState.Success -> RefreshableContent(
                        isRefreshing = isRefreshing,
                        onRefresh = onRefresh,
                        modifier = Modifier.weight(1f),
                    ) {
                        Column {
                            OfflineBanner(teamsState.savedAt)
                            PredictionInputContent(
                                league = league,
                                season = teamsState.season,
                                teams = teamsState.teams,
                                presetTeams = presetTeams,
                                onPredict = onPredict,
                            )
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PredictionInputContent(
    league: String,
    season: String,
    teams: List<String>,
    presetTeams: Pair<String, String>?,
    onPredict: (homeTeam: String, awayTeam: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    // Keyed on the list so a reloaded team list never leaves a stale selection.
    var homeTeam by rememberSaveable(teams, presetTeams) {
        mutableStateOf(presetTeams?.first?.takeIf { it in teams } ?: teams[0])
    }
    var awayTeam by rememberSaveable(teams, presetTeams) {
        mutableStateOf(presetTeams?.second?.takeIf { it in teams } ?: teams[1])
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(stringResource(Res.string.select_teams), style = MaterialTheme.typography.headlineSmall)
        Text(
            text = stringResource(Res.string.season_note, league, season),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        TeamDropdown(
            label = stringResource(Res.string.home_team),
            selectedTeam = homeTeam,
            teams = teams,
            onTeamSelected = { homeTeam = it },
        )
        TeamDropdown(
            label = stringResource(Res.string.away_team),
            selectedTeam = awayTeam,
            teams = teams,
            onTeamSelected = { awayTeam = it },
        )
        Spacer(Modifier.height(8.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
        ) {
            Text(
                text = homeTeam,
                style = MaterialTheme.typography.titleMedium,
            )
            Spacer(Modifier.width(12.dp))
            Text(stringResource(Res.string.versus), style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.width(12.dp))
            Text(
                text = awayTeam,
                style = MaterialTheme.typography.titleMedium,
            )
        }
        val predictDescription = stringResource(Res.string.cd_predict)
        Button(
            onClick = { onPredict(homeTeam, awayTeam) },
            enabled = homeTeam != awayTeam,
            modifier = Modifier
                .fillMaxWidth()
                .semantics { contentDescription = predictDescription },
        ) {
            Text(stringResource(Res.string.action_predict))
        }
        if (homeTeam == awayTeam) {
            Text(
                text = stringResource(Res.string.teams_must_differ),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.error,
            )
        }
    }
}

/** Chooses which served league's teams to predict (ADR 012). */
@Composable
internal fun LeaguePicker(
    state: CompetitionsUiState.Success,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier) {
        TeamDropdown(
            label = stringResource(Res.string.league),
            selectedTeam = state.selected,
            teams = state.competitions.map { it.name },
            onTeamSelected = onSelect,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TeamDropdown(
    label: String,
    selectedTeam: String,
    teams: List<String>,
    onTeamSelected: (String) -> Unit,
) {
    var expanded by rememberSaveable { mutableStateOf(false) }
    val dropdownDescription = stringResource(Res.string.cd_team_dropdown, label, selectedTeam)
    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
    ) {
        OutlinedTextField(
            value = selectedTeam,
            onValueChange = {},
            readOnly = true,
            label = { Text(label) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor()
                .semantics { contentDescription = dropdownDescription },
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            teams.forEach { team ->
                DropdownMenuItem(
                    text = { Text(team) },
                    onClick = {
                        onTeamSelected(team)
                        expanded = false
                    },
                )
            }
        }
    }
}
