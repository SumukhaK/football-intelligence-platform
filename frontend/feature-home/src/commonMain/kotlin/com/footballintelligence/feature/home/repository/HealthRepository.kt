package com.footballintelligence.feature.home.repository

import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.FootballApiService

/** Retrieves backend health status. */
interface HealthRepository {
    suspend fun getHealth(): NetworkResult<HealthStatus>
}

/** Production implementation backed by [FootballApiService]. */
class DefaultHealthRepository(
    private val api: FootballApiService,
) : HealthRepository {
    override suspend fun getHealth(): NetworkResult<HealthStatus> = api.getHealth()
}
