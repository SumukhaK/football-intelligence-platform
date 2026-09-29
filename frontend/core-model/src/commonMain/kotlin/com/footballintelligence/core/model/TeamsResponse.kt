package com.footballintelligence.core.model

import kotlinx.serialization.Serializable

/** Response from GET /teams: the latest season's teams the API accepts. */
@Serializable
data class TeamsResponse(
    val competition: String,
    val season: String,
    val teams: List<String>,
)
