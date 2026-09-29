package com.footballintelligence.feature.prediction

import com.footballintelligence.core.model.Competition
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.PredictionResult

/** UI state for the list of teams the user can pick from. */
sealed class TeamsUiState {
    data object Loading : TeamsUiState()
    data class Success(val season: String, val teams: List<String>) : TeamsUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : TeamsUiState()
}

/** UI state for the prediction input screen. */
sealed class PredictionInputUiState {
    data object Idle : PredictionInputUiState()
    data object Loading : PredictionInputUiState()
    data class Success(val result: PredictionResult) : PredictionInputUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : PredictionInputUiState()
}

/** UI state for the explanation screen. */
sealed class ExplanationUiState {
    data object Idle : ExplanationUiState()
    data object Loading : ExplanationUiState()
    data class Success(val result: ExplanationResult) : ExplanationUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : ExplanationUiState()
}

/** UI state for the goals-model insights shown under a prediction. */
sealed class InsightsUiState {
    data object Idle : InsightsUiState()
    data object Loading : InsightsUiState()
    data class Success(val insights: Insights) : InsightsUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : InsightsUiState()
}

/** UI state for the league picker (ADR 012). */
sealed class CompetitionsUiState {
    data object Loading : CompetitionsUiState()
    data class Success(val competitions: List<Competition>, val selected: String) : CompetitionsUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : CompetitionsUiState()
}
