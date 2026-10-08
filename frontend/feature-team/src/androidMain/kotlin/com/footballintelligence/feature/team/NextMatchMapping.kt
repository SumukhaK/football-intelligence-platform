package com.footballintelligence.feature.team

import com.footballintelligence.core.common.fixtureDay
import com.footballintelligence.core.common.formatKickoff
import com.footballintelligence.core.common.formatMatchDay
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.Fixture
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.label
import com.footballintelligence.core.model.valueText
import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.util.Locale
import kotlin.math.roundToInt

// ponytail: a fixed length covers 90 minutes, half-time and stoppage time; the
// server drops the fixture the next day anyway.
private val MATCH_LENGTH: Duration = Duration.ofHours(2)
private const val REASONS_SHOWN = 3
private const val SCORELINES_SHOWN = 3
private const val PERCENT = 100

/** True once the match has been played: two hours after kick-off, or after its day without a time. */
internal fun Fixture.isOver(now: Instant, zone: ZoneId): Boolean =
    kickoff?.let { OffsetDateTime.parse(it).toInstant().plus(MATCH_LENGTH) <= now }
        ?: LocalDate.parse(matchDate).isBefore(LocalDate.ofInstant(now, zone))

/** Builds the card; [explanation] and [insights] are null when the server could not supply them. */
@Suppress("LongParameterList") // Each argument is one API answer or formatting setting.
internal fun nextMatch(
    team: String,
    fixture: Fixture,
    prediction: PredictionResult,
    explanation: ExplanationResult?,
    insights: Insights?,
    zone: ZoneId,
    locale: Locale,
): NextMatch {
    val atHome = fixture.homeTeam == team
    return NextMatch(
        homeTeam = fixture.homeTeam,
        awayTeam = fixture.awayTeam,
        day = formatMatchDay(fixtureDay(fixture.matchDate, fixture.kickoff, zone), locale),
        time = fixture.kickoff?.let { formatKickoff(it, zone, locale) },
        pick = teamOutcome(prediction.predictedResult, atHome),
        pickPercent = percent(prediction.confidence),
        drawPossible = prediction.drawPossible,
        reasons = explanation?.topPositiveFeatures.orEmpty()
            .sortedByDescending { it.shapValue }
            .take(REASONS_SHOWN)
            .map { MatchReason(it.label(), it.valueText()) },
        scorelines = insights?.topScores.orEmpty()
            .sortedByDescending { it.probability }
            .take(SCORELINES_SHOWN)
            .map { Scoreline(it.home, it.away, percent(it.probability)) },
        cleanSheetPercent = insights?.markets?.let { percent(if (atHome) it.homeCleanSheet else it.awayCleanSheet) },
    )
}

private fun teamOutcome(code: String, atHome: Boolean): TeamOutcome = when (code) {
    "D" -> TeamOutcome.DRAW
    "H" -> if (atHome) TeamOutcome.WIN else TeamOutcome.LOSS
    "A" -> if (atHome) TeamOutcome.LOSS else TeamOutcome.WIN
    else -> error("Unknown predicted result: $code")
}

private fun percent(probability: Double): Int = (probability * PERCENT).roundToInt()
