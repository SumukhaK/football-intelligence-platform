package com.footballintelligence.feature.home

import com.footballintelligence.core.model.ErrorKind

/** UI state for the Home screen: one league's upcoming fixtures. */
sealed class HomeUiState {
    data object Loading : HomeUiState()

    /** [savedAt] is set when the server was unreachable and this is saved data. */
    data class Success(val days: List<FixtureDay>, val savedAt: String? = null) : HomeUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : HomeUiState()
}

/** Fixtures on one day, under a heading such as "Sat 10 Oct". */
data class FixtureDay(val label: String, val fixtures: List<FixtureRow>)

/** One fixture as shown; [time] is null until the league confirms it. */
data class FixtureRow(val homeTeam: String, val awayTeam: String, val time: String?)
