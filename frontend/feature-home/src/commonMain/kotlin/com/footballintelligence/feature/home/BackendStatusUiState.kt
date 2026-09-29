package com.footballintelligence.feature.home

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.HealthStatus

/** UI state for the backend status section. */
sealed class BackendStatusUiState {
    data object Loading : BackendStatusUiState()

    /** [savedAt] is set when the server was unreachable and this is saved data. */
    data class Success(val health: HealthStatus, val savedAt: String? = null) : BackendStatusUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : BackendStatusUiState()
}
