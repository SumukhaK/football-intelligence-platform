package com.footballintelligence.feature.settings

import com.footballintelligence.core.model.ModelInfo

/** UI state for the model information screen. */
sealed class ModelInfoUiState {
    data object Loading : ModelInfoUiState()
    data class Success(val info: ModelInfo) : ModelInfoUiState()
    data class Error(val message: String) : ModelInfoUiState()
}
