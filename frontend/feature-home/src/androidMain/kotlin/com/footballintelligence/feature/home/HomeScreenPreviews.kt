package com.footballintelligence.feature.home

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.SERVED_LEAGUES
import com.footballintelligence.core.ui.PreviewSurface

private val sampleDays = listOf(
    FixtureDay(
        "Sat 10 Oct",
        listOf(
            FixtureRow("Arsenal", "Leeds", "12:30"),
            FixtureRow("Aston Villa", "Brentford", "15:00"),
            FixtureRow("Man City", "Fulham", null),
        ),
    ),
    FixtureDay("Sun 11 Oct", listOf(FixtureRow("Everton", "Chelsea", "16:30"))),
)

private val sampleHealth = HealthStatus(
    status = "ok",
    modelLoaded = true,
    explainabilityAvailable = true,
    assistantAvailable = false,
    version = "2.0.0",
)

@Composable
private fun HomePreview(state: HomeUiState) {
    PreviewSurface {
        HomeScreen(
            uiState = state,
            leagues = SERVED_LEAGUES,
            selectedLeague = SERVED_LEAGUES.first(),
            onSelectLeague = {},
            onRetry = {},
        )
    }
}

@Preview
@Composable
private fun HomeLoadedPreview() = HomePreview(HomeUiState.Success(sampleDays))

@Preview
@Composable
private fun HomeOfflinePreview() = HomePreview(HomeUiState.Success(sampleDays, savedAt = "29 Sep, 12:31"))

@Preview
@Composable
private fun HomeEmptyPreview() = HomePreview(HomeUiState.Success(emptyList()))

@Preview
@Composable
private fun HomeLoadingPreview() = HomePreview(HomeUiState.Loading)

@Preview
@Composable
private fun HomeErrorPreview() = HomePreview(HomeUiState.Error("Could not reach the server."))

@Preview
@Composable
private fun BackendStatusPreview() = PreviewSurface {
    BackendStatusSection(BackendStatusUiState.Success(sampleHealth), onRetry = {})
}
