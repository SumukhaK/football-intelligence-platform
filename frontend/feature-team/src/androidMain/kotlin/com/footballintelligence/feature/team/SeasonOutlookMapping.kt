package com.footballintelligence.feature.team

import com.footballintelligence.core.model.TeamOutlook
import com.footballintelligence.core.model.TeamProjection
import kotlin.math.roundToInt

private const val PERCENT = 100

/** The section's view of an outlook: whole percentages and the team marked in the table. */
internal fun seasonOutlook(outlook: TeamOutlook): SeasonOutlook {
    val projection = outlook.projection
    return SeasonOutlook(
        team = outlook.team,
        position = projection.mostLikelyPosition,
        currentPoints = projection.currentPoints,
        expectedPoints = projection.expectedPoints.roundToInt(),
        titlePercent = percent(projection.chanceFirst),
        topFourPercent = percent(projection.chanceTopFour),
        relegationPercent = percent(projection.chanceBottomThree),
        attack = outlook.strengths.attack,
        defence = outlook.strengths.defence,
        history = outlook.history.map {
            ChancePoint(
                played = it.played,
                title = it.chanceFirst.toFloat(),
                topFour = it.chanceTopFour.toFloat(),
                relegation = it.chanceBottomThree.toFloat(),
            )
        },
        table = outlook.table.mapIndexed { index, row -> tableRow(index + 1, row, outlook.team) },
    )
}

private fun tableRow(position: Int, row: TeamProjection, favourite: String) = TableRow(
    position = position,
    team = row.team,
    currentPoints = row.currentPoints,
    expectedPoints = row.expectedPoints.roundToInt(),
    titlePercent = percent(row.chanceFirst),
    topFourPercent = percent(row.chanceTopFour),
    relegationPercent = percent(row.chanceBottomThree),
    isFavourite = row.team == favourite,
)

private fun percent(chance: Double): Int = (chance * PERCENT).roundToInt()
