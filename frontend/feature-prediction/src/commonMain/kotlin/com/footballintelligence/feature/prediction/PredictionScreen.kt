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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.PREMIER_LEAGUE_TEAMS
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView

/** Team selection screen for submitting a match prediction. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PredictionScreen(
    uiState: PredictionInputUiState,
    onPredict: (homeTeam: String, awayTeam: String) -> Unit,
    onNavigateToResult: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Match Prediction") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
        modifier = modifier,
    ) { padding ->
        when (uiState) {
            is PredictionInputUiState.Loading -> LoadingView(Modifier.padding(padding))
            is PredictionInputUiState.Error -> ErrorView(
                message = uiState.message,
                modifier = Modifier.padding(padding),
            )
            is PredictionInputUiState.Success -> {
                onNavigateToResult()
                LoadingView(Modifier.padding(padding))
            }
            is PredictionInputUiState.Idle -> PredictionInputContent(
                onPredict = onPredict,
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PredictionInputContent(
    onPredict: (homeTeam: String, awayTeam: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val teams = PREMIER_LEAGUE_TEAMS.map { it.name }
    var homeTeam by rememberSaveable { mutableStateOf(teams.first()) }
    var awayTeam by rememberSaveable { mutableStateOf(teams[1]) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Select Teams", style = MaterialTheme.typography.headlineSmall)
        Text(
            text = "Note: predictions use average feature values for demonstration.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        TeamDropdown(
            label = "Home Team",
            selectedTeam = homeTeam,
            teams = teams,
            onTeamSelected = { homeTeam = it },
        )
        TeamDropdown(
            label = "Away Team",
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
            Text("vs", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.width(12.dp))
            Text(
                text = awayTeam,
                style = MaterialTheme.typography.titleMedium,
            )
        }
        Button(
            onClick = { onPredict(homeTeam, awayTeam) },
            enabled = homeTeam != awayTeam,
            modifier = Modifier
                .fillMaxWidth()
                .semantics { contentDescription = "Predict match outcome" },
        ) {
            Text("Predict Match Outcome")
        }
        if (homeTeam == awayTeam) {
            Text(
                text = "Home and away teams must be different.",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.error,
            )
        }
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
                .semantics { contentDescription = "$label dropdown: $selectedTeam" },
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
