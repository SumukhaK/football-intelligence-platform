package com.footballintelligence.feature.prediction

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import com.footballintelligence.core.model.toOutcomeLabel
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import kotlin.math.roundToInt

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
                title = { Text("Prediction Result") },
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
                message = "No prediction available.",
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
                    "${result.homeTeam} vs ${result.awayTeam}",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    result.predictedResult.toOutcomeLabel(result.homeTeam, result.awayTeam),
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    "Confidence: ${(result.confidence * 100).roundToInt()}%",
                    style = MaterialTheme.typography.bodyLarge,
                )
                Text(
                    "Model: ${result.modelVersion}",
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
                Text("Probabilities", style = MaterialTheme.typography.titleSmall)
                ProbabilityRow("${result.homeTeam} Win", result.probabilityHome)
                ProbabilityRow("Draw", result.probabilityDraw)
                ProbabilityRow("${result.awayTeam} Win", result.probabilityAway)
            }
        }

        Spacer(Modifier.weight(1f))

        Button(
            onClick = onExplain,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Explain This Prediction")
        }
        OutlinedButton(
            onClick = onNewPrediction,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("New Prediction")
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
                "${(probability * 100).roundToInt()}%",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
        LinearProgressIndicator(
            progress = { probability.toFloat() },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}
