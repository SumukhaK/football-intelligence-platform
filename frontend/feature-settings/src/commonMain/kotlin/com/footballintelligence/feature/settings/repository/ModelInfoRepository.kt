package com.footballintelligence.feature.settings.repository

import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.FootballApiService

/** Retrieves model information from the backend. */
interface ModelInfoRepository {
    suspend fun getModelInfo(): NetworkResult<ModelInfo>
}

/** Production implementation backed by [FootballApiService]. */
class DefaultModelInfoRepository(
    private val api: FootballApiService,
) : ModelInfoRepository {
    override suspend fun getModelInfo(): NetworkResult<ModelInfo> = api.getModel()
}
