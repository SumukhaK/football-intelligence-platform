package com.footballintelligence.feature.settings

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.ModelInfo

/** UI state for the model information screen. */
sealed class ModelInfoUiState {
    data object Loading : ModelInfoUiState()
    data class Success(val info: ModelInfo, val savedAt: String? = null) : ModelInfoUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : ModelInfoUiState()
}
