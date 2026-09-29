package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Request body for POST /predict, POST /explain and POST /insights.
 *
 * Only the teams are sent; the server computes match features from results
 * played before today (ADR 008).
 */
@Serializable
data class PredictionRequest(
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    /** League from GET /competitions; the server defaults to the Premier League. */
    val competition: String? = null,
)

/**
 * Response from POST /predict.
 *
 * [drawPossible] flags matches whose draw chance is high enough to mention; it
 * never changes [predictedResult] (ADR 011). Older servers omit it.
 */
@Serializable
data class PredictionResult(
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    @SerialName("predicted_result") val predictedResult: String,
    @SerialName("probability_home") val probabilityHome: Double,
    @SerialName("probability_draw") val probabilityDraw: Double,
    @SerialName("probability_away") val probabilityAway: Double,
    val confidence: Double,
    @SerialName("model_version") val modelVersion: String,
    @SerialName("draw_possible") val drawPossible: Boolean = false,
    /** Echoed by the server (ADR 012); empty from older servers. */
    val competition: String = "",
)
