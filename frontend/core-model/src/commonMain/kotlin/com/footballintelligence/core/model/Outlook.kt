package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Response from GET /v2/teams/{team}/outlook: a team's projected season finish
 * and how its chances have moved (ADR 023). Each [history] point used only the
 * results known on its date.
 */
@Serializable
data class TeamOutlook(
    val competition: String,
    val season: String,
    val team: String,
    @SerialName("as_of") val asOf: String,
    @SerialName("model_version") val modelVersion: String,
    val simulations: Int,
    @SerialName("history_simulations") val historySimulations: Int,
    val projection: TeamProjection,
    val strengths: TeamStrength,
    val table: List<TeamProjection>,
    val history: List<OutlookPoint>,
)

/** One team's projected finish; chances are between 0 and 1. */
@Serializable
data class TeamProjection(
    val team: String,
    @SerialName("current_points") val currentPoints: Int,
    @SerialName("expected_points") val expectedPoints: Double,
    @SerialName("most_likely_position") val mostLikelyPosition: Int,
    @SerialName("chance_first") val chanceFirst: Double,
    @SerialName("chance_top_four") val chanceTopFour: Double,
    @SerialName("chance_bottom_three") val chanceBottomThree: Double,
)

/** The team's chances as they stood on [asOf], after [played] matches. */
@Serializable
data class OutlookPoint(
    @SerialName("as_of") val asOf: String,
    val played: Int,
    @SerialName("most_likely_position") val mostLikelyPosition: Int,
    @SerialName("chance_first") val chanceFirst: Double,
    @SerialName("chance_top_four") val chanceTopFour: Double,
    @SerialName("chance_bottom_three") val chanceBottomThree: Double,
)

/** Attack and defence as multiples of a league-average side; defence below 1 concedes fewer. */
@Serializable
data class TeamStrength(val attack: Double, val defence: Double)
