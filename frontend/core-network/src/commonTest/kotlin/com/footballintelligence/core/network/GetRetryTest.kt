package com.footballintelligence.core.network

import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.http.HttpMethod
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import kotlin.random.Random

class GetRetryTest {
    private var calls = 0

    private fun client(vararg replies: Pair<HttpStatusCode, String?>) =
        HttpClient(
            MockEngine {
                val (status, retryAfter) = replies[minOf(calls, replies.lastIndex)]
                calls++
                val headers = retryAfter?.let { headersOf("Retry-After", it) } ?: headersOf()
                respond("", status, headers)
            },
        ) { installGetRetry(Random(0)) }

    @Test
    fun `a GET is retried after a 503 and then succeeds`() = runTest {
        val response = client(HttpStatusCode.ServiceUnavailable to null, HttpStatusCode.OK to null)
            .get("http://test/v2/fixtures")
        assertEquals(HttpStatusCode.OK, response.status)
        assertEquals(2, calls)
    }

    @Test
    fun `a GET is retried at most twice`() = runTest {
        val response = client(HttpStatusCode.BadGateway to null).get("http://test/v2/fixtures")
        assertEquals(HttpStatusCode.BadGateway, response.status)
        assertEquals(3, calls)
    }

    @Test
    fun `a POST is never retried`() = runTest {
        client(HttpStatusCode.ServiceUnavailable to null, HttpStatusCode.OK to null)
            .post("http://test/v2/assistant/chat")
        assertEquals(1, calls)
    }

    @Test
    fun `a client error is not retried`() = runTest {
        client(HttpStatusCode.NotFound to null).get("http://test/v2/teams/x")
        assertEquals(1, calls)
    }

    @Test
    fun `a 429 asking for a long wait is not retried`() = runTest {
        client(HttpStatusCode.TooManyRequests to "60").get("http://test/v2/fixtures")
        assertEquals(1, calls)
    }

    @Test
    fun `a short Retry-After is honoured`() {
        assertTrue(isRetryable(HttpMethod.Get, 429, retryAfterSeconds = 2))
        assertEquals(2_000L, retryDelayMs(retry = 1, retryAfterSeconds = 2, random = Random(0)))
    }

    @Test
    fun `without Retry-After the wait grows and stays capped`() {
        val random = Random(1)
        val waits = (1..10).map { retryDelayMs(it, retryAfterSeconds = null, random = random) }
        assertTrue(waits.all { it in 0..MAX_WAIT_MS })
        assertTrue(retryDelayMs(1, null, Random(2)) <= 1_000L)
    }

    @Test
    fun `writes and other statuses are never retryable`() {
        assertFalse(isRetryable(HttpMethod.Post, 503, retryAfterSeconds = null))
        assertFalse(isRetryable(HttpMethod.Get, 500, retryAfterSeconds = null))
        assertFalse(isRetryable(HttpMethod.Get, 401, retryAfterSeconds = null))
    }
}
