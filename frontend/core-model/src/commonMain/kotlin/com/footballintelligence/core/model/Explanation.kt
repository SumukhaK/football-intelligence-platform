package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * SHAP contribution of a single feature.
 *
 * [displayName] and [displayValue] are the server's fan-friendly wording
 * ("Arsenal team strength rating", "1618"); older servers send neither.
 */
@Serializable
data class FeatureContribution(
    @SerialName("feature_name") val featureName: String,
    @SerialName("feature_value") val featureValue: Double,
    @SerialName("shap_value") val shapValue: Double,
    @SerialName("display_name") val displayName: String = "",
    @SerialName("display_value") val displayValue: String = "",
)

/** How much one factor moved the prediction, compared with the strongest one. */
enum class Impact { BIG, MEDIUM, SMALL }

/** Fan-friendly label, falling back to the raw feature name. */
fun FeatureContribution.label(): String =
    displayName.ifBlank { featureName.replace('_', ' ') }

/** Fan-friendly value, falling back to the raw number. */
fun FeatureContribution.valueText(): String =
    displayValue.ifBlank { featureValue.toString().take(MAX_RAW_VALUE_CHARS) }

/** Impact relative to [strongest], the largest absolute SHAP value shown. */
fun FeatureContribution.impact(strongest: Double): Impact {
    if (strongest <= 0.0) return Impact.SMALL
    val share = kotlin.math.abs(shapValue) / strongest
    return when {
        share >= BIG_SHARE -> Impact.BIG
        share >= MEDIUM_SHARE -> Impact.MEDIUM
        else -> Impact.SMALL
    }
}

private const val BIG_SHARE = 0.5
private const val MEDIUM_SHARE = 0.2
private const val MAX_RAW_VALUE_CHARS = 5

/** Response from POST /explain. */
@Serializable
data class ExplanationResult(
    @SerialName("home_team") val homeTeam: String,
    @SerialName("away_team") val awayTeam: String,
    @SerialName("predicted_result") val predictedResult: String,
    @SerialName("probability_home") val probabilityHome: Double,
    @SerialName("probability_draw") val probabilityDraw: Double,
    @SerialName("probability_away") val probabilityAway: Double,
    val confidence: Double,
    @SerialName("top_positive_features") val topPositiveFeatures: List<FeatureContribution>,
    @SerialName("top_negative_features") val topNegativeFeatures: List<FeatureContribution>,
    @SerialName("all_contributions") val allContributions: List<FeatureContribution>,
    @SerialName("model_version") val modelVersion: String,
    @SerialName("feature_version") val featureVersion: String,
    @SerialName("dataset_version") val datasetVersion: String,
    @SerialName("explanation_timestamp") val explanationTimestamp: String,
)
