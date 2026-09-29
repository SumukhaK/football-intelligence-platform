package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Response from POST /insights: the goals model's view of a fixture (ADR 009).
 *
 * The headline pick still comes from [PredictionResult]; [outcome] is the goals
 * model's own view and is shown for reference only.
 */
@Serializable
data class Insights(
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    @SerialName("model_version") val modelVersion: String,
    @SerialName("fitted_before") val fittedBefore: String,
    @SerialName("expected_goals") val expectedGoals: ExpectedGoals,
    @SerialName("top_scores") val topScores: List<ScoreProbability>,
    val markets: GoalMarkets,
    val outcome: OutcomeProbabilities,
    val reasons: List<String>,
)

/** Mean goals for each side. */
@Serializable
data class ExpectedGoals(val home: Double, val away: Double)

/** One scoreline and its probability. */
@Serializable
data class ScoreProbability(val home: Int, val away: Int, val probability: Double)

/** Probabilities of common goal events. */
@Serializable
data class GoalMarkets(
    val btts: Double,
    @SerialName("over_1_5") val over15: Double,
    @SerialName("over_2_5") val over25: Double,
    @SerialName("over_3_5") val over35: Double,
    @SerialName("home_clean_sheet") val homeCleanSheet: Double,
    @SerialName("away_clean_sheet") val awayCleanSheet: Double,
)

/** Home, draw and away probabilities. */
@Serializable
data class OutcomeProbabilities(val home: Double, val draw: Double, val away: Double)
