package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Request body for POST /predict and POST /explain. */
@Serializable
data class PredictionRequest(
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    val features: Map<String, Double>,
)

/** Response from POST /predict. */
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
)

/** Human-readable label for a predicted outcome code (H/D/A). */
fun String.toOutcomeLabel(homeTeam: String, awayTeam: String): String = when (this) {
    "H" -> "$homeTeam Win"
    "D" -> "Draw"
    "A" -> "$awayTeam Win"
    else -> this
}
