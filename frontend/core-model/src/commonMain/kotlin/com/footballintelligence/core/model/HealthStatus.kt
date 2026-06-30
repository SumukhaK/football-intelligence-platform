package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Mirrors GET /health response. */
@Serializable
data class HealthStatus(
    val status: String,
    @SerialName("model_loaded") val modelLoaded: Boolean,
    @SerialName("explainability_available") val explainabilityAvailable: Boolean,
    @SerialName("assistant_available") val assistantAvailable: Boolean,
    val version: String,
)
