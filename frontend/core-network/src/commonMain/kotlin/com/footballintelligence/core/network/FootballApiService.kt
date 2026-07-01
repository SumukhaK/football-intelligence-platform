package com.footballintelligence.core.network

import com.footballintelligence.core.model.ChatRequest
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.HttpResponse
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.http.isSuccess

/** Typed API service for the Football Intelligence FastAPI backend. */
interface FootballApiService {
    suspend fun getHealth(): NetworkResult<HealthStatus>
    suspend fun getModel(): NetworkResult<ModelInfo>
    suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult>
    suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult>
    suspend fun chat(request: ChatRequest): NetworkResult<ChatResponse>
}

/** Ktor-backed implementation of [FootballApiService]. */
class KtorFootballApiService(
    private val client: HttpClient,
    private val config: NetworkConfig,
) : FootballApiService {

    private val base get() = config.baseUrl

    override suspend fun getHealth(): NetworkResult<HealthStatus> =
        try {
            client.get("$base/health").decode()
        } catch (e: Exception) {
            NetworkResult.Error(message = e.message ?: "Unknown network error")
        }

    override suspend fun getModel(): NetworkResult<ModelInfo> =
        try {
            client.get("$base/model").decode()
        } catch (e: Exception) {
            NetworkResult.Error(message = e.message ?: "Unknown network error")
        }

    override suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult> =
        try {
            client.post("$base/predict") {
                contentType(ContentType.Application.Json)
                setBody(request)
            }.decode()
        } catch (e: Exception) {
            NetworkResult.Error(message = e.message ?: "Unknown network error")
        }

    override suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult> =
        try {
            client.post("$base/explain") {
                contentType(ContentType.Application.Json)
                setBody(request)
            }.decode()
        } catch (e: Exception) {
            NetworkResult.Error(message = e.message ?: "Unknown network error")
        }

    override suspend fun chat(request: ChatRequest): NetworkResult<ChatResponse> =
        try {
            client.post("$base/assistant/chat") {
                contentType(ContentType.Application.Json)
                setBody(request)
            }.decode()
        } catch (e: Exception) {
            NetworkResult.Error(message = e.message ?: "Unknown network error")
        }

    private suspend inline fun <reified T> HttpResponse.decode(): NetworkResult<T> =
        if (status.isSuccess()) {
            NetworkResult.Success(body())
        } else {
            NetworkResult.Error(
                message = "HTTP ${status.value}: ${status.description}",
                code = status.value,
            )
        }
}
