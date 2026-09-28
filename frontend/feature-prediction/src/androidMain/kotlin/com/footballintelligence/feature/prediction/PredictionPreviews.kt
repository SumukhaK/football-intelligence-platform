package com.footballintelligence.feature.prediction

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.FeatureContribution
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.ui.PreviewSurface

private val sampleTeams = listOf("Arsenal", "Chelsea", "Coventry City", "Liverpool")

private val samplePrediction = PredictionResult(
    homeTeam = "Arsenal",
    awayTeam = "Chelsea",
    predictedResult = "H",
    probabilityHome = 0.65,
    probabilityDraw = 0.20,
    probabilityAway = 0.15,
    confidence = 0.65,
    modelVersion = "xgb-2026.09",
)

private val strength = FeatureContribution(
    featureName = "home_elo_before",
    featureValue = 1617.7,
    shapValue = 0.34,
    displayName = "Arsenal team strength rating",
    displayValue = "1618",
)
private val homeForm = FeatureContribution(
    featureName = "home_win_pct",
    featureValue = 0.68,
    shapValue = 0.09,
    displayName = "Arsenal win rate at home",
    displayValue = "68%",
)
private val awayPosition = FeatureContribution(
    featureName = "away_league_position",
    featureValue = 3.0,
    shapValue = -0.12,
    displayName = "Chelsea league position",
    displayValue = "3rd",
)

private val sampleExplanation = ExplanationResult(
    homeTeam = "Arsenal",
    awayTeam = "Chelsea",
    predictedResult = "H",
    probabilityHome = 0.65,
    probabilityDraw = 0.20,
    probabilityAway = 0.15,
    confidence = 0.65,
    topPositiveFeatures = listOf(strength, homeForm),
    topNegativeFeatures = listOf(awayPosition),
    allContributions = listOf(strength, homeForm, awayPosition),
    modelVersion = "xgb-2026.09",
    featureVersion = "1.2.0",
    datasetVersion = "top5-2000-2026",
    explanationTimestamp = "2026-09-28T12:00:00Z",
)

@Composable
private fun TeamSelection(teams: TeamsUiState, input: PredictionInputUiState = PredictionInputUiState.Idle) {
    PreviewSurface {
        PredictionScreen(
            uiState = input,
            teamsState = teams,
            onPredict = { _, _ -> },
            onRetryTeams = {},
            onNavigateToResult = {},
            onBack = {},
        )
    }
}

@Preview
@Composable
private fun TeamSelectionPreview() = TeamSelection(TeamsUiState.Success(season = "2026/27", teams = sampleTeams))

@Preview
@Composable
private fun TeamSelectionLoadingPreview() = TeamSelection(TeamsUiState.Loading)

@Preview
@Composable
private fun TeamSelectionErrorPreview() = TeamSelection(TeamsUiState.Error("Could not load the team list."))

@Composable
private fun Result(state: PredictionInputUiState) {
    PreviewSurface {
        PredictionResultScreen(uiState = state, onExplain = {}, onNewPrediction = {}, onBack = {})
    }
}

@Preview
@Composable
private fun ResultPreview() = Result(PredictionInputUiState.Success(samplePrediction))

@Preview
@Composable
private fun ResultMissingPreview() = Result(PredictionInputUiState.Idle)

@Composable
private fun Explanation(state: ExplanationUiState) {
    PreviewSurface {
        ExplainPredictionScreen(uiState = state, onBack = {})
    }
}

@Preview
@Composable
private fun ExplanationPreview() = Explanation(ExplanationUiState.Success(sampleExplanation))

@Preview
@Composable
private fun ExplanationLoadingPreview() = Explanation(ExplanationUiState.Loading)

@Preview
@Composable
private fun ExplanationErrorPreview() = Explanation(ExplanationUiState.Error("The explainer is offline."))
