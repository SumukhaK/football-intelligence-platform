package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Mirrors GET /model response. */
@Serializable
data class ModelInfo(
    @SerialName("model_version") val modelVersion: String,
    @SerialName("dataset_version") val datasetVersion: String,
    @SerialName("training_timestamp") val trainingTimestamp: String,
    @SerialName("git_commit") val gitCommit: String? = null,
    val metrics: Map<String, Double> = emptyMap(),
)
