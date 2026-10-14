package com.footballintelligence.feature.auth

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.Me
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.TokenStore
import com.footballintelligence.core.network.AuthApiService
import com.footballintelligence.core.network.AuthSession
import com.footballintelligence.core.network.NetworkConfig
import com.footballintelligence.core.network.bearerAuth
import com.footballintelligence.feature.auth.repository.DefaultAuthRepository
import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.MockRequestHandleScope
import io.ktor.client.engine.mock.respond
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.HttpRequestData
import io.ktor.client.request.HttpResponseData
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.content.TextContent
import io.ktor.http.headersOf
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class AuthRepositoryTest {
    private class MemoryTokenStore(var saved: String? = null) : TokenStore {
        override fun load() = saved
        override fun save(token: String) {
            saved = token
        }
        override fun clear() {
            saved = null
        }
    }

    private val store = MemoryTokenStore()
    private val session = AuthSession(store)
    private val requests = mutableListOf<HttpRequestData>()

    private fun repository(handler: suspend MockRequestHandleScope.(HttpRequestData) -> HttpResponseData) =
        DefaultAuthRepository(
            AuthApiService(
                HttpClient(
                    MockEngine { request ->
                        requests += request
                        handler(request)
                    },
                ) {
                    install(ContentNegotiation) { json(Json { ignoreUnknownKeys = true }) }
                    install(bearerAuth(session))
                },
                NetworkConfig(baseUrl = "http://test"),
            ),
            session,
        )

    private fun MockRequestHandleScope.json(body: String, status: HttpStatusCode = HttpStatusCode.OK) =
        respond(body, status, headersOf(HttpHeaders.ContentType, "application/json"))

    private val sessionJson = """{"token":"tok-1","expires_at":"2026-11-07T12:00:00Z"}"""
    private val meJson =
        """{"email":"sam@example.com","consent_required":true,"consent_version":2,
           "consent_text":"Notice","store_questions":false}"""

    private fun HttpRequestData.text() = (body as TextContent).text

    @Test
    fun `signing in keeps the token`() = runTest {
        val result = repository { json(sessionJson) }.signIn(" sam@example.com ", "matchday-2026")
        assertEquals(NetworkResult.Success(Unit), result)
        assertEquals("tok-1", store.saved)
        assertEquals("/v2/auth/login", requests.single().url.encodedPath)
        assertEquals("""{"email":"sam@example.com","password":"matchday-2026"}""", requests.single().text())
    }

    @Test
    fun `a wrong password keeps the server's status and starts no session`() = runTest {
        val error = """{"error":"Invalid credentials","detail":"Wrong email or password."}"""
        val result = repository { json(error, HttpStatusCode.Unauthorized) }.signIn("sam@example.com", "nope")
        result as NetworkResult.Error
        assertEquals(401, result.code)
        assertEquals(ErrorKind.REJECTED, result.kind)
        assertNull(session.token.value)
    }

    @Test
    fun `redeeming an invite sends the code and keeps the token`() = runTest {
        repository { json(sessionJson) }.redeemInvite("sam@example.com", "bX3k9_QpZr2LmN7vT0aYwQ", "matchday-2026")
        assertEquals("/v2/auth/redeem-invite", requests.single().url.encodedPath)
        assertEquals(
            """{"email":"sam@example.com","code":"bX3k9_QpZr2LmN7vT0aYwQ","password":"matchday-2026"}""",
            requests.single().text(),
        )
        assertEquals("tok-1", session.token.value)
    }

    @Test
    fun `signing out tells the server with the token, then forgets it`() = runTest {
        session.signIn("tok-1")
        repository { respond("", HttpStatusCode.NoContent) }.signOut()
        assertEquals("/v2/auth/logout", requests.single().url.encodedPath)
        assertEquals("Bearer tok-1", requests.single().headers[HttpHeaders.Authorization])
        assertNull(store.saved)
    }

    @Test
    fun `signing out works offline too`() = runTest {
        session.signIn("tok-1")
        repository { throw java.io.IOException("Connection refused") }.signOut()
        assertNull(session.token.value)
    }

    @Test
    fun `me reads the notice`() = runTest {
        session.signIn("tok-1")
        val result = repository { json(meJson) }.me()
        assertEquals(NetworkResult.Success(Me("sam@example.com", true, 2, "Notice", false)), result)
        assertEquals("Bearer tok-1", requests.single().headers[HttpHeaders.Authorization])
    }

    @Test
    fun `accepting sends the version and the storing choice`() = runTest {
        session.signIn("tok-1")
        repository { json(meJson.replace("true", "false")) }.acceptConsent(version = 2, storeQuestions = true)
        assertEquals("/v2/me/consent", requests.single().url.encodedPath)
        assertEquals("""{"version":2,"store_questions":true}""", requests.single().text())
    }

    @Test
    fun `an expired session signs out`() = runTest {
        session.signIn("tok-1")
        val error = """{"error":"Not signed in","detail":"Sign in again."}"""
        repository { json(error, HttpStatusCode.Unauthorized) }.me()
        assertNull(session.token.value)
    }
}
