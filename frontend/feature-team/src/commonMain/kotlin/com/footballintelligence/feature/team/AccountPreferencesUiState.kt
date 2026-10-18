package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.FavouriteTeam

/** Navigation remains gated until the authenticated server has answered successfully. */
sealed class AccountPreferencesUiState {
    data object Loading : AccountPreferencesUiState()
    data object ConfirmedEmpty : AccountPreferencesUiState()
    data class Success(val favourite: FavouriteTeam) : AccountPreferencesUiState()
    data class Error(val message: String, val kind: ErrorKind) : AccountPreferencesUiState()
}
