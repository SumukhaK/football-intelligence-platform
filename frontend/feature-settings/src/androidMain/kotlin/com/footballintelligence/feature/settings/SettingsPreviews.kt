package com.footballintelligence.feature.settings

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.ui.PreviewSurface

private val sampleModelInfo = ModelInfo(
    modelVersion = "20260928_123224",
    datasetVersion = "top5-2000-2026",
    trainingTimestamp = "2026-09-28T12:32:24Z",
    gitCommit = "f85e5e3a1b2c",
    metrics = mapOf("log_loss" to 0.9874, "accuracy" to 0.5231, "rps" to 0.2012),
)

@Preview
@Composable
private fun SettingsPreview() {
    PreviewSurface {
        SettingsScreen(onModelInfoClick = {}, onAboutClick = {}, onBack = {})
    }
}

@Preview(heightDp = 1000)
@Composable
private fun AboutPreview() {
    PreviewSurface {
        AboutScreen(onBack = {})
    }
}

@Composable
private fun ModelInfo(state: ModelInfoUiState) {
    PreviewSurface {
        ModelInfoScreen(uiState = state, onRetry = {}, onBack = {})
    }
}

@Preview
@Composable
private fun ModelInfoPreview() = ModelInfo(ModelInfoUiState.Success(sampleModelInfo))

@Preview
@Composable
private fun ModelInfoLoadingPreview() = ModelInfo(ModelInfoUiState.Loading)

@Preview
@Composable
private fun ModelInfoErrorPreview() = ModelInfo(ModelInfoUiState.Error("Could not load model details."))
