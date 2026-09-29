package com.footballintelligence.feature.prediction

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.feature.prediction.resources.Res
import com.footballintelligence.feature.prediction.resources.action_explain
import com.footballintelligence.feature.prediction.resources.action_new_prediction
import com.footballintelligence.feature.prediction.resources.confidence
import com.footballintelligence.feature.prediction.resources.fixture
import com.footballintelligence.feature.prediction.resources.model_version
import com.footballintelligence.feature.prediction.resources.no_prediction
import com.footballintelligence.feature.prediction.resources.outcome_draw
import com.footballintelligence.feature.prediction.resources.outcome_team_win
import com.footballintelligence.feature.prediction.resources.percent
import com.footballintelligence.feature.prediction.resources.probabilities
import com.footballintelligence.feature.prediction.resources.result_title
import org.jetbrains.compose.resources.stringResource

/** Displays the prediction result and offers navigation to the explanation. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PredictionResultScreen(
    uiState: PredictionInputUiState,
    onExplain: () -> Unit,
    onNewPrediction: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.result_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        modifier = modifier,
    ) { padding ->
        when (uiState) {
            is PredictionInputUiState.Loading -> LoadingView(Modifier.padding(padding))
            is PredictionInputUiState.Error -> ErrorView(
                message = uiState.message,
                onRetry = onNewPrediction,
                modifier = Modifier.padding(padding),
            )
            is PredictionInputUiState.Success -> ResultContent(
                result = uiState.result,
                onExplain = onExplain,
                onNewPrediction = onNewPrediction,
                modifier = Modifier.padding(padding),
            )
            is PredictionInputUiState.Idle -> ErrorView(
                message = stringResource(Res.string.no_prediction),
                onRetry = onNewPrediction,
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun ResultContent(
    result: PredictionResult,
    onExplain: () -> Unit,
    onNewPrediction: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer,
            ),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    stringResource(Res.string.fixture, result.homeTeam, result.awayTeam),
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    outcomeLabel(result.predictedResult, result.homeTeam, result.awayTeam),
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    stringResource(Res.string.confidence, percentOf(result.confidence)),
                    style = MaterialTheme.typography.bodyLarge,
                )
                Text(
                    stringResource(Res.string.model_version, result.modelVersion),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                )
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(stringResource(Res.string.probabilities), style = MaterialTheme.typography.titleSmall)
                ProbabilityRow(stringResource(Res.string.outcome_team_win, result.homeTeam), result.probabilityHome)
                ProbabilityRow(stringResource(Res.string.outcome_draw), result.probabilityDraw)
                ProbabilityRow(stringResource(Res.string.outcome_team_win, result.awayTeam), result.probabilityAway)
            }
        }

        Spacer(Modifier.weight(1f))

        Button(
            onClick = onExplain,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(stringResource(Res.string.action_explain))
        }
        OutlinedButton(
            onClick = onNewPrediction,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(stringResource(Res.string.action_new_prediction))
        }
    }
}

@Composable
private fun ProbabilityRow(label: String, probability: Double) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(label, style = MaterialTheme.typography.bodyMedium)
            Text(
                stringResource(Res.string.percent, percentOf(probability)),
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        LinearProgressIndicator(
            progress = { probability.toFloat() },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}
