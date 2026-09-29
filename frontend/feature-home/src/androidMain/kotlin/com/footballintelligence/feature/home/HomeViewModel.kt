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

/** ViewModel for [HomeScreen]. Loads backend health status on creation. */
class HomeViewModel(
    private val repository: HealthRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<HomeUiState>(HomeUiState.Loading)
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

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
        _state.value = HomeUiState.Loading
        viewModelScope.launch { _state.value = fetch() }
    }

    private suspend fun fetch(): HomeUiState =
        when (val result = repository.getHealth()) {
            is NetworkResult.Success -> HomeUiState.Success(
                result.data,
                savedAt = result.cachedAt?.let { formatSavedAt(it) },
            )
            is NetworkResult.Error -> HomeUiState.Error(result.message, result.kind)
            is NetworkResult.Loading -> HomeUiState.Loading
        }
}
