package com.footballintelligence.feature.prediction

import androidx.compose.runtime.Composable
import com.footballintelligence.feature.prediction.resources.Res
import com.footballintelligence.feature.prediction.resources.outcome_draw
import com.footballintelligence.feature.prediction.resources.outcome_team_win
import org.jetbrains.compose.resources.stringResource
import kotlin.math.roundToInt

/** Readable label for a predicted outcome code (H, D or A). */
@Composable
internal fun outcomeLabel(code: String, homeTeam: String, awayTeam: String): String = when (code) {
    "H" -> stringResource(Res.string.outcome_team_win, homeTeam)
    "D" -> stringResource(Res.string.outcome_draw)
    "A" -> stringResource(Res.string.outcome_team_win, awayTeam)
    else -> code
}

/** A probability between 0 and 1 as a whole percentage. */
internal fun percentOf(probability: Double): Int = (probability * PERCENT).roundToInt()

private const val PERCENT = 100
