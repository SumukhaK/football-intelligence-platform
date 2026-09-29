package com.footballintelligence.feature.prediction

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.Competition
import com.footballintelligence.core.model.ExpectedGoals
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.FeatureContribution
import com.footballintelligence.core.model.GoalMarkets
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.OutcomeProbabilities
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.ScoreProbability
import com.footballintelligence.core.ui.PreviewSurface

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

private val sampleLeagues = CompetitionsUiState.Success(
    competitions = listOf(
        Competition("Premier League", "2026/27", 20, "2026-09-20", true),
        Competition("Bundesliga", "2026/27", 18, "2026-09-20", true),
    ),
    selected = "Bundesliga",
)

@Composable
private fun TeamSelection(teams: TeamsUiState, input: PredictionInputUiState = PredictionInputUiState.Idle) {
    PreviewSurface {
        PredictionScreen(
            uiState = input,
            competitionsState = sampleLeagues,
            teamsState = teams,
            onSelectCompetition = {},
            onPredict = { _, _ -> },
            onRetryTeams = {},
            onNavigateToResult = {},
            onBack = {},
        )
    }
}

@Preview
@Composable
private fun TeamSelectionPreview() = TeamSelection(
    TeamsUiState.Success(season = "2026/27", teams = listOf("Bayern Munich", "Dortmund", "Leipzig")),
)

@Preview
@Composable
private fun LeaguePickerPreview() = PreviewSurface { LeaguePicker(state = sampleLeagues, onSelect = {}) }

@Preview
@Composable
private fun TeamSelectionLoadingPreview() = TeamSelection(TeamsUiState.Loading)

@Preview
@Composable
private fun TeamSelectionErrorPreview() = TeamSelection(TeamsUiState.Error("Could not load the team list."))

private val sampleInsights = Insights(
    homeTeam = "Arsenal",
    awayTeam = "Chelsea",
    modelVersion = "dc-2026-09-28",
    fittedBefore = "2026-09-28",
    expectedGoals = ExpectedGoals(home = 1.95, away = 0.98),
    topScores = listOf(
        ScoreProbability(1, 1, 0.112),
        ScoreProbability(2, 0, 0.102),
        ScoreProbability(2, 1, 0.099),
        ScoreProbability(1, 0, 0.095),
        ScoreProbability(3, 0, 0.066),
    ),
    markets = GoalMarkets(0.544, 0.799, 0.560, 0.336, 0.376, 0.143),
    outcome = OutcomeProbabilities(home = 0.590, draw = 0.235, away = 0.175),
    reasons = listOf(
        "Arsenal concede 31% fewer goals than an average side in this league",
        "Arsenal score 23% more goals than an average side in this league",
    ),
)

@Composable
private fun Result(
    state: PredictionInputUiState,
    insights: InsightsUiState = InsightsUiState.Success(sampleInsights),
) {
    PreviewSurface {
        PredictionResultScreen(
            uiState = state,
            insightsState = insights,
            onExplain = {},
            onNewPrediction = {},
            onBack = {},
        )
    }
}

@Preview(heightDp = 1600)
@Composable
private fun ResultWithInsightsPreview() = Result(PredictionInputUiState.Success(samplePrediction))

@Preview
@Composable
private fun InsightsLoadingPreview() = PreviewSurface { InsightsSection(InsightsUiState.Loading) }

@Preview
@Composable
private fun InsightsErrorPreview() = PreviewSurface { InsightsSection(InsightsUiState.Error("HTTP 503")) }

@Preview
@Composable
private fun ResultPreview() = Result(PredictionInputUiState.Success(samplePrediction), InsightsUiState.Idle)

@Preview
@Composable
private fun ResultDrawPossiblePreview() = Result(
    PredictionInputUiState.Success(
        samplePrediction.copy(
            homeTeam = "Everton",
            awayTeam = "Brentford",
            probabilityHome = 0.39,
            probabilityDraw = 0.30,
            probabilityAway = 0.31,
            confidence = 0.39,
            drawPossible = true,
        ),
    ),
)

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
