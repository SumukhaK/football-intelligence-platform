package com.footballintelligence.feature.auth

import com.footballintelligence.core.model.ErrorKind

/** UI state for the notice shown after sign-in. */
sealed class ConsentUiState {
    data object Loading : ConsentUiState()

    /**
     * The notice to accept: [text] and [version] come from the server.
     * [error] is set when accepting failed; null means no error to show.
     */
    data class Ready(
        val text: String,
        val version: Int,
        val storeQuestions: Boolean = false,
        val isSubmitting: Boolean = false,
        val error: Error? = null,
    ) : ConsentUiState()

    /** Nothing (more) to accept: the app moves on. */
    data object Accepted : ConsentUiState()

    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : ConsentUiState()
}
