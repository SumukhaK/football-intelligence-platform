package com.footballintelligence.feature.home

import com.footballintelligence.core.model.HealthStatus

/** UI state for the Home screen. */
sealed class HomeUiState {
    data object Loading : HomeUiState()
    data class Success(val health: HealthStatus) : HomeUiState()
    data class Error(val message: String) : HomeUiState()
}
