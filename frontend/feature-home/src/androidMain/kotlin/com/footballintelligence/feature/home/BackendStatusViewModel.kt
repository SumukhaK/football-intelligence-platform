package com.footballintelligence.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.common.formatSavedAt
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.home.repository.HealthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** ViewModel for [BackendStatusSection]. Loads backend health status on creation. */
class BackendStatusViewModel(
    private val repository: HealthRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<BackendStatusUiState>(BackendStatusUiState.Loading)
    val state: StateFlow<BackendStatusUiState> = _state.asStateFlow()

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    init {
        loadHealth()
    }

    fun retry() {
        loadHealth()
    }

    /** Pull to refresh: reloads while the current content stays on screen. */
    fun refresh() {
        _isRefreshing.value = true
        viewModelScope.launch {
            _state.value = fetch()
            _isRefreshing.value = false
        }
    }

    private fun loadHealth() {
        _state.value = BackendStatusUiState.Loading
        viewModelScope.launch { _state.value = fetch() }
    }

    private suspend fun fetch(): BackendStatusUiState =
        when (val result = repository.getHealth()) {
            is NetworkResult.Success -> BackendStatusUiState.Success(
                result.data,
                savedAt = result.cachedAt?.let { formatSavedAt(it) },
            )
            is NetworkResult.Error -> BackendStatusUiState.Error(result.message, result.kind)
            is NetworkResult.Loading -> BackendStatusUiState.Loading
        }
}
