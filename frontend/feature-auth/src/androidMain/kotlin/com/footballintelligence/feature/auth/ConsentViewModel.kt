package com.footballintelligence.feature.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.auth.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * ViewModel for the notice shown after sign-in. Asks the server whether the
 * current notice still needs accepting; the app moves on once it doesn't.
 */
class ConsentViewModel(private val repository: AuthRepository) : ViewModel() {
    private val _state = MutableStateFlow<ConsentUiState>(ConsentUiState.Loading)
    val state: StateFlow<ConsentUiState> = _state.asStateFlow()

    init {
        load()
    }

    fun retry() = load()

    fun setStoreQuestions(enabled: Boolean) =
        _state.update { if (it is ConsentUiState.Ready) it.copy(storeQuestions = enabled) else it }

    /** Accepts the notice shown; a newer one on the server is fetched and shown instead. */
    fun accept() {
        val ready = _state.value as? ConsentUiState.Ready ?: return
        if (ready.isSubmitting) return
        _state.value = ready.copy(isSubmitting = true, error = null)
        viewModelScope.launch {
            when (val result = repository.acceptConsent(ready.version, ready.storeQuestions)) {
                is NetworkResult.Success -> _state.value = ConsentUiState.Accepted
                is NetworkResult.Error ->
                    if (result.code == HTTP_FORBIDDEN) {
                        load()
                    } else {
                        _state.value = ready.copy(error = ConsentUiState.Error(result.message, result.kind))
                    }
                is NetworkResult.Loading -> Unit
            }
        }
    }

    fun signOut() {
        viewModelScope.launch { repository.signOut() }
    }

    /**
     * Offline counts as accepted so saved data still shows; the server asks
     * again (HTTP 403) on the next request if the notice really is pending.
     */
    private fun load() {
        _state.value = ConsentUiState.Loading
        viewModelScope.launch {
            _state.value = when (val result = repository.me()) {
                is NetworkResult.Success ->
                    if (result.data.consentRequired) {
                        ConsentUiState.Ready(result.data.consentText, result.data.consentVersion)
                    } else {
                        ConsentUiState.Accepted
                    }
                is NetworkResult.Error ->
                    if (result.kind == ErrorKind.OFFLINE) {
                        ConsentUiState.Accepted
                    } else {
                        ConsentUiState.Error(result.message, result.kind)
                    }
                is NetworkResult.Loading -> ConsentUiState.Loading
            }
        }
    }
}

private const val HTTP_FORBIDDEN = 403
