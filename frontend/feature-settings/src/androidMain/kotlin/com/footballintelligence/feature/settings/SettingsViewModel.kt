package com.footballintelligence.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
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

    init {
        loadModelInfo()
    }

    fun retry() {
        loadModelInfo()
    }

    private fun loadModelInfo() {
        _modelInfoState.value = ModelInfoUiState.Loading
        viewModelScope.launch {
            _modelInfoState.value = when (val result = repository.getModelInfo()) {
                is NetworkResult.Success -> ModelInfoUiState.Success(result.data)
                is NetworkResult.Error -> ModelInfoUiState.Error(result.message)
                is NetworkResult.Loading -> ModelInfoUiState.Loading
            }
        }
    }
}
