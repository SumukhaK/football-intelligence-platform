package com.footballintelligence.core.network

import com.footballintelligence.core.model.TokenStore
import io.ktor.client.HttpClient
import io.ktor.client.engine.mock.MockEngine
import io.ktor.client.engine.mock.respond
import io.ktor.client.request.get
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class BearerAuthTest {
    private class MemoryTokenStore(var saved: String?) : TokenStore {
        override fun load() = saved
        override fun save(token: String) {
            saved = token
        }
        override fun clear() {
            saved = null
        }
    }

    private val store = MemoryTokenStore("tok-1")
    private val session = AuthSession(store)
    private var sentHeader: String? = null

    private fun client(status: HttpStatusCode) =
        HttpClient(
            MockEngine { request ->
                sentHeader = request.headers[HttpHeaders.Authorization]
                respond("", status)
            },
        ) { install(bearerAuth(session)) }

    @Test
    fun `every request carries the session token`() = runTest {
        client(HttpStatusCode.OK).get("http://test/v2/fixtures")
        assertEquals("Bearer tok-1", sentHeader)
    }

    @Test
    fun `no header is sent when signed out`() = runTest {
        session.signOut()
        client(HttpStatusCode.OK).get("http://test/v2/fixtures")
        assertNull(sentHeader)
    }

    @Test
    fun `a rejected token signs out`() = runTest {
        client(HttpStatusCode.Unauthorized).get("http://test/v2/fixtures")
        assertNull(session.token.value)
        assertNull(store.saved)
    }

    @Test
    fun `other errors keep the session`() = runTest {
        client(HttpStatusCode.Forbidden).get("http://test/v2/fixtures")
        assertEquals("tok-1", session.token.value)
    }

    @Test
    fun `a 401 for a token already replaced keeps the new one`() = runTest {
        val engine = MockEngine {
            session.signIn("tok-2")
            respond("", HttpStatusCode.Unauthorized)
        }
        HttpClient(engine) { install(bearerAuth(session)) }.get("http://test/v2/me")
        assertEquals("tok-2", session.token.value)
    }
}
