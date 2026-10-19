package com.footballintelligence.core.network

import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.TokenStore
import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.headersOf
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class AccountPreferencesApiTest {
    @Test
    fun `cancellation propagates instead of becoming an offline account`() {
        val client = HttpClient(MockEngine { throw CancellationException("Cancelled") })
        val api = AccountPreferencesApiService(client, NetworkConfig(baseUrl = "http://test"))
        assertThrows(CancellationException::class.java) { runTest { api.load("A") } }
    }

    @Test
    fun `a missing preference field is malformed rather than a confirmed empty account`() = runTest {
        val client = HttpClient(
            MockEngine {
                respond("""{"email":"a@example.com"}""", headers = headersOf("Content-Type", "application/json"))
            },
        ) { install(ContentNegotiation) { json() } }
        val api = AccountPreferencesApiService(client, NetworkConfig(baseUrl = "http://test"))
        assertInstanceOf(NetworkResult.Error::class.java, api.load("A"))
    }
    private val session = AuthSession(object : TokenStore {
        override fun load() = "B"
        override fun save(token: String) = Unit
        override fun clear() = Unit
    })

    @Test
    fun `preference requests preserve originating credentials even after session switch`() = runTest {
        val client = HttpClient(
            MockEngine { request ->
                assertEquals("Bearer A", request.headers[HttpHeaders.Authorization])
                assertEquals("/v2/me/preferences", request.url.encodedPath)
                respond(
                    """{"email":"a@example.com","favourite":null}""",
                    headers = headersOf("Content-Type", "application/json"),
                )
            },
        ) {
            install(ContentNegotiation) { json() }
            install(bearerAuth(session))
        }
        val api = AccountPreferencesApiService(client, NetworkConfig(baseUrl = "http://test"))
        assertInstanceOf(NetworkResult.Success::class.java, api.load("A"))
        assertInstanceOf(NetworkResult.Success::class.java, api.save("A", FavouriteTeam("Serie A", "Inter")))
    }

    @Test
    fun `provider failure is an error rather than an empty favourite`() = runTest {
        val client = HttpClient(
            MockEngine {
                respond(
                    """{"error":"Unavailable","detail":"Try again"}""",
                    HttpStatusCode.ServiceUnavailable,
                    headersOf("Content-Type", "application/json"),
                )
            },
        ) { install(ContentNegotiation) { json() } }
        val result = AccountPreferencesApiService(client, NetworkConfig(baseUrl = "http://test")).load("A")
        assertInstanceOf(NetworkResult.Error::class.java, result)
    }
}
