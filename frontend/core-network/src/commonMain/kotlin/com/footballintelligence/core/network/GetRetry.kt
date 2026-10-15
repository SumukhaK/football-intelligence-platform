package com.footballintelligence.core.network

import io.ktor.client.HttpClientConfig
import io.ktor.client.plugins.HttpRequestRetry
import io.ktor.client.statement.HttpResponse
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpMethod
import io.ktor.http.contentType
import kotlin.math.min
import kotlin.random.Random

/** Rate limited, or the server or its proxy briefly unavailable. */
private val RETRYABLE_STATUSES = setOf(429, 502, 503, 504)
private const val MAX_RETRIES = 2
private const val BASE_WAIT_MS = 500L
private const val MS_PER_SECOND = 1_000L

// 500 ms doubled four times already passes the cap.
private const val MAX_DOUBLINGS = 4

/** The longest the app waits before a retry, however long the server asks for. */
internal const val MAX_WAIT_MS = 8_000L

/**
 * Whether a response may be retried. GETs change nothing on the server, so
 * they retry on any of [RETRYABLE_STATUSES]. A POST could send a chat message
 * or a sign-in twice, so it retries only on a 429 [fromPlatform]: Cloud Run's
 * own "no instance available" page while it scales from zero, when the
 * request never reached the app. A Retry-After longer than [MAX_WAIT_MS] is
 * answered at once instead.
 */
internal fun isRetryable(method: HttpMethod, status: Int, retryAfterSeconds: Long?, fromPlatform: Boolean): Boolean {
    val allowed = when (method) {
        HttpMethod.Get -> status in RETRYABLE_STATUSES
        else -> status == HTTP_TOO_MANY_REQUESTS && fromPlatform
    }
    return allowed && (retryAfterSeconds == null || retryAfterSeconds * MS_PER_SECOND <= MAX_WAIT_MS)
}

private const val HTTP_TOO_MANY_REQUESTS = 429

/** Wait before retry number [retry]: Retry-After, else capped exponential backoff with full jitter. */
internal fun retryDelayMs(retry: Int, retryAfterSeconds: Long?, random: Random): Long {
    if (retryAfterSeconds != null) return retryAfterSeconds * MS_PER_SECOND
    val ceiling = min(MAX_WAIT_MS, BASE_WAIT_MS shl min(retry, MAX_DOUBLINGS))
    return random.nextLong(0, ceiling + 1)
}

/**
 * Retries idempotent GETs that hit a 429, 502, 503 or 504, and any request
 * Cloud Run turned away while scaling up, up to twice.
 * Connection failures are not retried, so an unreachable server still falls
 * back to saved data within the connect timeout.
 */
fun HttpClientConfig<*>.installGetRetry(random: Random = Random.Default) {
    install(HttpRequestRetry) {
        maxRetries = MAX_RETRIES
        retryIf { request, response ->
            isRetryable(request.method, response.status.value, response.retryAfterSeconds(), response.isFromPlatform())
        }
        retryOnExceptionIf { _, _ -> false }
        delayMillis(respectRetryAfterHeader = false) { retry ->
            retryDelayMs(retry, response?.retryAfterSeconds(), random)
        }
    }
}

/** The backend always answers errors in JSON; anything else came from Cloud Run's front end. */
private fun HttpResponse.isFromPlatform(): Boolean =
    contentType()?.match(ContentType.Application.Json) != true

private fun HttpResponse.retryAfterSeconds(): Long? = headers[HttpHeaders.RetryAfter]?.trim()?.toLongOrNull()
