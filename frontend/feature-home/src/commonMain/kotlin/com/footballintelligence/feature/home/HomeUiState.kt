package com.footballintelligence.feature.home

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.HealthStatus

/** UI state for the Home screen. */
sealed class HomeUiState {
    data object Loading : HomeUiState()

    /** [savedAt] is set when the server was unreachable and this is saved data. */
    data class Success(val health: HealthStatus, val savedAt: String? = null) : HomeUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : HomeUiState()
}
