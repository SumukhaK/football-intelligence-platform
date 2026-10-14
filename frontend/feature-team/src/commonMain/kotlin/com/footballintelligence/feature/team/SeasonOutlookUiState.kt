package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind

/** UI state for the Season outlook section and the projected table. */
sealed class SeasonOutlookUiState {
    data object Loading : SeasonOutlookUiState()

    /** [savedAt] is set when the server was unreachable and this is saved data. */
    data class Success(val outlook: SeasonOutlook, val savedAt: String? = null) : SeasonOutlookUiState()
    data class Error(val message: String, val kind: ErrorKind = ErrorKind.UNKNOWN) : SeasonOutlookUiState()
}

/**
 * The favourite team's projected finish. Chances are whole percentages;
 * [attack] and [defence] are multiples of a league-average side, and a
 * defence below 1 concedes fewer goals than average.
 */
data class SeasonOutlook(
    val team: String,
    val position: Int,
    val currentPoints: Int,
    val expectedPoints: Int,
    val titlePercent: Int,
    val topFourPercent: Int,
    val relegationPercent: Int,
    val attack: Double,
    val defence: Double,
    val history: List<ChancePoint>,
    val table: List<TableRow>,
)

/** The three chances after [played] matches, each between 0 and 1, for the chart. */
data class ChancePoint(val played: Int, val title: Float, val topFour: Float, val relegation: Float)

/** One row of the projected table; [isFavourite] marks the fan's team. */
data class TableRow(
    val position: Int,
    val team: String,
    val currentPoints: Int,
    val expectedPoints: Int,
    val titlePercent: Int,
    val topFourPercent: Int,
    val relegationPercent: Int,
    val isFavourite: Boolean,
)
