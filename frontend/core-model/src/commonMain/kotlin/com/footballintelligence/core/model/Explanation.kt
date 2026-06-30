package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** SHAP contribution of a single feature. */
@Serializable
data class FeatureContribution(
    @SerialName("feature_name") val featureName: String,
    @SerialName("feature_value") val featureValue: Double,
    @SerialName("shap_value") val shapValue: Double,
)

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
