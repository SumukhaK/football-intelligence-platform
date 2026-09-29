package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Response from GET /competitions: the leagues the API serves (ADR 012). */
@Serializable
data class CompetitionsResponse(
    val default: String,
    val competitions: List<Competition>,
)

/** One served league and how current its data is. */
@Serializable
data class Competition(
    val name: String,
    val season: String,
    @SerialName("team_count") val teamCount: Int,
    @SerialName("matches_through") val matchesThrough: String,
    @SerialName("insights_available") val insightsAvailable: Boolean,
)
