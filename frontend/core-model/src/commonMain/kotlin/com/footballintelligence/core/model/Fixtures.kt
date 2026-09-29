package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Response from GET /v2/fixtures: a league's upcoming matches (ADR 015). */
@Serializable
data class FixturesResponse(
    val competition: String,
    val fixtures: List<Fixture>,
    @SerialName("updated_at") val updatedAt: String? = null,
)

/**
 * One upcoming match. [kickoff] is ISO 8601 with a UTC offset, or null until
 * the league confirms the time; [matchDate] is always set.
 */
@Serializable
data class Fixture(
    @SerialName("match_date") val matchDate: String,
    val kickoff: String? = null,
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    val round: String,
)

/** The leagues the app shows, in tab order (ADR 012). The first is the default. */
val SERVED_LEAGUES: List<String> =
    listOf("Premier League", "Bundesliga", "La Liga", "Serie A", "Ligue 1")
