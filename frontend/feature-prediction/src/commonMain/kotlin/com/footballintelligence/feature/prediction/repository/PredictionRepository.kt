package com.footballintelligence.feature.prediction.repository

import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.network.FootballApiService

/** Submits match prediction and explanation requests to the backend. */
interface PredictionRepository {
    suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult>
    suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult>
}

/** Production implementation backed by [FootballApiService]. */
class DefaultPredictionRepository(
    private val api: FootballApiService,
) : PredictionRepository {
    override suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult> =
        api.predict(request)

    override suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult> =
        api.explain(request)
}
