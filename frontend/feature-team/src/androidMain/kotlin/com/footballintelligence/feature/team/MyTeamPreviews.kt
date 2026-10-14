package com.footballintelligence.feature.team

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.SERVED_LEAGUES
import com.footballintelligence.core.ui.PreviewSurface

private val sampleMatch = NextMatch(
    homeTeam = "Everton",
    awayTeam = "Arsenal",
    day = "Sun 18 Oct",
    time = "16:30",
    pick = TeamOutcome.WIN,
    pickPercent = 52,
    drawPossible = true,
    reasons = listOf(
        MatchReason("Arsenal team strength rating", "1618"),
        MatchReason("Arsenal wins in last 10", "7 of 10"),
        MatchReason("Everton league position", "15th"),
    ),
    scorelines = listOf(Scoreline(0, 1, 14), Scoreline(1, 1, 12), Scoreline(0, 2, 11)),
    cleanSheetPercent = 31,
)

@Composable
private fun MyTeam(state: MyTeamUiState, outlook: SeasonOutlookUiState = SeasonOutlookUiState.Success(sampleOutlook)) =
    PreviewSurface { MyTeamScreen(uiState = state, outlookState = outlook, onRetry = {}, onOpenTable = {}) }

@Preview
@Composable
private fun MyTeamPreview() = MyTeam(MyTeamUiState.Success(sampleMatch))

@Preview
@Composable
private fun MyTeamOfflinePreview() =
    MyTeam(MyTeamUiState.Success(sampleMatch.copy(time = null, reasons = emptyList()), savedAt = "9 Oct, 09:00"))

@Preview
@Composable
private fun MyTeamNoMatchPreview() = MyTeam(MyTeamUiState.NoUpcomingMatch("Arsenal"))

@Preview
@Composable
private fun MyTeamLoadingPreview() = MyTeam(MyTeamUiState.Loading)

@Preview
@Composable
private fun MyTeamErrorPreview() = MyTeam(MyTeamUiState.Error("Could not reach the server."))

private val serieA = listOf("Inter", "Milan", "Napoli", "Roma")

@Composable
private fun Picker(step: PickerStep, isOnboarding: Boolean = true) = PreviewSurface {
    TeamPickerScreen(
        step = step,
        isOnboarding = isOnboarding,
        onSelectLeague = {},
        onSelectTeam = {},
        onBackToLeagues = {},
        onRetry = {},
        onLeave = {},
    )
}

@Preview
@Composable
private fun PickerLeaguesPreview() = Picker(PickerStep.League(SERVED_LEAGUES))

@Preview
@Composable
private fun PickerLeaguesCheckedPreview() =
    Picker(PickerStep.League(SERVED_LEAGUES, selected = "Serie A"), isOnboarding = false)

@Preview
@Composable
private fun PickerTeamsPreview() =
    Picker(
        PickerStep.Team("Serie A", TeamsUiState.Success(serieA), selected = "Inter"),
        isOnboarding = false,
    )

@Preview
@Composable
private fun PickerTeamsErrorPreview() = Picker(PickerStep.Team("Serie A", TeamsUiState.Error("Offline")))

@Preview
@Composable
private fun SettingsSectionPreview() = PreviewSurface {
    MyTeamSettingsSection(FavouriteTeam("Premier League", "Arsenal"), onChange = {})
}

@Preview
@Composable
private fun NextMatchCardPreview() = PreviewSurface { NextMatchCard(sampleMatch) }

private val sampleOutlook = SeasonOutlook(
    team = "Arsenal",
    position = 2,
    currentPoints = 13,
    expectedPoints = 75,
    titlePercent = 23,
    topFourPercent = 79,
    relegationPercent = 0,
    attack = 1.23,
    defence = 0.69,
    history = listOf(
        ChancePoint(0, 0.18f, 0.71f, 0.01f),
        ChancePoint(1, 0.21f, 0.74f, 0.01f),
        ChancePoint(3, 0.17f, 0.69f, 0.0f),
        ChancePoint(5, 0.23f, 0.79f, 0.0f),
    ),
    table = listOf(
        TableRow(1, "Man City", 15, 80, 51, 95, 0, isFavourite = false),
        TableRow(2, "Arsenal", 13, 75, 23, 79, 0, isFavourite = true),
        TableRow(3, "Liverpool", 12, 71, 14, 66, 0, isFavourite = false),
    ),
)

@Preview(heightDp = 1400)
@Composable
private fun MyTeamWithOutlookPreview() = MyTeam(MyTeamUiState.Success(sampleMatch))

@Composable
private fun Outlook(state: SeasonOutlookUiState) = PreviewSurface {
    SeasonOutlookSection(state, onOpenTable = {}, onRetry = {})
}

@Preview(heightDp = 700)
@Composable
private fun SeasonOutlookPreview() = Outlook(SeasonOutlookUiState.Success(sampleOutlook))

@Preview
@Composable
private fun SeasonOutlookLoadingPreview() = Outlook(SeasonOutlookUiState.Loading)

@Preview
@Composable
private fun SeasonOutlookErrorPreview() = Outlook(SeasonOutlookUiState.Error("Season outlook not available"))

@Preview
@Composable
private fun ChanceChartPreview() = PreviewSurface { ChanceChart(sampleOutlook.history) }

@Preview
@Composable
private fun ProjectedTablePreview() = PreviewSurface {
    ProjectedTableScreen(
        SeasonOutlookUiState.Success(sampleOutlook, savedAt = "8 Oct, 09:00"),
        onRetry = {},
        onBack = {},
    )
}
