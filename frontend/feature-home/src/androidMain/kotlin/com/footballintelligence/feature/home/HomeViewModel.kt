package com.footballintelligence.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
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

    init {
        loadHealth()
    }

    fun retry() {
        loadHealth()
    }

    private fun loadHealth() {
        _state.value = HomeUiState.Loading
        viewModelScope.launch {
            _state.value = when (val result = repository.getHealth()) {
                is NetworkResult.Success -> HomeUiState.Success(result.data)
                is NetworkResult.Error -> HomeUiState.Error(result.message)
                is NetworkResult.Loading -> HomeUiState.Loading
            }
        }
    }
}
