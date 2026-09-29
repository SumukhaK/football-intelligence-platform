package com.footballintelligence.core.network

import com.footballintelligence.core.model.ChatRequest
import com.footballintelligence.core.model.ChatResponse
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import kotlinx.serialization.KSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.serializer

/** One saved API response and when it was fetched (ISO 8601, UTC). */
@Serializable
data class CachedResponse(val json: String, val savedAt: String)

/** Key-value storage for saved API responses. */
interface ResponseCache {
    fun read(key: String): CachedResponse?
    fun write(key: String, response: CachedResponse)
}

/**
 * Saves every successful response and replays it when the server can't be
 * reached, so the app keeps showing the last data it had.
 *
 * Only [ErrorKind.OFFLINE] falls back to the cache: a server that answers with
 * an error has something to say, and old data would hide it. Replayed results
 * carry [NetworkResult.Success.cachedAt]. Chat is never cached.
 */
class CachingFootballApiService(
    private val delegate: FootballApiService,
    private val cache: ResponseCache,
    private val clock: () -> String,
) : FootballApiService {

    private val json = Json { ignoreUnknownKeys = true }

    override suspend fun getHealth() = cached("health") { delegate.getHealth() }

    override suspend fun getModel() = cached("model") { delegate.getModel() }

    override suspend fun getCompetitions() = cached("competitions") { delegate.getCompetitions() }

    override suspend fun getTeams(competition: String) =
        cached("teams|$competition") { delegate.getTeams(competition) }

    override suspend fun predict(request: PredictionRequest) =
        cached("predict|${request.key()}") { delegate.predict(request) }

    override suspend fun explain(request: PredictionRequest) =
        cached("explain|${request.key()}") { delegate.explain(request) }

    override suspend fun getInsights(request: PredictionRequest) =
        cached("insights|${request.key()}") { delegate.getInsights(request) }

    override suspend fun chat(request: ChatRequest): NetworkResult<ChatResponse> = delegate.chat(request)

    private suspend inline fun <reified T> cached(
        key: String,
        call: () -> NetworkResult<T>,
    ): NetworkResult<T> {
        val serializer: KSerializer<T> = serializer()
        val result = call()
        if (result is NetworkResult.Success) {
            cache.write(key, CachedResponse(json.encodeToString(serializer, result.data), clock()))
        }
        val offline = result is NetworkResult.Error && result.kind == ErrorKind.OFFLINE
        return (if (offline) replay(key, serializer) else null) ?: result
    }

    private fun <T> replay(key: String, serializer: KSerializer<T>): NetworkResult<T>? {
        val saved = cache.read(key) ?: return null
        return runCatching { json.decodeFromString(serializer, saved.json) }
            .getOrNull()
            ?.let { NetworkResult.Success(it, cachedAt = saved.savedAt) }
    }
}

private fun PredictionRequest.key(): String = "${competition.orEmpty()}|$homeTeam|$awayTeam"
