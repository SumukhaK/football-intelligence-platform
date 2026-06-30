package com.footballintelligence.feature.prediction

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.buildNeutralFeatures
import com.footballintelligence.feature.prediction.repository.PredictionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** ViewModel for the prediction and explanation flow. */
class PredictionViewModel(
    private val repository: PredictionRepository,
) : ViewModel() {

    private val _predictionState =
        MutableStateFlow<PredictionInputUiState>(PredictionInputUiState.Idle)
    val predictionState: StateFlow<PredictionInputUiState> = _predictionState.asStateFlow()

    private val _explanationState =
        MutableStateFlow<ExplanationUiState>(ExplanationUiState.Idle)
    val explanationState: StateFlow<ExplanationUiState> = _explanationState.asStateFlow()

    fun predict(homeTeam: String, awayTeam: String) {
        _predictionState.value = PredictionInputUiState.Loading
        val request = PredictionRequest(
            homeTeam = homeTeam,
            awayTeam = awayTeam,
            features = buildNeutralFeatures(),
        )
        viewModelScope.launch {
            _predictionState.value = when (val result = repository.predict(request)) {
                is NetworkResult.Success -> PredictionInputUiState.Success(result.data)
                is NetworkResult.Error -> PredictionInputUiState.Error(result.message)
                is NetworkResult.Loading -> PredictionInputUiState.Loading
            }
        }
    }

    fun explain() {
        val current = _predictionState.value
        if (current !is PredictionInputUiState.Success) return
        _explanationState.value = ExplanationUiState.Loading
        val request = PredictionRequest(
            homeTeam = current.result.homeTeam,
            awayTeam = current.result.awayTeam,
            features = buildNeutralFeatures(),
        )
        viewModelScope.launch {
            _explanationState.value = when (val result = repository.explain(request)) {
                is NetworkResult.Success -> ExplanationUiState.Success(result.data)
                is NetworkResult.Error -> ExplanationUiState.Error(result.message)
                is NetworkResult.Loading -> ExplanationUiState.Loading
            }
        }
    }

    fun resetPrediction() {
        _predictionState.value = PredictionInputUiState.Idle
        _explanationState.value = ExplanationUiState.Idle
    }
}
