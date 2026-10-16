package com.footballintelligence.core.network

import com.footballintelligence.core.model.LoginRequest
import com.footballintelligence.core.model.RedeemInviteRequest
import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.MockRequestHandleScope
import io.ktor.client.engine.mock.respond
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.HttpRequestData
import io.ktor.client.request.HttpResponseData
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import java.io.IOException

class AuthApiServiceTest {
    private val config = NetworkConfig(baseUrl = "http://test")
    private val requests = mutableListOf<HttpRequestData>()

    private fun service(
        reply: MockRequestHandleScope.() -> HttpResponseData = {
            respond("{}", HttpStatusCode.OK, headersOf("Content-Type", "application/json"))
        },
    ) = AuthApiService(
        HttpClient(
            MockEngine { request ->
                requests += request
                reply()
            },
        ) {
            install(ContentNegotiation) { json() }
            install(HttpTimeout) { requestTimeoutMillis = config.timeoutMs }
        },
        config,
    )

    private fun timeoutOf(request: HttpRequestData): Long? =
        request.getCapabilityOrNull(HttpTimeout)?.requestTimeoutMillis

    @Test
    fun `signing in waits long enough for a server starting from cold`() = runTest {
        service().login(LoginRequest(email = "sam@example.com", password = "matchday-2026"))
        assertEquals(config.signInTimeoutMs, timeoutOf(requests.single()))
    }

    @Test
    fun `redeeming an invite waits long enough for a server starting from cold`() = runTest {
        service().redeemInvite(
            RedeemInviteRequest(email = "sam@example.com", code = "bX3k9", password = "matchday-2026"),
        )
        assertEquals(config.signInTimeoutMs, timeoutOf(requests.single()))
    }

    @Test
    fun `waking the server asks the liveness probe`() = runTest {
        service().wake()
        assertEquals("http://test/v2/live", requests.single().url.toString())
    }

    @Test
    fun `waking the server ignores a failure`() = runTest {
        service { throw IOException("offline") }.wake()
        assertEquals(1, requests.size)
    }
}
