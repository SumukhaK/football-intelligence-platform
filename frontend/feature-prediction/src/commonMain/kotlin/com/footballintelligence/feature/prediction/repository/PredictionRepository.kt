package com.footballintelligence.feature.prediction.repository

import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.TeamsResponse
import com.footballintelligence.core.network.FootballApiService

/** Loads selectable teams and submits prediction and explanation requests. */
interface PredictionRepository {
    suspend fun teams(): NetworkResult<TeamsResponse>
    suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult>
    suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult>
    suspend fun insights(request: PredictionRequest): NetworkResult<Insights>
}

/** Production implementation backed by [FootballApiService]. */
class DefaultPredictionRepository(
    private val api: FootballApiService,
) : PredictionRepository {
    override suspend fun teams(): NetworkResult<TeamsResponse> = api.getTeams()

    override suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult> =
        api.predict(request)

    override suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult> =
        api.explain(request)

    override suspend fun insights(request: PredictionRequest): NetworkResult<Insights> =
        api.getInsights(request)
}
