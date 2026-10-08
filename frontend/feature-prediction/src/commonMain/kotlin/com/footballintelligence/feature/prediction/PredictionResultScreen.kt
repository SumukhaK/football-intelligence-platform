package com.footballintelligence.feature.prediction

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.OfflineBanner
import com.footballintelligence.core.ui.RefreshableContent
import com.footballintelligence.core.ui.TeamCrest
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.prediction.resources.Res
import com.footballintelligence.feature.prediction.resources.action_explain
import com.footballintelligence.feature.prediction.resources.action_new_prediction
import com.footballintelligence.feature.prediction.resources.confidence
import com.footballintelligence.feature.prediction.resources.draw_possible
import com.footballintelligence.feature.prediction.resources.draw_possible_detail
import com.footballintelligence.feature.prediction.resources.fixture
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
    insightsState: InsightsUiState,
    onExplain: () -> Unit,
    onNewPrediction: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    isRefreshing: Boolean = false,
    onRefresh: () -> Unit = {},
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.result_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        bottomBar = {
            if (uiState is PredictionInputUiState.Success) {
                ResultActions(onExplain = onExplain, onNewPrediction = onNewPrediction)
            }
        },
        modifier = modifier,
    ) { padding ->
        when (uiState) {
            is PredictionInputUiState.Loading -> LoadingView(Modifier.padding(padding))
            is PredictionInputUiState.Error -> ErrorView(
                message = errorMessage(uiState.kind, uiState.message),
                onRetry = onNewPrediction,
                modifier = Modifier.padding(padding),
            )
            is PredictionInputUiState.Success -> RefreshableContent(
                isRefreshing = isRefreshing,
                onRefresh = onRefresh,
                modifier = Modifier.padding(padding),
            ) {
                Column {
                    OfflineBanner(uiState.savedAt)
                    ResultContent(result = uiState.result, insightsState = insightsState)
                }
            }
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
    insightsState: InsightsUiState,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.secondaryContainer,
            ),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                if (result.competition.isNotBlank()) {
                    Text(result.competition, style = MaterialTheme.typography.labelMedium)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                    TeamCrest(result.homeTeam, size = 48.dp)
                    TeamCrest(result.awayTeam, size = 48.dp)
                }
                Text(
                    stringResource(Res.string.fixture, result.homeTeam, result.awayTeam),
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    outcomeLabel(result.predictedResult, result.homeTeam, result.awayTeam),
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.primary,
                )
                if (result.drawPossible) {
                    DrawPossibleTag()
                }
                Text(
                    stringResource(Res.string.confidence, percentOf(result.confidence)),
                    style = MaterialTheme.typography.bodyLarge,
                )
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text(stringResource(Res.string.probabilities), style = MaterialTheme.typography.titleSmall)
                ProbabilityRow(stringResource(Res.string.outcome_team_win, result.homeTeam), result.probabilityHome)
                ProbabilityRow(stringResource(Res.string.outcome_draw), result.probabilityDraw)
                ProbabilityRow(stringResource(Res.string.outcome_team_win, result.awayTeam), result.probabilityAway)
            }
        }

        InsightsSection(state = insightsState)
    }
}

/** Explain and New prediction, pinned to the bottom of the screen. */
@Composable
private fun ResultActions(onExplain: () -> Unit, onNewPrediction: () -> Unit) {
    Surface(tonalElevation = 3.dp) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            OutlinedButton(onClick = onNewPrediction, modifier = Modifier.weight(1f)) {
                Text(stringResource(Res.string.action_new_prediction))
            }
            Button(onClick = onExplain, modifier = Modifier.weight(1f)) {
                Text(stringResource(Res.string.action_explain))
            }
        }
    }
}

@Composable
private fun ProbabilityRow(label: String, probability: Double) {
    val fill = remember { Animatable(0f) }
    LaunchedEffect(probability) {
        fill.animateTo(probability.toFloat(), tween(durationMillis = FILL_MILLIS))
    }
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(label, style = MaterialTheme.typography.bodyMedium)
            Text(
                stringResource(Res.string.percent, percentOf(probability)),
                style = MaterialTheme.typography.titleSmall,
            )
        }
        LinearProgressIndicator(
            progress = { fill.value },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}

@Composable
private fun DrawPossibleTag() {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = stringResource(Res.string.draw_possible),
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onTertiaryContainer,
            modifier = Modifier
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.tertiaryContainer)
                .padding(horizontal = 12.dp, vertical = 4.dp),
        )
        Text(
            text = stringResource(Res.string.draw_possible_detail),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onPrimaryContainer,
        )
    }
}

private const val FILL_MILLIS = 700
