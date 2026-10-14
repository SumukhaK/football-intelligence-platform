package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind

/** UI state for the My Team screen: the favourite team's next match. */
sealed class MyTeamUiState {
    data object Loading : MyTeamUiState()

    /** [savedAt] is set when the server was unreachable and this is saved data. */
    data class Success(val match: NextMatch, val savedAt: String? = null) : MyTeamUiState()

    /** The schedule has no match left for [team], for example between seasons. */
    data class NoUpcomingMatch(val team: String, val savedAt: String? = null) : MyTeamUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : MyTeamUiState()
}

/**
 * The "Your next match" card. [pick] is from the favourite team's side;
 * [time] is null until the league confirms it, and [cleanSheetPercent] is null
 * when the goals model is unavailable.
 */
data class NextMatch(
    val homeTeam: String,
    val awayTeam: String,
    val day: String,
    val time: String?,
    val pick: TeamOutcome,
    val pickPercent: Int,
    val drawPossible: Boolean,
    val reasons: List<MatchReason>,
    val scorelines: List<Scoreline>,
    val cleanSheetPercent: Int?,
)

/** The predicted result for the favourite team. */
enum class TeamOutcome { WIN, DRAW, LOSS }

/** One SHAP factor behind the pick, in the server's fan-friendly wording. */
data class MatchReason(val label: String, val value: String)

/** One likely final score, home goals first. */
data class Scoreline(val home: Int, val away: Int, val percent: Int)
