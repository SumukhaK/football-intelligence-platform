package com.footballintelligence.feature.team

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.team.repository.AccountPreferencesRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Loads account preferences before routing, with explicit retry instead of an empty fallback. */
class AccountPreferencesViewModel(private val repository: AccountPreferencesRepository) : ViewModel() {
    private val token = repository.sessionToken
    private val _state = MutableStateFlow<AccountPreferencesUiState>(AccountPreferencesUiState.Loading)
    val state = _state.asStateFlow()
    private var loading: Job? = null

    init {
        retry()
    }

    /** Repeats the server read for this screen's session. */
    fun retry() {
        val expected = token ?: return
        loading?.cancel()
        _state.value = AccountPreferencesUiState.Loading
        loading = viewModelScope.launch {
            val result = repository.load(expected)
            if (repository.sessionToken != expected) return@launch
            _state.value = when (result) {
                is NetworkResult.Success -> result.data.favourite?.let { AccountPreferencesUiState.Success(it) }
                    ?: AccountPreferencesUiState.ConfirmedEmpty
                is NetworkResult.Error -> AccountPreferencesUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> AccountPreferencesUiState.Loading
            }
        }
    }
}
