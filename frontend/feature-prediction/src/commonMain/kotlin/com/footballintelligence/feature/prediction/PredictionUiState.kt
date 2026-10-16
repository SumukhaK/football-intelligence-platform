package com.footballintelligence.feature.prediction

import com.footballintelligence.core.model.Competition
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.PredictionResult

/** UI state for the list of teams the user can pick from. */
sealed class TeamsUiState {
    data object Loading : TeamsUiState()
    data class Success(
        val season: String,
        val teams: List<String>,
        val savedAt: String? = null,
    ) : TeamsUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : TeamsUiState()
}

/** UI state for the prediction input screen. */
sealed class PredictionInputUiState {
    data object Idle : PredictionInputUiState()
    data object Loading : PredictionInputUiState()

    /** [yourTeam] is the fan's saved team when it plays in this match, so the screen can mark it. */
    data class Success(
        val result: PredictionResult,
        val savedAt: String? = null,
        val yourTeam: String? = null,
    ) : PredictionInputUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : PredictionInputUiState()
}

/** UI state for the explanation screen. */
sealed class ExplanationUiState {
    data object Idle : ExplanationUiState()
    data object Loading : ExplanationUiState()
    data class Success(val result: ExplanationResult, val savedAt: String? = null) : ExplanationUiState()
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
