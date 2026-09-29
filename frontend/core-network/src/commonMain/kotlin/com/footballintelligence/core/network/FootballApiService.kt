package com.footballintelligence.core.network

import com.footballintelligence.core.model.ChatRequest
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.CompetitionsResponse
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.TeamsResponse
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.get
import io.ktor.client.request.parameter
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.HttpResponse
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.http.isSuccess
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException

/** Typed API service for the Football Intelligence FastAPI backend. */
interface FootballApiService {
    suspend fun getHealth(): NetworkResult<HealthStatus>
    suspend fun getModel(): NetworkResult<ModelInfo>
    suspend fun getCompetitions(): NetworkResult<CompetitionsResponse>
    suspend fun getTeams(competition: String): NetworkResult<TeamsResponse>
    suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult>
    suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult>
    suspend fun getInsights(request: PredictionRequest): NetworkResult<Insights>
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

    override suspend fun getCompetitions(): NetworkResult<CompetitionsResponse> =
        guarded {
            client.get("$base/competitions").decode()
        }

    override suspend fun getTeams(competition: String): NetworkResult<TeamsResponse> =
        guarded {
            client.get("$base/teams") { parameter("competition", competition) }.decode()
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

    override suspend fun getInsights(request: PredictionRequest): NetworkResult<Insights> =
        guarded {
            client.post("$base/insights") {
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
}

/**
 * Runs one API call and turns any failure into [NetworkResult.Error].
 *
 * Ktor surfaces connection, timeout and TLS problems as unrelated exception
 * types, and the UI treats every one as "can't reach the server", so a broad
 * catch in this single place is deliberate. A malformed response is reported
 * separately as an unexpected error.
 */
@Suppress("TooGenericExceptionCaught")
private suspend inline fun <T> guarded(call: () -> NetworkResult<T>): NetworkResult<T> =
    try {
        call()
    } catch (e: SerializationException) {
        NetworkResult.Error(message = e.message ?: "Malformed response", kind = ErrorKind.UNKNOWN)
    } catch (e: Exception) {
        NetworkResult.Error(message = e.message ?: "Unknown network error", kind = ErrorKind.OFFLINE)
    }

private suspend inline fun <reified T> HttpResponse.decode(): NetworkResult<T> =
    if (status.isSuccess()) {
        NetworkResult.Success(body())
    } else {
        NetworkResult.Error(
            message = serverDetail() ?: "HTTP ${status.value}: ${status.description}",
            code = status.value,
            kind = errorKindFor(status.value),
        )
    }

/** The `detail` of the backend's structured error body, if it has one. */
private suspend fun HttpResponse.serverDetail(): String? =
    runCatching { body<ErrorBody>() }.getOrNull()?.detail?.takeIf { it.isNotBlank() }

/** The backend's structured error body: `{"error": ..., "detail": ...}`. */
@Serializable
private data class ErrorBody(val error: String = "", val detail: String = "")

/** Classifies an HTTP error status for the UI. */
internal fun errorKindFor(status: Int): ErrorKind = when (status) {
    in SERVER_BUSY_CODES -> ErrorKind.SERVER_BUSY
    in CLIENT_ERROR_CODES -> ErrorKind.REJECTED
    else -> ErrorKind.UNKNOWN
}

private val SERVER_BUSY_CODES = 502..504
private val CLIENT_ERROR_CODES = 400..499
