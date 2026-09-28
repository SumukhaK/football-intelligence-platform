package com.footballintelligence.feature.home

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.ui.PreviewSurface

private val sampleHealth = HealthStatus(
    status = "ok",
    modelLoaded = true,
    explainabilityAvailable = true,
    assistantAvailable = false,
    version = "0.1.0",
)

@Composable
private fun HomePreview(state: HomeUiState) {
    PreviewSurface {
        HomeScreen(
            uiState = state,
            onPredictClick = {},
            onAssistantClick = {},
            onSettingsClick = {},
            onRetry = {},
        )
    }
}

@Preview
@Composable
private fun HomeLoadedPreview() = HomePreview(HomeUiState.Success(sampleHealth))

@Preview
@Composable
private fun HomeLoadingPreview() = HomePreview(HomeUiState.Loading)

@Preview
@Composable
private fun HomeErrorPreview() = HomePreview(HomeUiState.Error("Could not reach the server."))
