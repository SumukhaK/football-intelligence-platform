package com.footballintelligence.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.common.formatSavedAt
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.settings.repository.ModelInfoRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** ViewModel for the model information screen. */
class SettingsViewModel(
    private val repository: ModelInfoRepository,
) : ViewModel() {

    private val _modelInfoState =
        MutableStateFlow<ModelInfoUiState>(ModelInfoUiState.Loading)
    val modelInfoState: StateFlow<ModelInfoUiState> = _modelInfoState.asStateFlow()

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    init {
        loadModelInfo()
    }

    fun retry() {
        loadModelInfo()
    }

    /** Pull to refresh: reloads while the current content stays on screen. */
    fun refresh() {
        _isRefreshing.value = true
        viewModelScope.launch {
            _modelInfoState.value = fetch()
            _isRefreshing.value = false
        }
    }

    private fun loadModelInfo() {
        _modelInfoState.value = ModelInfoUiState.Loading
        viewModelScope.launch { _modelInfoState.value = fetch() }
    }

    private suspend fun fetch(): ModelInfoUiState =
        when (val result = repository.getModelInfo()) {
            is NetworkResult.Success -> ModelInfoUiState.Success(
                result.data,
                savedAt = result.cachedAt?.let { formatSavedAt(it) },
            )
            is NetworkResult.Error -> ModelInfoUiState.Error(result.message, result.kind)
            is NetworkResult.Loading -> ModelInfoUiState.Loading
        }
}
