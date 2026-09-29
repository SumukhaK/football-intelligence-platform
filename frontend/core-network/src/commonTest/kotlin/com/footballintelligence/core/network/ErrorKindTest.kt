package com.footballintelligence.core.network

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ErrorKindTest {
    private fun api(engine: MockEngine) =
        KtorFootballApiService(
            HttpClient(engine) {
                install(ContentNegotiation) { json(Json { ignoreUnknownKeys = true }) }
            },
            NetworkConfig(baseUrl = "http://test"),
        )

    private fun respondWith(status: HttpStatusCode, body: String = "") =
        MockEngine { respond(body, status, headersOf(HttpHeaders.ContentType, "application/json")) }

    private val request = PredictionRequest("Arsenal", "Bayern Munich", competition = "Bundesliga")

    @Test
    fun `service unavailable means the server is busy`() = runTest {
        val result = api(respondWith(HttpStatusCode.ServiceUnavailable)).predict(request)
        assertEquals(ErrorKind.SERVER_BUSY, (result as NetworkResult.Error).kind)
    }

    @Test
    fun `a rejected request keeps the server's explanation`() = runTest {
        val body =
            """{"error":"Unknown team","team":"Arsenal",
               "detail":"'Arsenal' did not play in Bundesliga 2026/27"}"""
        val result = api(respondWith(HttpStatusCode.UnprocessableEntity, body)).predict(request)
        result as NetworkResult.Error
        assertEquals(ErrorKind.REJECTED, result.kind)
        assertEquals("'Arsenal' did not play in Bundesliga 2026/27", result.message)
    }

    @Test
    fun `no connection means offline`() = runTest {
        val result = api(MockEngine { throw java.io.IOException("Connection refused") }).predict(request)
        assertEquals(ErrorKind.OFFLINE, (result as NetworkResult.Error).kind)
    }

    @Test
    fun `other server errors are unknown`() = runTest {
        val result = api(respondWith(HttpStatusCode.InternalServerError)).predict(request)
        assertEquals(ErrorKind.UNKNOWN, (result as NetworkResult.Error).kind)
    }
}
