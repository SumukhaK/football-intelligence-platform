package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind

/** Why the picker was opened, which decides its first step and what saving does. */
enum class PickerFlow {
    /** First launch: league, then team, then into the app. */
    ONBOARDING,

    /** From Settings, starting at the league step. */
    CHANGE_LEAGUE,

    /** From Settings, starting at the team step of the saved league. */
    CHANGE_TEAM,
}

/** What the app does once a team is saved. */
enum class PickerOutcome {
    /** Leave onboarding for the main screens. */
    ONBOARDING_FINISHED,

    /** Restart the app so every screen loads the new team's data. */
    RELAUNCH,
}

/** The picker's current step: choosing a league, or a team in that league. */
sealed class PickerStep {
    data class League(val leagues: List<String>) : PickerStep()
    data class Team(val league: String, val teams: TeamsUiState) : PickerStep()
}

/** One league's teams for the team step. */
sealed class TeamsUiState {
    data object Loading : TeamsUiState()
    data class Success(val teams: List<String>) : TeamsUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : TeamsUiState()
}
