package com.footballintelligence.core.network

import com.footballintelligence.core.model.ChatRequest
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.TeamsResponse
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
    suspend fun getTeams(): NetworkResult<TeamsResponse>
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
        guarded {
            client.get("$base/health").decode()
        }

    override suspend fun getModel(): NetworkResult<ModelInfo> =
        guarded {
            client.get("$base/model").decode()
        }

    override suspend fun getTeams(): NetworkResult<TeamsResponse> =
        guarded {
            client.get("$base/teams").decode()
        }

    override suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult> =
        guarded {
            client.post("$base/predict") {
                contentType(ContentType.Application.Json)
                setBody(request)
            }.decode()
        }

    override suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult> =
        guarded {
            client.post("$base/explain") {
                contentType(ContentType.Application.Json)
                setBody(request)
            }.decode()
        }

    override suspend fun chat(request: ChatRequest): NetworkResult<ChatResponse> =
        guarded {
            client.post("$base/assistant/chat") {
                contentType(ContentType.Application.Json)
                setBody(request)
            }.decode()
        }

    /**
     * Runs one API call and turns any failure into [NetworkResult.Error].
     *
     * Ktor surfaces connection, timeout, TLS and serialization problems as
     * unrelated exception types, and the UI treats every one the same way,
     * so a broad catch in this single place is deliberate.
     */
    @Suppress("TooGenericExceptionCaught")
    private suspend inline fun <T> guarded(call: () -> NetworkResult<T>): NetworkResult<T> =
        try {
            call()
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
