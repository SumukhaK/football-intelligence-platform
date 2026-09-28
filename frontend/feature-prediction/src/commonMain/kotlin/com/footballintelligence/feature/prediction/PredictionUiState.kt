package com.footballintelligence.feature.prediction

import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.PredictionResult

/** UI state for the list of teams the user can pick from. */
sealed class TeamsUiState {
    data object Loading : TeamsUiState()
    data class Success(val season: String, val teams: List<String>) : TeamsUiState()
    data class Error(val message: String) : TeamsUiState()
}

/** UI state for the prediction input screen. */
sealed class PredictionInputUiState {
    data object Idle : PredictionInputUiState()
    data object Loading : PredictionInputUiState()
    data class Success(val result: PredictionResult) : PredictionInputUiState()
    data class Error(val message: String) : PredictionInputUiState()
}

/** UI state for the explanation screen. */
sealed class ExplanationUiState {
    data object Idle : ExplanationUiState()
    data object Loading : ExplanationUiState()
    data class Success(val result: ExplanationResult) : ExplanationUiState()
    data class Error(val message: String) : ExplanationUiState()
}
